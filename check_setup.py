#!/usr/bin/env python3
"""
Setup verification script for InVesta.
Checks all modules and dependencies are properly configured.
Includes API functionality tests.
"""

import sys
import importlib
from pathlib import Path
import time


def check_files_exist() -> bool:
    """Check if all required files exist."""
    print("📁 Checking required files...")
    required_files = [
        "config.py",
        "database.py",
        "portfolio.py",
        "ui.py",
        "app.py",
        "main.py",
        "finance.db"
    ]
    
    all_exist = True
    for file in required_files:
        exists = Path(file).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_imports() -> bool:
    """Check if all modules can be imported."""
    print("\n📚 Checking module imports...")
    modules_to_check = [
        ("config", "Configuration module"),
        ("database", "Database module"),
        ("portfolio", "Portfolio module"),
        ("ui", "UI module"),
    ]
    
    all_imported = True
    for module_name, description in modules_to_check:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name} - {description}")
        except ImportError as e:
            print(f"  ❌ {module_name} - {description}")
            print(f"     Error: {e}")
            all_imported = False
    
    return all_imported


def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    dependencies = {
        "streamlit": "Streamlit web framework",
        "pandas": "Data manipulation library",
        "plotly": "Visualization library",
        "yfinance": "Yahoo Finance data fetcher",
        "sqlite3": "SQLite database (built-in)",
    }
    
    all_installed = True
    for package, description in dependencies.items():
        try:
            if package == "sqlite3":
                __import__(package)
            else:
                importlib.import_module(package)
            print(f"  ✅ {package} - {description}")
        except ImportError:
            print(f"  ❌ {package} - {description}")
            all_installed = False
    
    return all_installed


def check_config() -> bool:
    """Check if config module has all required constants."""
    print("\n⚙️  Checking config constants...")
    try:
        import config
        required_constants = [
            "DB_PATH",
            "TABLE_TRANSACTIONS",
            "TABLE_INVESTMENTS",
            "TABLE_TAGS",
            "TRANSACTION_TYPES",
            "TRADE_TYPES",
            "INCOME_CATEGORIES",
            "PAGE_TITLE",
            "PAGE_ICON",
        ]
        
        all_present = True
        for const in required_constants:
            if hasattr(config, const):
                value = getattr(config, const)
                print(f"  ✅ {const} = {repr(value)[:50]}")
            else:
                print(f"  ❌ {const} - MISSING")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"  ❌ Error checking config: {e}")
        return False


def check_database_manager() -> bool:
    """Check if DatabaseManager class is properly defined."""
    print("\n🗄️  Checking DatabaseManager class...")
    try:
        from database import DatabaseManager
        required_methods = [
            "get_conn",
            "init_db",
            "fetch_tags",
            "insert_transaction",
            "insert_investment",
            "insert_tag",
            "delete_record",
            "fetch_transactions",
            "fetch_investments",
        ]
        
        all_present = True
        for method in required_methods:
            if hasattr(DatabaseManager, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - MISSING")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"  ❌ Error checking DatabaseManager: {e}")
        return False


def check_portfolio_analyzer() -> bool:
    """Check if PortfolioAnalyzer class is properly defined."""
    print("\n📊 Checking PortfolioAnalyzer class...")
    try:
        from portfolio import PortfolioAnalyzer
        required_methods = [
            "fetch_latest_price",
            "aggregate_portfolio",
            "compute_metrics",
            "get_portfolio_allocation",
        ]
        
        all_present = True
        for method in required_methods:
            if hasattr(PortfolioAnalyzer, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - MISSING")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"  ❌ Error checking PortfolioAnalyzer: {e}")
        return False


def check_ui_functions() -> bool:
    """Check if UI utility functions are defined."""
    print("\n🎨 Checking UI utility functions...")
    try:
        import ui
        required_functions = [
            "display_metric_cards",
            "display_empty_state",
            "display_confirmation_message",
        ]
        
        all_present = True
        for func in required_functions:
            if hasattr(ui, func) and callable(getattr(ui, func)):
                print(f"  ✅ {func}")
            else:
                print(f"  ❌ {func} - MISSING")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"  ❌ Error checking UI functions: {e}")
        return False


def check_type_hints() -> bool:
    """Check if modules use type hints."""
    print("\n🔍 Checking type hints...")
    modules_with_hints = {
        "database.py": "DatabaseManager class",
        "portfolio.py": "PortfolioAnalyzer class",
        "ui.py": "UI functions",
    }
    
    all_have_hints = True
    for file_name in modules_with_hints.keys():
        with open(file_name, "r") as f:
            content = f.read()
            has_type_hints = "->" in content and ":" in content
            status = "✅" if has_type_hints else "⚠️ "
            print(f"  {status} {file_name}")
            if not has_type_hints:
                all_have_hints = False
    
    return all_have_hints


def check_yfinance_api() -> bool:
    """Check if yfinance API is working properly."""
    print("\n📡 Checking yfinance API connectivity...")
    try:
        import yfinance as yf
        
        # Test with a popular ticker
        test_ticker = "AAPL"
        print(f"  Testing API with ticker: {test_ticker}")
        
        try:
            ticker = yf.Ticker(test_ticker)
            data = ticker.history(period="1d")
            
            if not data.empty:
                latest_price = float(data['Close'].iloc[-1])
                print(f"  ✅ API working - {test_ticker} price: ${latest_price:.2f}")
                return True
            else:
                print(f"  ⚠️  API returned empty data for {test_ticker}")
                return False
        except Exception as e:
            print(f"  ❌ API error: {str(e)}")
            return False
    except Exception as e:
        print(f"  ❌ Error testing yfinance: {e}")
        return False


def check_database_operations() -> bool:
    """Check if database operations work correctly."""
    print("\n💾 Checking database operations...")
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        print(f"  ✅ DatabaseManager initialized")
        
        # Check if database file exists
        if Path("finance.db").exists():
            print(f"  ✅ Database file exists")
        else:
            print(f"  ⚠️  Database file not found")
        
        # Try to fetch data
        try:
            transactions = db.fetch_transactions()
            investments = db.fetch_investments()
            tags = db.fetch_tags()
            print(f"  ✅ Data fetch operations successful")
            print(f"     - Transactions: {len(transactions)}")
            print(f"     - Investments: {len(investments)}")
            print(f"     - Tags: {len(tags)}")
            return True
        except Exception as e:
            print(f"  ❌ Data fetch error: {e}")
            return False
    except Exception as e:
        print(f"  ❌ Error checking database: {e}")
        return False


def check_portfolio_calculations() -> bool:
    """Check if portfolio analysis works correctly."""
    print("\n📈 Checking portfolio calculations...")
    try:
        from database import DatabaseManager
        from portfolio import PortfolioAnalyzer
        import pandas as pd
        
        db = DatabaseManager()
        investments_df = db.fetch_investments()
        transactions_df = db.fetch_transactions()
        
        if investments_df.empty:
            print(f"  ℹ️  No investments in database - skipping calculation test")
            return True
        
        try:
            portfolio_df = PortfolioAnalyzer.aggregate_portfolio(investments_df)
            metrics = PortfolioAnalyzer.compute_metrics(
                transactions_df, 
                investments_df, 
                portfolio_df
            )
            allocation_df = PortfolioAnalyzer.get_portfolio_allocation(portfolio_df)
            
            print(f"  ✅ Portfolio aggregation successful")
            print(f"     - Holdings: {len(portfolio_df)}")
            print(f"     - Metrics: {list(metrics.keys())}")
            print(f"     - Total Assets: ${metrics['Total Assets']:,.2f}")
            return True
        except Exception as e:
            print(f"  ❌ Calculation error: {e}")
            return False
    except Exception as e:
        print(f"  ❌ Error checking portfolio: {e}")
        return False


def main() -> None:
    """Run all checks."""
    print("=" * 60)
    print("🔍 InVesta Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Files", check_files_exist),
        ("Dependencies", check_dependencies),
        ("Module Imports", check_imports),
        ("Config Constants", check_config),
        ("DatabaseManager", check_database_manager),
        ("PortfolioAnalyzer", check_portfolio_analyzer),
        ("UI Functions", check_ui_functions),
        ("Type Hints", check_type_hints),
        ("Database Operations", check_database_operations),
        ("API Connectivity", check_yfinance_api),
        ("Portfolio Calculations", check_portfolio_calculations),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ Error during {check_name} check: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("\n✅ All checks passed! Your setup is complete.")
        print("\n🚀 To run the application:")
        print("   - Using Python: python main.py")
        print("   - Using UV: uv run main.py")
        print("   - Direct Streamlit: streamlit run app.py")
        return 0
    else:
        print("\n⚠️  Some checks failed or were skipped.")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
