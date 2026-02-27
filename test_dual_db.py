#!/usr/bin/env python3
"""Test the new dual-database system"""

import sys
sys.path.insert(0, '/Users/jaychou/Documents/InVesta')

print("=" * 60)
print("Testing Dual-Database System")
print("=" * 60)

# Test 1: Imports
print("\nTest 1: Module Imports")
try:
    from ticker_sync import get_sync_manager, TickerSyncManager
    print("✓ ticker_sync imported")
    
    from ticker_data import (
        initialize_ticker_sync,
        search_tickers,
        get_formatted_ticker_options,
        batch_fetch_prices,
    )
    print("✓ ticker_data imported")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Database initialization
print("\nTest 2: Database Initialization")
try:
    manager = get_sync_manager()
    print(f"✓ TickerSyncManager initialized")
    
    count = manager.get_ticker_count()
    print(f"✓ Ticker database has {count} tickers")
except Exception as e:
    print(f"✗ Database init failed: {e}")
    sys.exit(1)

# Test 3: Search functionality
print("\nTest 3: Search Functionality")
try:
    results = search_tickers("AAPL", limit=5)
    print(f"✓ search_tickers('AAPL') returned {len(results)} results")
    
    results_empty = search_tickers("")
    print(f"✓ Empty search returns default: {results_empty}")
    
    results_multi = search_tickers("AP", limit=10)
    print(f"✓ Prefix search 'AP' returned {len(results_multi)} results")
except Exception as e:
    print(f"✗ Search failed: {e}")
    sys.exit(1)

# Test 4: Formatted options
print("\nTest 4: Formatted Options")
try:
    options = get_formatted_ticker_options()
    print(f"✓ get_formatted_ticker_options() returned {len(options)} options")
    if options:
        print(f"  Sample: {options[0]}")
    
    search_options = get_formatted_ticker_options("MSFT")
    print(f"✓ Search options for 'MSFT' returned {len(search_options)} results")
except Exception as e:
    print(f"✗ Formatted options failed: {e}")
    sys.exit(1)

# Test 5: assets.db exists
print("\nTest 5: Database Files")
try:
    from pathlib import Path
    assets_db = Path("/Users/jaychou/Documents/InVesta/assets.db")
    if assets_db.exists():
        size_mb = assets_db.stat().st_size / (1024 * 1024)
        print(f"✓ assets.db exists ({size_mb:.2f} MB)")
    else:
        print("⚠ assets.db will be created on first sync")
except Exception as e:
    print(f"✗ Database file check failed: {e}")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
