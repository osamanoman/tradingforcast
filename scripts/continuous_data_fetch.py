from modules.ticker_dwn import dwn_data
import time

# Download data for GLD, SPY, and QQQ and the new tickers every 5 minutes
new_tickers = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA"]

while True:
    print("Fetching data for:", new_tickers)
    dwn_data(select=new_tickers, is_json=True) 
    print("Data fetch complete. Waiting 5 minutes...") 
    time. sleep(300) # 5 minutes 