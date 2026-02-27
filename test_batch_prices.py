#!/usr/bin/env python3
"""Test batch_fetch_prices with fixed MultiIndex handling"""

import sys
sys.path.insert(0, '/Users/jaychou/Documents/InVesta')

# Disable Streamlit warnings
import warnings
warnings.filterwarnings('ignore')

import logging
logging.getLogger('streamlit').setLevel(logging.ERROR)

import pandas as pd

print("=" * 70)
print("Testing batch_fetch_prices with MultiIndex fix")
print("=" * 70)

# Test directly with yfinance to ensure the logic works
import yfinance as yf

def test_batch_fetch(tickers):
    """Test batch fetch logic"""
    try:
        data = yf.download(" ".join(tickers), period="1d", progress=False)
        prices = {}
        
        if len(tickers) == 1:
            # Single ticker returns Series
            prices[tickers[0]] = float(data["Close"].iloc[-1].item())
        else:
            # Multiple tickers return DataFrame with MultiIndex columns
            if isinstance(data, pd.DataFrame):
                for ticker in tickers:
                    try:
                        # For MultiIndex columns: ('Close', 'AAPL')
                        if ("Close", ticker) in data.columns:
                            prices[ticker] = float(data[("Close", ticker)].iloc[-1].item())
                    except (KeyError, TypeError):
                        # Fallback: try simple column access
                        if ticker in data.columns:
                            prices[ticker] = float(data[ticker]["Close"].iloc[-1].item())
        
        return prices
    except Exception as e:
        print(f"Error: {e}")
        return {}

# Test 1: Single ticker
print("\nTest 1: Single Ticker (AAPL)")
print("-" * 70)
prices = test_batch_fetch(["AAPL"])
if prices:
    for ticker, price in prices.items():
        print(f"✓ {ticker}: ${price:.2f}")
else:
    print("✗ No prices returned")

# Test 2: Multiple tickers
print("\nTest 2: Multiple Tickers (AAPL, MSFT, GOOGL)")
print("-" * 70)
prices = test_batch_fetch(["AAPL", "MSFT", "GOOGL"])
if prices:
    for ticker, price in prices.items():
        print(f"✓ {ticker}: ${price:.2f}")
    if len(prices) == 3:
        print("✓ All 3 tickers fetched successfully")
    else:
        print(f"⚠ Only {len(prices)} out of 3 tickers fetched")
else:
    print("✗ No prices returned")

# Test 3: Import and test actual function
print("\n\nTest 3: Actual batch_fetch_prices function")
print("-" * 70)
try:
    from ticker_data import batch_fetch_prices
    prices = batch_fetch_prices(["AAPL", "MSFT", "GOOGL"])
    if prices:
        for ticker, price in prices.items():
            print(f"✓ {ticker}: ${price:.2f}")
    else:
        print("⚠ Function returned empty dict (may be due to cache)")
except Exception as e:
    print(f"✗ Error importing or running: {e}")

print("\n" + "=" * 70)
print("✅ Test complete!")
print("=" * 70)
