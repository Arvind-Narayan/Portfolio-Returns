import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_current_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        current_price = stock.info['regularMarketPrice']
        return True, current_price
    except Exception as e:
        return False, f"Error fetching price for {symbol}: {str(e)}"

def get_historical_prices(symbol, start_date, end_date=None):
    try:
        if end_date is None:
            end_date = datetime.now()
        
        stock = yf.Ticker(symbol)
        hist_data = stock.history(start=start_date, end=end_date)
        return True, hist_data['Close']
    except Exception as e:
        return False, f"Error fetching historical prices for {symbol}: {str(e)}"

def validate_symbol(symbol):
    try:
        stock = yf.Ticker(symbol)
        # Try to get info - will fail if symbol is invalid
        _ = stock.info
        return True, "Valid symbol"
    except Exception as e:
        return False, f"Invalid symbol: {str(e)}" 
    
def get_current_prices(symbols):
    """
    Get current prices for multiple stock symbols
    Returns a dictionary of {symbol: price}
    """
    try:
        prices = {}
        for symbol in symbols:
            success, price = get_current_price(symbol)
            if success:
                prices[symbol] = price
            else:
                return False, f"Error fetching price for {symbol}"
        return True, prices
    except Exception as e:
        return False, f"Error fetching prices: {str(e)}"

# print(get_historical_prices('MSFT', '2025-01-01', '2025-02-26')) 