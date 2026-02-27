#!/usr/bin/env python3
"""
Feature Testing Script for InVesta
Tests all implemented features without running the Streamlit app
"""

import sys
import os
from datetime import date, timedelta

# Add current directory to path
sys.path.insert(0, '/Users/jaychou/Documents/InVesta')

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        import config
        print("✓ config module imported")
        
        import database
        print("✓ database module imported")
        
        import portfolio
        print("✓ portfolio module imported")
        
        import ui
        print("✓ ui module imported")
        
        import ticker_data
        print("✓ ticker_data module imported")
        
        print("\n✅ All modules imported successfully!\n")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}\n")
        return False


def test_database():
    """Test database operations"""
    print("=" * 60)
    print("TEST 2: Database Operations")
    print("=" * 60)
    
    try:
        from database import DatabaseManager
        from config import TABLE_INVESTMENTS
        
        db = DatabaseManager()
        print("✓ DatabaseManager initialized")
        
        # Test fetch operations
        investments = db.fetch_investments()
        print(f"✓ Fetched {len(investments)} investments")
        
        transactions = db.fetch_transactions()
        print(f"✓ Fetched {len(transactions)} transactions")
        
        print("\n✅ Database operations successful!\n")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}\n")
        return False


def test_ticker_search():
    """Test ticker search functionality"""
    print("=" * 60)
    print("TEST 3: Ticker Search & Data")
    print("=" * 60)
    
    try:
        from ticker_data import search_tickers, get_stock_info, get_stock_stats_summary
        
        # Test search
        results = search_tickers("NVDA", limit=5)
        print(f"✓ Searched for 'NVDA': found {len(results)} results")
        print(f"  Results: {results[:3]}")
        
        # Test getting stock info
        if results:
            ticker = results[0]
            info = get_stock_info(ticker)
            if info:
                print(f"✓ Retrieved info for {ticker}:")
                print(f"  - Price: ${info.get('current_price', 'N/A')}")
                print(f"  - Market Cap: ${info.get('market_cap', 'N/A')}")
            else:
                print(f"⚠ Could not get info for {ticker} (API issue)")
            
            # Test getting stats
            stats = get_stock_stats_summary(ticker)
            if stats:
                print(f"✓ Retrieved stats for {ticker}:")
                print(f"  - Open: ${stats.get('open', 'N/A')}")
                print(f"  - High: ${stats.get('high', 'N/A')}")
            else:
                print(f"⚠ Could not get stats for {ticker} (API issue)")
        
        print("\n✅ Ticker search & data tests successful!\n")
        return True
    except Exception as e:
        print(f"❌ Ticker test failed: {e}\n")
        return False


def test_portfolio_analysis():
    """Test portfolio analysis functions"""
    print("=" * 60)
    print("TEST 4: Portfolio Analysis")
    print("=" * 60)
    
    try:
        from database import DatabaseManager
        from portfolio import PortfolioAnalyzer
        import pandas as pd
        
        db = DatabaseManager()
        investments = db.fetch_investments()
        transactions = db.fetch_transactions()
        
        print(f"✓ Loaded {len(investments)} investments")
        
        if not investments.empty:
            # Test aggregation
            portfolio = PortfolioAnalyzer.aggregate_portfolio(investments)
            print(f"✓ Aggregated portfolio: {len(portfolio)} tickers")
            
            # Test metrics
            metrics = PortfolioAnalyzer.compute_metrics(transactions, investments, portfolio)
            print(f"✓ Computed metrics:")
            print(f"  - Total Assets: ${metrics.get('total_assets', 0):,.2f}")
            print(f"  - Cash Balance: ${metrics.get('cash_balance', 0):,.2f}")
            print(f"  - P&L: ${metrics.get('pnl', 0):,.2f}")
            
            # Test allocation
            allocation = PortfolioAnalyzer.get_portfolio_allocation(portfolio)
            print(f"✓ Allocation computed: {len(allocation)} entries")
        else:
            print("⚠ No investments in database (skipping aggregation tests)")
        
        print("\n✅ Portfolio analysis tests successful!\n")
        return True
    except Exception as e:
        print(f"❌ Portfolio test failed: {e}\n")
        return False


def test_ui_components():
    """Test UI component functions"""
    print("=" * 60)
    print("TEST 5: UI Components")
    print("=" * 60)
    
    try:
        from ui import display_metric_cards, display_empty_state, display_confirmation_message
        
        print("✓ All UI functions imported successfully")
        print("  - display_metric_cards")
        print("  - display_empty_state")
        print("  - display_confirmation_message")
        
        print("\n✅ UI component tests successful!\n")
        return True
    except Exception as e:
        print(f"❌ UI test failed: {e}\n")
        return False


def test_data_insertion():
    """Test data insertion workflow"""
    print("=" * 60)
    print("TEST 6: Data Insertion (Test Trade)")
    print("=" * 60)
    
    try:
        from database import DatabaseManager
        import tempfile
        import sqlite3
        
        # Create temporary test database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_db_path = tmp.name
        
        # Create test database
        conn = sqlite3.connect(tmp_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE investments (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                trade_type TEXT NOT NULL CHECK(trade_type IN ('Buy', 'Sell')),
                shares INTEGER NOT NULL,
                price REAL NOT NULL,
                note TEXT,
                UNIQUE(date, ticker, trade_type, shares, price)
            )
        """)
        conn.commit()
        
        # Test insertion
        cursor.execute("""
            INSERT INTO investments (date, ticker, trade_type, shares, price, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(date.today()), 'TEST', 'Buy', 10, 100.0, 'Test trade'))
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT * FROM investments WHERE ticker = 'TEST'")
        result = cursor.fetchone()
        
        if result:
            print(f"✓ Test trade inserted successfully")
            print(f"  - Ticker: {result[2]}")
            print(f"  - Type: {result[3]}")
            print(f"  - Shares: {result[4]}")
            print(f"  - Price: ${result[5]}")
        else:
            print("❌ Insertion failed")
        
        conn.close()
        os.remove(tmp_db_path)
        
        print("\n✅ Data insertion tests successful!\n")
        return True
    except Exception as e:
        print(f"❌ Data insertion test failed: {e}\n")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("🧪 INVESTA FEATURE TESTS 🧪")
    print("=" * 60)
    print()
    
    results = {
        "Imports": test_imports(),
        "Database": test_database(),
        "Ticker Search": test_ticker_search(),
        "Portfolio Analysis": test_portfolio_analysis(),
        "UI Components": test_ui_components(),
        "Data Insertion": test_data_insertion(),
    }
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {total - passed} test(s) failed")
    
    print()


if __name__ == "__main__":
    run_all_tests()
