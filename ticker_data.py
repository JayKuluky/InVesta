"""
Ticker search and stock data module for InVesta.
Provides real-time ticker search and chart data.
"""

from typing import List, Dict, Tuple, Optional
import logging
import yfinance as yf
import pandas as pd
import streamlit as st

# Suppress yfinance and urllib3 warnings
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)


# S&P 500 和其他主要美股列表（无重复）
US_STOCK_TICKERS = [
    # Big Tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
    # Finance
    "JPM", "BAC", "WFC", "GS", "C", "BLK", "SCHW", "CBOE",
    # Healthcare
    "JNJ", "UNH", "PFE", "MRK", "ABBV", "TMO", "GILD", "BIIB",
    # Energy
    "XOM", "CVX", "COP", "MPC", "PSX", "VLO", "EOG", "SLB",
    # Materials
    "LIN", "APD", "DOW", "DD", "NEM", "FCX", "STLD", "MTH",
    # Industrials
    "BA", "CAT", "GE", "RTX", "LMT", "HON", "ITW", "CARR",
    # Consumer
    "WMT", "KO", "PEP", "MCD", "NKE", "HD", "LOW", "COST",
    # Communication
    "VZ", "T", "CMCSA", "CHTR", "DIS", "NFLX", "CHARS",
    # Real Estate
    "PLD", "EQIX", "EQR", "ARE", "SHO", "PSA", "WELL",
    # Utilities
    "NEE", "DUK", "SO", "EXC", "AEP", "PPL", "PNW",
    # Insurance
    "BRK.B", "BRK.A", "ALL", "AIG", "PRU", "LPL", "FRC",
    # Pharmaceuticals & Biotech
    "LLY", "AMGN", "REGN", "VRTX", "CRSP", "EDIT", "EXAS", "ILMN",
    # Semiconductors
    "AMD", "QCOM", "INTC", "MRVL", "AVGO", "TXN", "INTU", "SNPS",
    # Software & IT Services
    "ORCL", "IBM", "SAP", "CRM", "SNOW", "ADBE", "ASML", "WDAY",
    # E-commerce & Internet
    "EBAY", "PINS", "UBER", "LYFT", "DASH", "SE", "SPOT", "RBLX",
    # Airlines & Transportation
    "DAL", "UAL", "AAL", "SW", "EXPD", "FDX", "UPS", "LUV",
    # Retail & Discretionary
    "F", "GM", "TM", "HMC", "BWA", "MAC", "CPRI", "RL",
    # Media & Entertainment
    "PARA", "FOXA", "FOX", "LIONSB", "IMAX", "MSON",
    # Banking & Financial
    "MS", "PYPL", "SQ", "SIVB",
    # Automotive
    "VWAGY", "NSANY", "GELYY", "HYMTF",
    # Apparel & Footwear
    "ADDYY", "VFC", "PVH", "ON", "SKX",
    # Household Products
    "PG", "CL", "CLX", "KMB", "HRL", "NUVA", "UL", "DRUKF",
    # Food & Beverage
    "SBUX", "QSR", "KKR", "MONDELEZ", "MDLZ", "CALX",
    # Chemicals
    "LYB", "IONM", "CE", "EMN", "WLK",
    # Paper & Packaging
    "IP", "WRK", "PKG", "MLL", "BOX", "GMS", "PGH", "UGI",
    # Machinery
    "XYLEM", "INSW", "GHC", "WIRE", "HI", "RLOG", "SHCO",
    # Electronics & Components
    "CCI", "TMUS", "VOD", "O", "STAG", "MINT",
    # Miscellaneous
    "ETN", "TT", "HRSTY", "PWR", "MOS", "CEL",
    # Additional Major Companies
    "AXP", "CAL", "CHD", "CSCO", "ACN", "CTSH", "V", "MA",
    "PYPL", "YUM", "MU", "LRCX", "ROP", "ROP", "GTLB", "GTLS",
    "EWBC", "FITB", "CMG", "EBAY", "PING", "POWI", "PSTG", "PGTI",
]

# Remove any duplicates by converting to set and back to list
US_STOCK_TICKERS = sorted(list(set(US_STOCK_TICKERS)))

# Default ticker if nothing selected
DEFAULT_TICKER = "AAPL"


@st.cache_data(ttl=3600)
def search_tickers(query: str, limit: int = 10) -> List[str]:
    """
    Search for tickers matching the query from US stock list.
    
    Args:
        query: Search query (e.g., "NVDA" or "NV")
        limit: Max number of results to return
    
    Returns:
        List of matching ticker symbols
    """
    if not query or len(query) < 1:
        # Return top tickers when no query
        return [DEFAULT_TICKER]
    
    query_upper = query.upper().strip()
    
    # Search for tickers starting with query
    matches = sorted([t for t in US_STOCK_TICKERS if t.startswith(query_upper)])
    
    # If no prefix matches, try substring matches
    if not matches:
        matches = sorted([t for t in US_STOCK_TICKERS if query_upper in t])
    
    return matches[:limit] if matches else [DEFAULT_TICKER]


@st.cache_data(ttl=600)
def get_stock_info(ticker: str) -> Optional[Dict]:
    """
    Get detailed stock information.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with stock info or None if error
    """
    try:
        data = yf.Ticker(ticker)
        info = data.info
        
        # Extract key fields
        return {
            "symbol": ticker,
            "name": info.get("longName", ""),
            "current_price": info.get("currentPrice", 0),
            "high_52w": info.get("fiftyTwoWeekHigh", 0),
            "low_52w": info.get("fiftyTwoWeekLow", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_daily_stock_data(ticker: str) -> Optional[pd.DataFrame]:
    """Get today's stock data (OHLCV)."""
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data
        return None
    except Exception:
        return None


@st.cache_data(ttl=600)
def get_historical_data(ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
    """
    Get historical stock data for charting.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y')
    
    Returns:
        DataFrame with historical data or None
    """
    try:
        data = yf.Ticker(ticker).history(period=period)
        if not data.empty:
            return data
        return None
    except Exception:
        return None


def get_stock_stats_summary(ticker: str) -> Optional[Dict]:
    """
    Get comprehensive stock statistics.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with stock stats
    """
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        
        if hist.empty:
            return None
        
        latest = hist.iloc[-1]
        
        return {
            "close": latest.get("Close", 0),
            "open": latest.get("Open", 0),
            "high": latest.get("High", 0),
            "low": latest.get("Low", 0),
            "volume": latest.get("Volume", 0),
        }
    except Exception:
        return None
