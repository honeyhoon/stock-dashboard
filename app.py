import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import requests
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(
    page_title="지능형 주식 블로그 비서 (Gemini)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 및 스타일링 ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        font-family: 'Sans-serif';
    }
    .stMetric {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("설정 및 입력")
    
    # Google API 키 입력
    if 'GOOGLE_API_KEY' in st.secrets.get('general', {}):
        api_key = st.secrets['general']['GOOGLE_API_KEY']
        st.success("Gemini API 키가 로드되었습니다.")
    else:
        api_key = st.text_input("Google API Key", type="password", help="AI 기능을 사용하려면 Gemini API 키가 필요합니다.")
        st.caption("팁: .streamlit/secrets.toml 파일에 키를 저장하세요.")
    
    st.markdown("---")
    st.header("종목 검색")
    ticker_symbol = st.text_input("티커 입력 (예: NVDA, AAPL)", value="NVDA").upper()
    
    if st.button("분석 시작"):
        st.session_state['run_analysis'] = True
    else:
        if 'run_analysis' not in st.session_state:
            st.session_state['run_analysis'] = False

# --- 데이터 가져오기 통합 함수 ---
from duckduckgo_search import DDGS
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# 한국어 번역 헬퍼 함수
def translate_to_korean(text):
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='auto', target='ko').translate(text)
    except:
        return text

# 기업 대표 이미지 검색 함수 - 핵심 매출 제품 기반
def get_company_images(ticker, company_name="", industry=""):
    """DuckDuckGo 이미지 검색으로 기업 핵심 제품 이미지 4장 가져오기"""
    images = []
    
    # 티커별 핵심 제품 키워드 매핑
    product_keywords = {
        'NVDA': 'data center GPU AI chip H100',
        'AAPL': 'iPhone MacBook Apple products',
        'MSFT': 'Azure cloud Microsoft Office',
        'GOOGL': 'Google Search AI Cloud',
        'GOOG': 'Google Search AI Cloud',
        'AMZN': 'AWS cloud Amazon warehouse',
        'META': 'Facebook Instagram VR Quest',
        'TSLA': 'Tesla Model electric car',
        'AMD': 'AMD EPYC Ryzen processor',
        'INTC': 'Intel processor data center',
    }
    
    try:
        with DDGS() as ddgs:
            # 티커에 맞는 키워드 사용, 없으면 기본값
            keyword = product_keywords.get(ticker, f"{company_name} main product")
            query = f"{keyword}"
            
            results = list(ddgs.images(query, max_results=4))
            for r in results:
                images.append({
                    'url': r.get('image', ''),
                    'title': r.get('title', ''),
                    'source': r.get('source', '')
                })
    except Exception as e:
        print(f"Image search error: {e}")
    
    return images


def get_hybrid_news(ticker):
    news_items = []
    
    # 1. DuckDuckGo Search (금융 미디어 타겟)
    target_sites = [
        ('CNBC', 'site:cnbc.com'),
        ('Reuters', 'site:reuters.com'),
        ('Investing.com', 'site:investing.com'),
        ('Bloomberg', 'site:bloomberg.com')
    ]
    
    try:
        with DDGS() as ddgs:
            for source_name, site_query in target_sites:
                query = f"{ticker} stock news {site_query}"
                results = list(ddgs.text(query, max_results=2))
                for r in results:
                    news_items.append({
                        'title': r['title'],
                        'link': r['href'],
                        'publisher': source_name,
                        'date': datetime.now().isoformat()
                    })
    except Exception as e:
        print(f"DDGS Error: {e}")

    # 2. Yahoo Finance News
    try:
        stock = yf.Ticker(ticker)
        yf_news = stock.news[:5]
        for item in yf_news:
            news_items.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'publisher': 'Yahoo Finance',
                'date': str(item.get('providerPublishTime', ''))
            })
    except Exception as e:
        print(f"Yahoo News Error: {e}")

    # 3. Google News RSS (가장 안정적인 소스)
    try:
        import xml.etree.ElementTree as ET
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item')[:5]:
                title_raw = item.find('title').text if item.find('title') is not None else 'No Title'
                parts = title_raw.rsplit(' - ', 1)
                title = parts[0].strip()
                publisher = parts[1].strip() if len(parts) > 1 else 'Google News'
                
                # Google News 리다이렉트 링크에서 실제 URL 추출
                google_link = item.find('link').text if item.find('link') is not None else '#'
                try:
                    # 리다이렉트를 따라가서 실제 URL 가져오기
                    redirect_resp = requests.head(google_link, allow_redirects=True, timeout=5)
                    actual_link = redirect_resp.url
                except:
                    actual_link = google_link
                
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                date_str = pub_date[:16] if pub_date else datetime.now().strftime('%Y-%m-%d')
                
                news_items.append({
                    'title': title,
                    'link': actual_link,
                    'publisher': publisher,
                    'date': date_str
                })
    except Exception as e:
        print(f"Google RSS Error: {e}")


    # 4. 중복 제거 (제목 유사도 80% 이상)
    unique_news = []
    for item in news_items:
        if not item.get('title'): continue
        is_duplicate = False
        for existing in unique_news:
            if similar(item['title'].lower(), existing['title'].lower()) > 0.8:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_news.append(item)
    
    # 5. 뉴스 제목 한국어 번역 + 대표 이미지 추출
    for item in unique_news:
        original_title = item.get('title', '')
        item['title_en'] = original_title
        item['title'] = translate_to_korean(original_title)
        
        # og:image 추출 시도
        try:
            from bs4 import BeautifulSoup
            resp = requests.get(item.get('link', ''), timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    item['image_url'] = og_image['content']
                else:
                    item['image_url'] = ''
            else:
                item['image_url'] = ''
        except:
            item['image_url'] = ''
            
    return unique_news[:10]

@st.cache_data
def get_dashboard_data(ticker):
    """주가, 정보, 뉴스를 한 번에 가져와서 serializable한 형태로 반환"""
    df = None
    error_msg = None
    
    # 1. 주가 데이터
    try:
        df = yf.download(ticker, period="1y", progress=False)
        
        # yfinance가 MultiIndex 컬럼을 반환할 수 있으므로 평탄화
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        
        if df is None or df.empty:
            try:
                import pandas_datareader.data as web
                start = datetime.now() - timedelta(days=365)
                end = datetime.now()
                try:
                    df = web.DataReader(f"{ticker}.US", 'stooq', start, end).sort_index()
                except:
                    df = web.DataReader(ticker, 'stooq', start, end).sort_index()
            except Exception as e:
                error_msg = f"데이터 수신 실패: {str(e)}"
        
        if df is not None and df.empty:
            error_msg = "데이터가 비어있습니다"
    except Exception as e:
        error_msg = f"오류: {str(e)}"
    
    # 2. 상세 정보
    info = {}
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
    except:
        info = {}
    
    # 3. 뉴스 (Hybrid 방식)
    news = get_hybrid_news(ticker)

    return df, info, news, error_msg

# --- AI 분석 요청 함수 (Gemini 1 -> Gemini 2 -> Groq 순차 시도) ---
def generate_ai_analysis(ticker, df_summary, news_summary, image_list, api_key):
    # 여러 API 키 가져오기
    gemini_key_1 = st.secrets.get('general', {}).get('GOOGLE_API_KEY_1', api_key)
    gemini_key_2 = st.secrets.get('general', {}).get('GOOGLE_API_KEY_2', '')
    groq_key = st.secrets.get('general', {}).get('GROQ_API_KEY', '')
    
    if not gemini_key_1 and not api_key:
        return "API 키가 입력되지 않았습니다."
    
    # 이미지 리스트 포맷팅
    images_str = ""
    if image_list:
        images_str = "\n[사용 가능한 이미지 목록 - 이 중 적절한 것을 골라 글 내용 중간에 마크다운 ![](url) 으로 삽입하세요]\n"
        for i, img in enumerate(image_list):
            images_str += f"{i+1}. {img['title']} (URL: {img['url']})\n"
    
    prompt = f"""
    당신은 한국의 투자 분석 블로거입니다.
    
    '{ticker}' 주식에 대해 블로그 글을 작성해주세요.
    
    [참고 데이터]
    주가 정보: {df_summary}
    최근 뉴스: {news_summary}
    {images_str}

    
    [글쓰기 스타일 - 반드시 지킬 것]
    
    1. 모든 문장 끝에 반드시 줄바꿈 2번 (빈 줄 삽입)
    2. 절대로 두 문장을 한 줄에 쓰지 않음
    3. 한 문장은 30~50자, 핵심만
    4. "~이다", "~했다" 간결체 사용
    5. 이모지, 특수문자 금지
    6. 뉴스 인용 시 출처와 날짜 명시
    
    [줄바꿈 예시 - 반드시 이 형식으로]
    
    첫 번째 문장이다.
    
    두 번째 문장이다.
    
    세 번째 문장이다.
    
    [필수 포함 내용 - 제목 없이 내용만]
    
    먼저 이 회사의 주요 사업 부문별 매출 비중을 구체적 숫자(%)로 제시한다.
    현재 가장 큰 매출원이 어디인지, 향후 성장이 기대되는 부문은 어디인지 설명한다.
    
    ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    
    현재 주가와 52주 최고/최저 비교, 1년 수익률과 최근 흐름을 설명한다.
    
    ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    
    주요 뉴스 2-3개를 아래 형식으로 인용한다:
    "뉴스 제목" (출처: 매체명, 기사링크: URL)
    
    ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    
    핵심 투자 포인트 2-3개와 주요 리스크 요인 2-3개를 나열한다.
    
    ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    
    현재 이 종목에 대한 종합 의견 1-2문장으로 마무리한다.
    (투자 권유가 아닌 정보 공유 목적임을 명시)
    
    [중요: 형식 규칙]
    - "##" 같은 마크다운 헤더 기호는 절대 사용하지 않음
    - 제목 대신 위처럼 "ㅡㅡㅡㅡㅡ" 구분선으로 섹션을 나눔
    
    총 50문장 이내로 핵심만 작성.
    """
    
    # 1. Gemini 키 1 시도
    try:
        genai.configure(api_key=gemini_key_1)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e1:
        if "429" not in str(e1):
            return f"AI 오류: {str(e1)}"
    
    # 2. Gemini 키 2 시도
    if gemini_key_2:
        try:
            genai.configure(api_key=gemini_key_2)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return f"[Gemini 키2 사용]\n\n{response.text}"
        except Exception as e2:
            if "429" not in str(e2):
                return f"AI 오류: {str(e2)}"
    
    # 3. Groq로 fallback
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "당신은 한국의 투자 분석 블로거입니다."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=2000
            )
            
            return f"[Groq AI 사용]\n\n{chat_completion.choices[0].message.content}"
        except Exception as e3:
            return f"모든 AI 서비스 실패: {str(e3)}"
    
    return "모든 API 제한 초과. 잠시 후 다시 시도하세요."



#------ 메인 앱 로직 ------

st.title("지능형 주식 블로그 비서")
st.markdown("주가 데이터 시각화, 뉴스 분석, 그리고 AI 기반의 미래 전망 리포트까지 한 번에 확인하세요.")

if st.session_state['run_analysis'] and ticker_symbol:
    
    # 데이터 가져오기
    with st.spinner(f"'{ticker_symbol}' 데이터 검색 및 분석 준비 중..."):
        df, info, news_list, error_msg = get_dashboard_data(ticker_symbol)
    
    # 에러 경고 (있으면)
    if error_msg:
        st.warning(f"주가 데이터: {error_msg}")
    
    # 사이드바 정보
    with st.sidebar:
        st.markdown("---")
        st.subheader(f"{ticker_symbol} 주요 지표")
        if info and info.get('currentPrice'):
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            market_cap = info.get('marketCap', 'N/A')
            per = info.get('trailingPE', 'N/A')
            
            def format_num(num):
                if isinstance(num, (int, float)):
                    return f"{num:,.0f}"
                return num
            
            st.metric("현재 주가", f"${current_price}")
            st.write(f"**시가총액**: {format_num(market_cap)}")
            st.write(f"**PER**: {per}")
        else:
            st.caption("재무 정보를 불러올 수 없습니다.")

    # 기업 대표 이미지 섹션
    company_name = info.get('longName', info.get('shortName', ticker_symbol))
    company_images = get_company_images(ticker_symbol, company_name)
    
    if company_images:
        st.subheader(f"{ticker_symbol} 기업 이미지")
        img_cols = st.columns(4)
        for idx, img in enumerate(company_images[:4]):
            with img_cols[idx]:
                if img.get('url'):
                    st.image(img['url'], caption=img.get('source', ''), use_container_width=True)
                    st.caption(f"[이미지 링크]({img['url']})")

    # 차트 시각화 (데이터 있을 때만)
    if df is not None and not df.empty and len(df) > 0:
        st.subheader(f"{ticker_symbol} 주가 및 거래량 차트 (지난 1년)")
        
        # 이동평균선
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # 차트 생성
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, 
                            subplot_titles=(f'{ticker_symbol} Price Chart', 'Volume'), 
                            row_heights=[0.7, 0.3])
        
        # 캔들스틱
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'], 
            high=df['High'],
            low=df['Low'], 
            close=df['Close'], 
            name='OHLC'
        ), row=1, col=1)
        
        # 이동평균선
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MA20'], 
            opacity=0.7, 
            line=dict(color='orange', width=2), 
            name='MA 20'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MA60'], 
            opacity=0.7, 
            line=dict(color='purple', width=2), 
            name='MA 60'
        ), row=1, col=1)
        
        # 거래량 (색상: 하락=red, 상승=green)
        import numpy as np
        colors = np.where(df['Close'].values < df['Open'].values, 'red', 'green')
        fig.add_trace(go.Bar(
            x=df.index, 
            y=df['Volume'], 
            marker_color=colors, 
            name='Volume'
        ), row=2, col=1)
        
        fig.update_layout(
            height=600, 
            showlegend=True, 
            xaxis_rangeslider_visible=False,
            title_text=f"{ticker_symbol} Analysis Chart"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("데이터를 표시할 수 없습니다.")

    # 뉴스 및 AI 분석
    col1, col2 = st.columns([1, 1])
    news_summary_text = ""
    
    with col1:
        st.subheader("최신 뉴스")
        
        if not news_list:
            st.info("최신 뉴스를 찾을 수 없습니다.")
            news_summary_text = "뉴스 데이터 없음"
        else:
            for idx, item in enumerate(news_list):
                title = item.get('title', '제목 없음')
                link = item.get('link', '#')
                publisher = item.get('publisher', 'Unknown')
                date = item.get('date', '')
                image_url = item.get('image_url', '')
                
                st.markdown(f"**{idx+1}. [{title}]({link})**")
                if image_url:
                    st.caption(f"출처: {publisher} | 날짜: {date}")
                    st.caption(f"이미지: {image_url}")
                else:
                    st.caption(f"출처: {publisher} | 날짜: {date}")
                
                # AI용 뉴스 요약에 이미지 URL 포함
                news_summary_text += f"- {title} (출처: {publisher}, 날짜: {date}, 기사링크: {link}"
                if image_url:
                    news_summary_text += f", 이미지URL: {image_url}"
                news_summary_text += ")\n"

    
    with col2:
        st.subheader("AI 투자 분석 리포트")
        
        # 데이터 요약
        if df is not None and not df.empty and len(df) > 0:
            last_close = float(df['Close'].iloc[-1])
            first_close = float(df['Close'].iloc[0])
            high_max = float(df['High'].max())
            low_min = float(df['Low'].min())
            price_change_1y = ((last_close - first_close) / first_close) * 100
            data_summary = f"""
            - 종목: {ticker_symbol}
            - 현재 주가: ${last_close:.2f}
            - 1년 수익률: {price_change_1y:.2f}%
            - 52주 최고가: ${high_max:.2f}
            - 52주 최저가: ${low_min:.2f}
            """
        else:
            data_summary = f"- 종목: {ticker_symbol}\n- 주가 데이터: 수신 실패"
        
        # AI 분석을 위한 이미지 리스트 수집
        ai_image_list = []
        
        # 1. 기업 대표 이미지
        if company_images:
            for img in company_images:
                if img.get('url'):
                    ai_image_list.append({'title': f"{ticker_symbol} 관련 이미지", 'url': img['url']})
        
        # 2. 뉴스 이미지
        for item in news_list:
            if item.get('image_url'):
                ai_image_list.append({'title': f"뉴스 이미지: {item.get('title')}", 'url': item.get('image_url')})

        # AI 분석 생성
        with st.spinner("AI가 데이터를 분석하고 글을 작성 중입니다..."):
            # API 키 (순차적으로 시도하므로 첫 번째 키 전달)
            api_key = st.secrets.get('general', {}).get('GOOGLE_API_KEY_1', st.session_state.get('api_key', ''))
            
            ai_report = generate_ai_analysis(ticker_symbol, data_summary, news_summary_text, ai_image_list, api_key)

        
        st.markdown(ai_report)
        st.text_area("블로그 포스팅용 텍스트 복사", value=ai_report, height=200)

else:
    st.info("사이드바에서 주식 티커를 입력하고 '분석 시작' 버튼을 눌러주세요.")
