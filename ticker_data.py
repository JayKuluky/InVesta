"""
Ticker search and stock data module for InVesta.
Provides real-time ticker search and chart data with Nasdaq sync fallback.
"""

from typing import List, Dict, Optional
import logging
import yfinance as yf
import pandas as pd
import streamlit as st

from ticker_sync import get_sync_manager

# Suppress warnings
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

# Fallback: Local 218-ticker list (used if Nasdaq sync fails)
US_STOCK_TICKERS = [
    "AAL", "AAPL", "ABBV", "ACN", "ADBE", "ADDYY", "AEP", "AIG", "ALL", "AMD",
    "AMGN", "AMZN", "APD", "AXP", "BAC", "BA", "BLK", "BRK.A", "BRK.B", "BWA",
    "C", "CAL", "CAT", "CBOE", "CARR", "CHD", "CHTR", "CMCSA", "COP", "COST",
    "CPRI", "CRM", "CRSP", "CSCO", "CTSH", "CVX", "DAL", "DASH", "DD", "DIS",
    "DOW", "DRUKF", "DUK", "EDIT", "EBAY", "EQIX", "EQR", "ETN", "EXAS", "EXC",
    "EXPD", "F", "FCX", "FDX", "FITB", "FOXA", "FOX", "FRC", "GE", "GELYY",
    "GHC", "GILD", "GM", "GS", "GTLB", "GTLS", "GOOG", "GOOGL", "HD", "HI",
    "HMC", "HON", "HRSTY", "HYMTF", "IBM", "ILMN", "IMAX", "INSW", "INTC",
    "INTU", "IONM", "IP", "ITW", "JNJ", "JPM", "KKR", "KMB", "KO", "LIN",
    "LIONSB", "LLY", "LMT", "LPL", "LOW", "LRCX", "LUV", "LYB", "LYFT", "MA",
    "MAC", "MCD", "MDLZ", "META", "MLL", "MONDELEZ", "MOS", "MRVL", "MU", "MS",
    "NEE", "NEM", "NFLX", "NKE", "NSANY", "NUVA", "ORCL", "O", "PEP", "PFE",
    "PG", "PINS", "PKG", "PLD", "PNW", "PPL", "PRU", "PSA", "PSX", "PYPL",
    "QCOM", "QSR", "RBLX", "REGN", "RL", "RLOG", "ROP", "RTX", "SAP", "SBUX",
    "SCHW", "SE", "SHCO", "SHO", "SIVB", "SKX", "SLB", "SNPS", "SO", "SPOT",
    "SQ", "STAG", "STLD", "SW", "T", "TMUS", "TMO", "TT", "UGI", "UL", "UNH",
    "UPS", "UAL", "VLC", "VLO", "VOD", "VRTX", "VZ", "WDAY", "WELL", "WFC",
    "WLK", "WMT", "WIRE", "WRK", "XYLEM", "XOM", "YUM", "VWAGY",
]

DEFAULT_TICKER = "AAPL"


@st.cache_resource
def initialize_ticker_sync():
    """Initialize and sync Nasdaq ticker database if needed."""
    manager = get_sync_manager()
    try:
        manager.sync_if_needed()
        ticker_count = manager.get_ticker_count()
        if ticker_count > 0:
            logging.info(f"Ticker database ready: {ticker_count} tickers")
            return True
    except Exception as e:
        logging.warning(f"Nasdaq sync failed, using local ticker list: {e}")
    return False


@st.cache_data(ttl=3600)
def search_tickers(query: str, limit: int = 10) -> List[str]:
    """
    Search for tickers from Nasdaq database or local list.
    
    Args:
        query: Search query (e.g., "NVDA" or "apple")
        limit: Max number of results
    
    Returns:
        List of matching ticker symbols
    """
    if not query or len(query) < 1:
        return [DEFAULT_TICKER]
    
    manager = get_sync_manager()
    ticker_count = manager.get_ticker_count()
    
    # Use Nasdaq database if available
    if ticker_count > 0:
        try:
            options = manager.get_ticker_options(query)
            tickers = [manager.get_ticker_from_option(opt) for opt in options]
            tickers = [t for t in tickers if t]  # Filter out None values
            if tickers:
                return tickers[:limit]
        except Exception as e:
            logging.warning(f"Error searching Nasdaq database: {e}")
    
    # Fallback to local list
    query_upper = query.upper().strip()
    matches = sorted([t for t in US_STOCK_TICKERS if t.startswith(query_upper)])
    
    if not matches:
        matches = sorted([t for t in US_STOCK_TICKERS if query_upper in t])
    
    return matches[:limit] if matches else [DEFAULT_TICKER]


def get_formatted_ticker_options(search_query: str = "") -> List[str]:
    """
    Get formatted ticker options for UI selectbox.
    
    Args:
        search_query: Optional search filter
    
    Returns:
        List of formatted strings: "SYMBOL | Name (Type)"
    """
    manager = get_sync_manager()
    ticker_count = manager.get_ticker_count()
    
    if ticker_count > 0:
        try:
            return manager.get_ticker_options(search_query)
        except Exception as e:
            logging.warning(f"Error getting formatted options: {e}")
    
    # Fallback: format local list (return all 218 tickers or filtered results)
    options = []
    search_upper = search_query.strip().upper() if search_query else ""
    
    for ticker in US_STOCK_TICKERS:
        # Filter by search query if provided
        if search_upper:
            if not (ticker.upper().startswith(search_upper) or search_upper in ticker.upper()):
                continue
        
        display = f"{ticker} | {ticker}"
        options.append(display)
    
    return options


def get_ticker_from_option(option: str) -> str:
    """
    Extract ticker symbol from formatted option string.
    
    Args:
        option: Formatted string like "AAPL | Apple Inc. (Stock)"
    
    Returns:
        Ticker symbol extracted from option
    """
    manager = get_sync_manager()
    ticker = manager.get_ticker_from_option(option)
    if ticker:
        return ticker
    
    # Fallback: extract from local format
    if " | " in option:
        return option.split(" | ")[0].strip()
    return option


@st.cache_data(ttl=600)
def get_stock_info(ticker: str) -> Optional[Dict]:
    """
    Get detailed stock information from yfinance.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with stock info or None if error
    """
    try:
        data = yf.Ticker(ticker)
        info = data.info
        
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


@st.cache_data(ttl=1800)
def batch_fetch_prices(tickers: List[str]) -> Dict[str, float]:
    """
    Fetch current prices for multiple tickers in batch with fallback support.
    
    Args:
        tickers: List of ticker symbols
    
    Returns:
        Dictionary of {ticker: price} with valid prices only. Skips tickers with NaN values.
    """
    if not tickers:
        return {}
    
    prices = {}
    failed_tickers = []
    
    try:
        data = yf.download(
            " ".join(tickers),
            period="1d",
            progress=False,
        )
        
        if len(tickers) == 1:
            # Single ticker returns Series
            try:
                price = float(data["Close"].iloc[-1].item())
                if not pd.isna(price):  # Only add if not NaN
                    prices[tickers[0]] = price
                else:
                    failed_tickers.append(tickers[0])
            except (ValueError, TypeError, IndexError):
                failed_tickers.append(tickers[0])
        else:
            # Multiple tickers return DataFrame with MultiIndex columns
            if isinstance(data, pd.DataFrame):
                for ticker in tickers:
                    try:
                        # Try MultiIndex column: ('Close', 'AAPL')
                        if ("Close", ticker) in data.columns:
                            price = float(data[("Close", ticker)].iloc[-1].item())
                            if not pd.isna(price):
                                prices[ticker] = price
                            else:
                                failed_tickers.append(ticker)
                        # Fallback: try simple column access
                        elif ticker in data.columns:
                            price = float(data[ticker]["Close"].iloc[-1].item())
                            if not pd.isna(price):
                                prices[ticker] = price
                            else:
                                failed_tickers.append(ticker)
                        else:
                            failed_tickers.append(ticker)
                    except (KeyError, ValueError, TypeError, IndexError) as e:
                        failed_tickers.append(ticker)
        
        # Log failures for debugging but don't fail silently
        if failed_tickers:
            logging.warning(f"Could not fetch prices for: {', '.join(failed_tickers)}")
        
        return prices
    except Exception as e:
        logging.error(f"Error batch fetching prices: {e}")
        return {}
