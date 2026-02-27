"""
Configuration and constants for InVesta application.
"""

# Database Configuration
DB_PATH = "finance.db"

# Table Names
TABLE_TRANSACTIONS = "transactions"
TABLE_INVESTMENTS = "investments"
TABLE_TAGS = "tags"

# Transaction Types
TRANSACTION_TYPE_INCOME = "Income"
TRANSACTION_TYPE_EXPENSE = "Expense"
TRANSACTION_TYPES = (TRANSACTION_TYPE_INCOME, TRANSACTION_TYPE_EXPENSE)

# Investment Trade Types
TRADE_TYPE_BUY = "Buy"
TRADE_TYPE_SELL = "Sell"
TRADE_TYPES = (TRADE_TYPE_BUY, TRADE_TYPE_SELL)

# Income Categories
INCOME_CATEGORIES = [
    "Regular Salary",
    "One-time Income",
    "Passive Income"
]

# Cache Settings
YFINANCE_CACHE_TTL = 60  # 1 minute for high-frequency updates

# UI Settings
PAGE_TITLE = "Personal Finance & Portfolio Dashboard"
PAGE_ICON = "💹"
PAGE_LAYOUT = "wide"

# Default Values
DEFAULT_CURRENCY = "USD"
CURRENCY_SYMBOL = "$"

# Precision Settings
PRICE_PRECISION = 2
SHARES_PRECISION = 4
PERCENTAGE_PRECISION = 2
