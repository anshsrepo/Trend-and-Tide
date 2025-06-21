import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import os

def get_stock_price(ticker):
    # Normalize ticker for Yahoo Finance (e.g., "TATA MOTORS" -> "TATAMOTORS.NS")
    ticker = ticker.strip().upper().replace(" ", "")
    if not ticker.endswith(".NS"):
        ticker += ".NS"

    try:
        stock = yf.Ticker(ticker)
        # Fetch the latest 1-day history to get the most recent price
        history = stock.history(period="1d")
        if history.empty:
            return f"Error: No price data found for {ticker}"
        price = history['Close'][-1]  # Get the latest closing price
        return f"The latest stock price of {ticker} is ₹{price:.2f}"
    except Exception as e:
        return f"Error fetching stock price: {str(e)}"

def calculate_SMA(ticker, window):
    ticker = ticker.strip().upper().replace(" ", "") + ".NS"
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        if history.empty:
            return f"Error: No historical data found for {ticker}"
        sma = history['Close'].rolling(window=window).mean().iloc[-1]
        return f"The {window}-day SMA for {ticker} is ₹{sma:.2f}"
    except Exception as e:
        return f"Error calculating SMA: {str(e)}"

def calculate_EMA(ticker, window):
    ticker = ticker.strip().upper().replace(" ", "") + ".NS"
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        if history.empty:
            return f"Error: No historical data found for {ticker}"
        ema = history['Close'].ewm(span=window, adjust=False).mean().iloc[-1]
        return f"The {window}-day EMA for {ticker} is ₹{ema:.2f}"
    except Exception as e:
        return f"Error calculating EMA: {str(e)}"

def calculate_RSI(ticker, period=14):
    ticker = ticker.strip().upper().replace(" ", "") + ".NS"
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        if history.empty:
            return f"Error: No historical data found for {ticker}"
        delta = history['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return f"The RSI for {ticker} (period={period}) is {rsi.iloc[-1]:.2f}"
    except Exception as e:
        return f"Error calculating RSI: {str(e)}"

def calculate_MACD(ticker):
    ticker = ticker.strip().upper().replace(" ", "") + ".NS"
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        if history.empty:
            return f"Error: No historical data found for {ticker}"
        exp1 = history['Close'].ewm(span=12, adjust=False).mean()
        exp2 = history['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return f"MACD for {ticker}: MACD Line: {macd.iloc[-1]:.2f}, Signal Line: {signal.iloc[-1]:.2f}"
    except Exception as e:
        return f"Error calculating MACD: {str(e)}"

def plot_stock_price(ticker):
    ticker = ticker.strip().upper().replace(" ", "") + ".NS"
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="6mo")
        if history.empty:
            return f"Error: No historical data found for {ticker}"
        
        # Create a directory for charts if it doesn't exist
        if not os.path.exists("static/charts"):
            os.makedirs("static/charts")
        
        # Plot using mplfinance
        chart_path = f"charts/{ticker}_price.png"
        mpf.plot(history, type='candle', style='charles', title=f"{ticker} Stock Price (6 Months)",
                 ylabel="Price (₹)", volume=True, savefig=f"static/{chart_path}")
        
        return chart_path
    except Exception as e:
        return f"Error plotting stock price: {str(e)}"

# Dictionary to map actions to functions
available_functions = {
    "get_stock_price": get_stock_price,
    "calculate_SMA": calculate_SMA,
    "calculate_EMA": calculate_EMA,
    "calculate_RSI": calculate_RSI,
    "calculate_MACD": calculate_MACD,
    "plot_stock_price": plot_stock_price
}

# List of function metadata for dynamic usage (e.g., in the UI)
functions = [
    {
        "name": "get_stock_price",
        "description": "Gets the latest stock price for a given ticker symbol.",
        "parameters": {
            "ticker": {"type": "string", "description": "The stock ticker symbol (e.g., TATAMOTORS)"}
        }
    },
    {
        "name": "calculate_SMA",
        "description": "Calculates the Simple Moving Average for a given stock ticker and window.",
        "parameters": {
            "ticker": {"type": "string", "description": "The stock ticker symbol (e.g., TATAMOTORS)"},
            "window": {"type": "integer", "description": "The number of days for the SMA calculation"}
        }
    },
    {
        "name": "calculate_EMA",
        "description": "Calculates the Exponential Moving Average for a given stock ticker and window.",
        "parameters": {
            "ticker": {"type": "string", "description": "The stock ticker symbol (e.g., TATAMOTORS)"},
            "window": {"type": "integer", "description": "The number of days for the EMA calculation"}
        }
    },
    {
        "name": "calculate_RSI",
        "description": "Calculates the Relative Strength Index for a given stock ticker.",
        "parameters": {
            "ticker": {"type": "string", "description": "The stock ticker symbol (e.g., TATAMOTORS)"}
        }
    },
    {
        "name": "calculate_MACD",
        "description": "Calculates the Moving Average Convergence Divergence for a given stock ticker.",
        "parameters": {
            "ticker": {"type": "string", "description": "The stock ticker symbol (e.g., TATAMOTORS)"}
        }
    },
    {
        "name": "plot_stock_price",
        "description": "Plots the stock price for the last 6 months for a given ticker symbol.",
        "parameters": {
            "ticker": {"type": "string", "description": "The stock ticker symbol (e.g., TATAMOTORS)"}
        }
    }
]