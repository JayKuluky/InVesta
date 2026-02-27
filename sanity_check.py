#!/usr/bin/env python3
"""
Sanity Check for Stock List Implementation
"""

import sys
sys.path.insert(0, '/Users/jaychou/Documents/InVesta')

def test_stock_list():
    """Verify the US stock list is valid"""
    print("=" * 60)
    print("TEST 1: Stock List Integrity")
    print("=" * 60)
    
    from ticker_data import US_STOCK_TICKERS, DEFAULT_TICKER
    
    print(f"✓ Total tickers in list: {len(US_STOCK_TICKERS)}")
    
    # Check for duplicates
    duplicates = [t for t in US_STOCK_TICKERS if US_STOCK_TICKERS.count(t) > 1]
    unique_duplicates = set(duplicates)
    if unique_duplicates:
        print(f"❌ Found {len(unique_duplicates)} duplicate tickers: {unique_duplicates}")
        return False
    print("✓ No duplicates found")
    
    # Check default ticker is in list
    if DEFAULT_TICKER not in US_STOCK_TICKERS:
        print(f"❌ Default ticker {DEFAULT_TICKER} not in list")
        return False
    print(f"✓ Default ticker {DEFAULT_TICKER} is in list")
    
    # Check for empty strings or None
    invalid = [t for t in US_STOCK_TICKERS if not t or not isinstance(t, str)]
    if invalid:
        print(f"❌ Found {len(invalid)} invalid tickers")
        return False
    print("✓ All tickers are valid strings")
    
    print(f"Sample tickers: {US_STOCK_TICKERS[:10]}")
    print()
    return True


def test_search_function():
    """Test the search_tickers function"""
    print("=" * 60)
    print("TEST 2: Search Function")
    print("=" * 60)
    
    from ticker_data import search_tickers, DEFAULT_TICKER
    
    # Test 1: Empty query
    results = search_tickers("")
    print(f"✓ Empty query returns: {results}")
    if results[0] != DEFAULT_TICKER:
        print(f"❌ Expected {DEFAULT_TICKER}, got {results[0]}")
        return False
    print(f"✓ Empty query returns default ticker")
    
    # Test 2: Prefix search
    results = search_tickers("AA", limit=5)
    print(f"✓ Search 'AA' returns: {results[:3]}...")
    if not results:
        print("❌ No results for 'AA' search")
        return False
    print("✓ Prefix search works")
    
    # Test 3: Known ticker
    results = search_tickers("NVDA", limit=5)
    print(f"✓ Search 'NVDA' returns: {results}")
    if "NVDA" not in results:
        print("❌ NVDA not in results")
        return False
    print("✓ Known ticker search works")
    
    # Test 4: Non-existent prefix (should return default)
    results = search_tickers("XYZ", limit=5)
    print(f"✓ Search 'XYZ' returns: {results}")
    
    print()
    return True


def test_app_imports():
    """Test that app.py imports correctly"""
    print("=" * 60)
    print("TEST 3: App Imports")
    print("=" * 60)
    
    try:
        from app import main
        print("✓ app.py imports successfully")
    except Exception as e:
        print(f"❌ app.py import failed: {e}")
        return False
    
    try:
        from ticker_data import DEFAULT_TICKER, search_tickers
        print("✓ ticker_data imports successfully")
    except Exception as e:
        print(f"❌ ticker_data import failed: {e}")
        return False
    
    print()
    return True


def test_auto_add_logic():
    """Test automatic ticker addition"""
    print("=" * 60)
    print("TEST 4: Auto-Add Logic")
    print("=" * 60)
    
    from ticker_data import DEFAULT_TICKER, search_tickers
    
    # Simulate: if ticker_search is empty, use default
    ticker_search = ""
    
    if ticker_search:
        matching_tickers = search_tickers(ticker_search, limit=10)
        ticker_input = matching_tickers[0] if matching_tickers else DEFAULT_TICKER
    else:
        matching_tickers = search_tickers("AAPL", limit=1)
        ticker_input = matching_tickers[0] if matching_tickers else DEFAULT_TICKER
    
    print(f"✓ When search is empty, ticker = {ticker_input}")
    if ticker_input != DEFAULT_TICKER:
        print(f"❌ Expected {DEFAULT_TICKER}, got {ticker_input}")
        return False
    print("✓ Auto-add logic works correctly")
    
    print()
    return True


def test_module_imports():
    """Test all module imports"""
    print("=" * 60)
    print("TEST 5: Module Imports")
    print("=" * 60)
    
    modules = ["config", "database", "portfolio", "ui", "ticker_data"]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} imported")
        except Exception as e:
            print(f"❌ {module} import failed: {e}")
            return False
    
    print()
    return True


def run_all_tests():
    """Run all sanity checks"""
    print("\n")
    print("🔍 SANITY CHECK FOR 500+ STOCK LIST 🔍")
    print("=" * 60)
    print()
    
    tests = [
        ("Stock List", test_stock_list),
        ("Search Function", test_search_function),
        ("App Imports", test_app_imports),
        ("Auto-Add Logic", test_auto_add_logic),
        ("Module Imports", test_module_imports),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
            import traceback
            traceback.print_exc()
    
    # Summary
    print("=" * 60)
    print("SANITY CHECK SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All sanity checks passed!")
    else:
        print(f"⚠️ {total - passed} check(s) failed")
    
    print()


if __name__ == "__main__":
    run_all_tests()
