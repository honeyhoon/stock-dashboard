import yfinance as yf

ticker = "TSLA"
print(f"Testing {ticker}...")

try:
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    print(f"History shape: {df.shape}")
    if df.empty:
        print("History is empty!")
    else:
        print("History fetched successfully.")

    print("Attempting to fetch info...")
    try:
        info = stock.info
        print("Info fetched keys:", list(info.keys())[:5])
    except Exception as e:
        print(f"Info fetch failed: {e}")

except Exception as e:
    print(f"Critical error: {e}")
