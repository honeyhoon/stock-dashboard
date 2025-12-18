# ==========================================================
# [주가 분석 대시보드] - Streamlit UI 버전
# 작성일: 2025년 12월 18일
# 설명: 여러 주식 종목의 수익률 비교 및 다양한 분석 기능을 제공하는 웹 앱
# ==========================================================

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(
    page_title="주가 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 CSS (깔끔한 모던 라이트 테마) ---
st.markdown("""
<style>
    /* 전체 배경 - 부드러운 그라디언트 */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* 메인 헤더 */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem 0;
    }
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
        border-right: 1px solid #e2e8f0;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4,
    section[data-testid="stSidebar"] .stMarkdown h5 {
        color: #1e293b !important;
    }
    
    /* 메트릭 카드 */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #f1f5f9;
        padding: 4px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        color: #64748b;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #3b82f6;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #3b82f6 !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* 버튼 */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Primary 버튼 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
    }
    
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }
    
    /* 입력 필드 */
    .stTextInput > div > div > input {
        background: white;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #1e293b;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* 셀렉트박스 */
    .stSelectbox > div > div {
        background: white;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
    }
    
    /* 체크박스 */
    .stCheckbox > label {
        color: #374151;
    }
    
    /* 섹션 제목 */
    h1, h2, h3, h4, h5 {
        color: #1e293b !important;
    }
    
    /* 캡션 */
    .stCaption, small {
        color: #64748b !important;
    }
    
    /* 정보 박스 */
    .stAlert {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
    }
    
    /* 데이터프레임 */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 8px;
        color: #1e293b !important;
        font-weight: 600;
    }
    
    /* 구분선 */
    hr {
        border-color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- 캐시된 데이터 가져오기 함수 ---
@st.cache_data(ttl=300)  # 5분간 캐시
def fetch_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """주식 데이터를 가져오는 함수 (캐시 적용)"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        if not df.empty:
            df['Ticker'] = ticker
        return df
    except Exception as e:
        st.warning(f"'{ticker}' 데이터 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_stock_info(ticker: str) -> dict:
    """종목 기본 정보 가져오기"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except:
        return {}

# --- 분석 함수들 ---
def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
    """수익률 계산"""
    if len(df) == 0:
        return df
    first_price = df['Close'].iloc[0]
    df['Return'] = (df['Close'] - first_price) / first_price * 100
    df['Daily_Return'] = df['Close'].pct_change() * 100
    return df

def calculate_moving_averages(df: pd.DataFrame, windows: list = [5, 20, 60]) -> pd.DataFrame:
    """이동평균선 계산"""
    for window in windows:
        if len(df) >= window:
            df[f'MA{window}'] = df['Close'].rolling(window=window).mean()
    return df

def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """변동성 계산 (20일 이동 표준편차)"""
    df['Volatility'] = df['Daily_Return'].rolling(window=window).std()
    return df

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI(상대강도지수) 계산"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """볼린저 밴드 계산"""
    df['BB_Middle'] = df['Close'].rolling(window=window).mean()
    std = df['Close'].rolling(window=window).std()
    df['BB_Upper'] = df['BB_Middle'] + (std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std * 2)
    return df

def format_price(price: float, ticker: str) -> str:
    """티커에 따라 통화 기호를 자동 설정 (한국: ₩, 미국: $)"""
    if ticker.endswith('.KS') or ticker.endswith('.KQ'):
        return f"₩{price:,.0f}"
    else:
        return f"${price:.2f}"

def get_currency_label(ticker: str) -> str:
    """티커에 따라 통화 라벨 반환"""
    if ticker.endswith('.KS') or ticker.endswith('.KQ'):
        return "가격 (원)"
    else:
        return "가격 ($)"

# --- 기업명 가져오기 ---
# 티커 -> 기업명 매핑 (한국 주요 종목)
TICKER_TO_NAME = {
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    '035420.KS': '네이버',
    '035720.KS': '카카오',
    '373220.KS': 'LG에너지솔루션',
    '207940.KS': '삼성바이오로직스',
    '005380.KS': '현대차',
    '000270.KS': '기아',
    '068270.KQ': '셀트리온',
    '005490.KS': 'POSCO홀딩스',
    '105560.KS': 'KB금융',
    '055550.KS': '신한지주',
    '051910.KS': 'LG화학',
    '006400.KS': '삼성SDI',
    '012330.KS': '현대모비스',
    '009150.KS': '삼성전기',
    '036570.KS': '엔씨소프트',
    '251270.KS': '넷마블',
    '323410.KS': '카카오뱅크',
    '377300.KS': '카카오페이',
    '259960.KS': '크래프톤',
    '352820.KS': '하이브',
    '096770.KS': 'SK이노베이션',
    '017670.KS': 'SK텔레콤',
    '030200.KS': 'KT',
    '066570.KS': 'LG전자',
    '012450.KS': '한화에어로스페이스',
    '034020.KS': '두산에너빌리티',
    # 미국 주요 종목
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Google',
    'AMZN': 'Amazon',
    'META': 'Meta',
    'TSLA': 'Tesla',
    'NVDA': 'NVIDIA',
    'AMD': 'AMD',
    'INTC': 'Intel',
    'TSM': 'TSMC',
    'JPM': 'JP Morgan',
    'BAC': 'Bank of America',
    'GS': 'Goldman Sachs',
    'MS': 'Morgan Stanley',
    'RIVN': 'Rivian',
    'LCID': 'Lucid',
    'NIO': 'NIO',
}

def get_company_name(ticker: str) -> str:
    """티커로부터 기업명을 가져옵니다"""
    ticker_upper = ticker.upper()
    if ticker_upper in TICKER_TO_NAME:
        return TICKER_TO_NAME[ticker_upper]
    
    # Yahoo Finance에서 가져오기 시도
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('shortName', info.get('longName', ticker))
        return name if name else ticker
    except:
        return ticker

# --- 한국 주요 종목 데이터베이스 (한글 검색용) ---
KOREAN_STOCKS = {
    '삼성전자': {'symbol': '005930.KS', 'name': 'Samsung Electronics'},
    '삼성': {'symbol': '005930.KS', 'name': 'Samsung Electronics'},
    'SK하이닉스': {'symbol': '000660.KS', 'name': 'SK Hynix'},
    '하이닉스': {'symbol': '000660.KS', 'name': 'SK Hynix'},
    '네이버': {'symbol': '035420.KS', 'name': 'Naver Corp'},
    '카카오': {'symbol': '035720.KS', 'name': 'Kakao Corp'},
    'LG에너지솔루션': {'symbol': '373220.KS', 'name': 'LG Energy Solution'},
    '삼성바이오로직스': {'symbol': '207940.KS', 'name': 'Samsung Biologics'},
    '현대차': {'symbol': '005380.KS', 'name': 'Hyundai Motor'},
    '현대자동차': {'symbol': '005380.KS', 'name': 'Hyundai Motor'},
    '기아': {'symbol': '000270.KS', 'name': 'Kia Corp'},
    '셀트리온': {'symbol': '068270.KQ', 'name': 'Celltrion'},
    'POSCO홀딩스': {'symbol': '005490.KS', 'name': 'POSCO Holdings'},
    '포스코': {'symbol': '005490.KS', 'name': 'POSCO Holdings'},
    'KB금융': {'symbol': '105560.KS', 'name': 'KB Financial Group'},
    '신한지주': {'symbol': '055550.KS', 'name': 'Shinhan Financial'},
    'LG화학': {'symbol': '051910.KS', 'name': 'LG Chem'},
    '삼성SDI': {'symbol': '006400.KS', 'name': 'Samsung SDI'},
    '현대모비스': {'symbol': '012330.KS', 'name': 'Hyundai Mobis'},
    '삼성전기': {'symbol': '009150.KS', 'name': 'Samsung Electro-Mechanics'},
    '엔씨소프트': {'symbol': '036570.KS', 'name': 'NCSoft'},
    '넷마블': {'symbol': '251270.KS', 'name': 'Netmarble'},
    '카카오뱅크': {'symbol': '323410.KS', 'name': 'KakaoBank'},
    '카카오페이': {'symbol': '377300.KS', 'name': 'KakaoPay'},
    '크래프톤': {'symbol': '259960.KS', 'name': 'Krafton'},
    '하이브': {'symbol': '352820.KS', 'name': 'HYBE'},
    'SK이노베이션': {'symbol': '096770.KS', 'name': 'SK Innovation'},
    'SK텔레콤': {'symbol': '017670.KS', 'name': 'SK Telecom'},
    'KT': {'symbol': '030200.KS', 'name': 'KT Corp'},
    'LG전자': {'symbol': '066570.KS', 'name': 'LG Electronics'},
    '한화에어로스페이스': {'symbol': '012450.KS', 'name': 'Hanwha Aerospace'},
    '두산에너빌리티': {'symbol': '034020.KS', 'name': 'Doosan Enerbility'},
}

# --- 티커 검색 함수 ---
def search_ticker(query: str) -> list:
    """Yahoo Finance API를 통해 티커 검색 (한글 지원)"""
    import requests
    
    results = []
    
    # 1. 먼저 한국 종목 DB에서 검색
    query_lower = query.strip()
    for kr_name, info in KOREAN_STOCKS.items():
        if query_lower in kr_name or kr_name in query_lower:
            results.append({
                'symbol': info['symbol'],
                'name': f"{kr_name} ({info['name']})",
                'exchange': 'Korea'
            })
    
    # 2. Yahoo Finance API 검색 (영어 검색어만)
    if not results or not any(ord(c) > 127 for c in query):  # ASCII가 아닌 문자가 없으면
        try:
            url = "https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                'q': query,
                'quotesCount': 10,
                'newsCount': 0,
                'enableFuzzyQuery': True,
            }
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                for quote in data.get('quotes', []):
                    symbol = quote.get('symbol', '')
                    name = quote.get('shortname', quote.get('longname', ''))
                    exchange = quote.get('exchDisp', quote.get('exchange', ''))
                    qtype = quote.get('quoteType', '')
                    
                    # 중복 제거
                    if qtype in ['EQUITY', 'ETF'] and symbol not in [r['symbol'] for r in results]:
                        results.append({
                            'symbol': symbol,
                            'name': name,
                            'exchange': exchange
                        })
        except Exception as e:
            pass
    
    return results[:10]

# --- 메인 UI ---
st.markdown('<h1 class="main-header">📈 주가 분석 대시보드</h1>', unsafe_allow_html=True)

# --- 사이드바 입력 ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 티커 검색 기능
    with st.expander("🔍 티커 검색 (회사명으로 찾기)", expanded=False):
        search_query = st.text_input("회사명 또는 티커 입력", placeholder="예: 삼성전자, Apple, Tesla")
        
        if search_query:
            search_results = search_ticker(search_query)
            
            if search_results:
                st.caption(f"검색 결과 ({len(search_results)}개)")
                for idx, result in enumerate(search_results[:8]):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.text(f"{result['symbol']}")
                        st.caption(f"{result['name'][:35]}..." if len(result['name']) > 35 else result['name'])
                    with col_b:
                        # 인덱스를 추가해서 키가 고유하도록 함
                        if st.button("추가", key=f"add_{idx}_{result['symbol']}", use_container_width=True):
                            # 현재 티커에 추가
                            if 'current_tickers' not in st.session_state:
                                st.session_state['current_tickers'] = ""
                            existing = st.session_state.get('current_tickers', '')
                            if result['symbol'] not in existing:
                                if existing and existing.strip():
                                    st.session_state['current_tickers'] = f"{existing}, {result['symbol']}"
                                else:
                                    st.session_state['current_tickers'] = result['symbol']
                                st.rerun()
            else:
                st.info("검색 결과가 없습니다. 영어로 검색해보세요.")
    
    st.divider()
    
    # 티커 입력
    st.subheader("종목 선택")
    
    # 세션에서 티커 가져오기
    default_tickers = st.session_state.get('current_tickers', 'AAPL, MSFT, NVDA')
    
    tickers_input = st.text_input(
        "티커 입력 (쉼표로 구분)",
        value=default_tickers,
        help="미국: AAPL, TSLA | 한국(코스피): 005930.KS | 한국(코스닥): 068270.KQ"
    )
    
    # 세션에 저장
    st.session_state['current_tickers'] = tickers_input
    
    # 인기 종목 빠른 선택
    st.markdown("##### 🚀 빠른 선택")
    
    st.caption("🇺🇸 미국")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("빅테크", key="us_bigtech", use_container_width=True):
            st.session_state['current_tickers'] = "AAPL, MSFT, GOOGL, AMZN, META"
            st.rerun()
    with col2:
        if st.button("반도체", key="us_semi", use_container_width=True):
            st.session_state['current_tickers'] = "NVDA, AMD, INTC, TSM"
            st.rerun()
    with col3:
        if st.button("전기차", key="us_ev", use_container_width=True):
            st.session_state['current_tickers'] = "TSLA, RIVN, LCID, NIO"
            st.rerun()
    with col4:
        if st.button("금융", key="us_fin", use_container_width=True):
            st.session_state['current_tickers'] = "JPM, BAC, GS, MS"
            st.rerun()
    
    st.caption("🇰🇷 한국")
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        if st.button("대형주", key="kr_large", use_container_width=True):
            st.session_state['current_tickers'] = "005930.KS, 000660.KS, 035420.KS, 035720.KS"
            st.rerun()
    with col6:
        if st.button("2차전지", key="kr_battery", use_container_width=True):
            st.session_state['current_tickers'] = "373220.KS, 006400.KS, 051910.KS"
            st.rerun()
    with col7:
        if st.button("바이오", key="kr_bio", use_container_width=True):
            st.session_state['current_tickers'] = "068270.KQ, 207940.KS, 326030.KQ"
            st.rerun()
    with col8:
        if st.button("게임", key="kr_game", use_container_width=True):
            st.session_state['current_tickers'] = "036570.KS, 251270.KS, 263750.KQ"
            st.rerun()
    
    st.divider()
    
    # 날짜 범위
    st.subheader("📅 기간 설정")
    date_preset = st.selectbox(
        "기간 프리셋",
        ["직접 입력", "최근 1개월", "최근 3개월", "최근 6개월", "최근 1년", "최근 2년", "YTD (연초부터)"]
    )
    
    today = datetime.now()
    if date_preset == "최근 1개월":
        start_date = today - timedelta(days=30)
        end_date = today
    elif date_preset == "최근 3개월":
        start_date = today - timedelta(days=90)
        end_date = today
    elif date_preset == "최근 6개월":
        start_date = today - timedelta(days=180)
        end_date = today
    elif date_preset == "최근 1년":
        start_date = today - timedelta(days=365)
        end_date = today
    elif date_preset == "최근 2년":
        start_date = today - timedelta(days=730)
        end_date = today
    elif date_preset == "YTD (연초부터)":
        start_date = datetime(today.year, 1, 1)
        end_date = today
    else:
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("시작일", value=today - timedelta(days=365))
        with col_end:
            end_date = st.date_input("종료일", value=today)
    
    st.divider()
    
    # 분석 옵션
    st.subheader("📊 분석 옵션")
    show_volume = st.checkbox("거래량 표시", value=True)
    show_ma = st.checkbox("이동평균선 (MA)", value=True)
    show_bollinger = st.checkbox("볼린저 밴드", value=False)
    show_rsi = st.checkbox("RSI 지표", value=False)
    
    if show_ma:
        ma_periods = st.multiselect(
            "이동평균 기간",
            options=[5, 10, 20, 50, 60, 120, 200],
            default=[20, 60]
        )
    else:
        ma_periods = []
    
    st.divider()
    
    # 데이터 로드 버튼
    load_button = st.button("🔍 분석 시작", type="primary", use_container_width=True)

# --- 데이터 로드 및 분석 ---
if load_button or 'stock_data' in st.session_state:
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    
    if not tickers:
        st.error("최소 1개 이상의 티커를 입력해주세요.")
    else:
        # 데이터 로드
        with st.spinner("데이터를 불러오는 중..."):
            all_data = {}
            for ticker in tickers:
                df = fetch_stock_data(
                    ticker, 
                    start_date.strftime("%Y-%m-%d"), 
                    end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else str(end_date)
                )
                if not df.empty:
                    df = calculate_returns(df)
                    df = calculate_moving_averages(df, ma_periods if show_ma else [])
                    df = calculate_volatility(df)
                    if show_rsi:
                        df = calculate_rsi(df)
                    if show_bollinger:
                        df = calculate_bollinger_bands(df)
                    all_data[ticker] = df
        
        if not all_data:
            st.error("데이터를 불러올 수 없습니다. 티커를 확인해주세요.")
        else:
            st.session_state['stock_data'] = all_data
            
            # --- 요약 통계 카드 ---
            st.subheader("📊 주요 지표")
            cols = st.columns(len(all_data))
            
            for i, (ticker, df) in enumerate(all_data.items()):
                with cols[i]:
                    current_price = df['Close'].iloc[-1]
                    total_return = df['Return'].iloc[-1]
                    volatility = df['Daily_Return'].std() * np.sqrt(252)  # 연간 변동성
                    company_name = get_company_name(ticker)
                    
                    st.metric(
                        label=f"{company_name} ({ticker})",
                        value=format_price(current_price, ticker),
                        delta=f"{total_return:.2f}%"
                    )
                    st.caption(f"연간 변동성: {volatility:.1f}%")
            
            # --- 탭 기반 차트 ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📈 수익률 비교", 
                "💰 주가 차트", 
                "📊 거래량", 
                "📉 기술적 분석",
                "🔗 상관관계"
            ])
            
            # 탭 1: 수익률 비교
            with tab1:
                fig = go.Figure()
                for ticker, df in all_data.items():
                    company_name = get_company_name(ticker)
                    display_name = f"{company_name} ({ticker})"
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['Return'],
                        mode='lines',
                        name=display_name,
                        hovertemplate=f'{company_name}: %{{y:.2f}}%<extra></extra>'
                    ))
                
                fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                             annotation_text="본전 (0%)")
                
                fig.update_layout(
                    title="누적 수익률 비교",
                    xaxis_title="날짜",
                    yaxis_title="수익률 (%)",
                    template="plotly_white",
                    hovermode="x unified",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 탭 2: 주가 차트
            with tab2:
                selected_ticker = st.selectbox("종목 선택", list(all_data.keys()))
                df = all_data[selected_ticker]
                
                fig = go.Figure()
                
                # 캔들스틱 차트
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=selected_ticker
                ))
                
                # 이동평균선
                if show_ma:
                    colors = ['orange', 'green', 'purple', 'brown']
                    for i, period in enumerate(ma_periods):
                        col_name = f'MA{period}'
                        if col_name in df.columns:
                            fig.add_trace(go.Scatter(
                                x=df.index,
                                y=df[col_name],
                                mode='lines',
                                name=f'MA{period}',
                                line=dict(color=colors[i % len(colors)], width=1)
                            ))
                
                # 볼린저 밴드
                if show_bollinger and 'BB_Upper' in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['BB_Upper'],
                        mode='lines', name='BB Upper',
                        line=dict(color='rgba(100,100,100,0.5)', dash='dot')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['BB_Lower'],
                        mode='lines', name='BB Lower',
                        line=dict(color='rgba(100,100,100,0.5)', dash='dot'),
                        fill='tonexty', fillcolor='rgba(100,100,100,0.1)'
                    ))
                
                fig.update_layout(
                    title=f"{selected_ticker} 주가 차트",
                    xaxis_title="날짜",
                    yaxis_title="가격 ($)",
                    template="plotly_white",
                    height=500,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 탭 3: 거래량
            with tab3:
                fig = go.Figure()
                colors = px.colors.qualitative.Set2
                
                for i, (ticker, df) in enumerate(all_data.items()):
                    fig.add_trace(go.Bar(
                        x=df.index,
                        y=df['Volume'],
                        name=ticker,
                        marker_color=colors[i % len(colors)],
                        opacity=0.7
                    ))
                
                fig.update_layout(
                    title="거래량 비교",
                    xaxis_title="날짜",
                    yaxis_title="거래량",
                    template="plotly_white",
                    barmode='group',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 탭 4: 기술적 분석
            with tab4:
                selected_ticker2 = st.selectbox("종목 선택 ", list(all_data.keys()), key="tech_ticker")
                df = all_data[selected_ticker2]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 일일 변동률 분포
                    fig = px.histogram(
                        df, x='Daily_Return', nbins=50,
                        title=f"{selected_ticker2} 일일 수익률 분포",
                        labels={'Daily_Return': '일일 수익률 (%)'}
                    )
                    fig.update_layout(template="plotly_white", height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # 변동성 추이
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['Volatility'],
                        mode='lines', name='20일 변동성',
                        fill='tozeroy'
                    ))
                    fig.update_layout(
                        title=f"{selected_ticker2} 변동성 추이",
                        xaxis_title="날짜",
                        yaxis_title="변동성 (%)",
                        template="plotly_white",
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # RSI 차트
                if show_rsi and 'RSI' in df.columns:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['RSI'],
                        mode='lines', name='RSI'
                    ))
                    fig.add_hline(y=70, line_dash="dash", line_color="red", 
                                 annotation_text="과매수 (70)")
                    fig.add_hline(y=30, line_dash="dash", line_color="green", 
                                 annotation_text="과매도 (30)")
                    fig.update_layout(
                        title=f"{selected_ticker2} RSI (14일)",
                        xaxis_title="날짜",
                        yaxis_title="RSI",
                        template="plotly_white",
                        height=300,
                        yaxis=dict(range=[0, 100])
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # 탭 5: 상관관계
            with tab5:
                if len(all_data) > 1:
                    # 수익률 데이터프레임 생성
                    returns_df = pd.DataFrame()
                    for ticker, df in all_data.items():
                        returns_df[ticker] = df['Daily_Return']
                    
                    # 상관관계 계산
                    corr_matrix = returns_df.corr()
                    
                    # 히트맵
                    fig = px.imshow(
                        corr_matrix,
                        text_auto='.2f',
                        color_continuous_scale='RdBu_r',
                        title="종목 간 상관관계 (일일 수익률 기준)"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("💡 상관계수가 1에 가까우면 같은 방향으로 움직이고, -1에 가까우면 반대 방향으로 움직입니다.")
                else:
                    st.info("상관관계 분석을 위해 2개 이상의 종목을 입력해주세요.")
            
            # --- 통계 요약 테이블 ---
            st.subheader("📋 상세 통계")
            
            stats_data = []
            for ticker, df in all_data.items():
                stats = {
                    '종목': ticker,
                    '현재가': format_price(df['Close'].iloc[-1], ticker),
                    '시작가': format_price(df['Close'].iloc[0], ticker),
                    '최고가': format_price(df['High'].max(), ticker),
                    '최저가': format_price(df['Low'].min(), ticker),
                    '총 수익률': f"{df['Return'].iloc[-1]:.2f}%",
                    '일평균 수익률': f"{df['Daily_Return'].mean():.3f}%",
                    '변동성 (연간)': f"{df['Daily_Return'].std() * np.sqrt(252):.2f}%",
                    '거래량 평균': f"{df['Volume'].mean():,.0f}",
                }
                stats_data.append(stats)
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)

else:
    # 환영 메시지
    st.info("👈 왼쪽 사이드바에서 종목과 기간을 설정한 후 '분석 시작' 버튼을 클릭하세요!")
    
    st.markdown("""
    ### 🚀 주요 기능
    - **수익률 비교**: 여러 종목의 누적 수익률을 한 눈에 비교
    - **캔들스틱 차트**: 상세한 가격 움직임 확인
    - **이동평균선**: 추세 분석을 위한 MA 지표
    - **볼린저 밴드**: 변동성 기반 매매 신호
    - **RSI**: 과매수/과매도 구간 확인
    - **상관관계 분석**: 종목 간 연관성 파악
    - **거래량 분석**: 거래 활성도 비교
    """)
