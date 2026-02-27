"""
Database operations module for InVesta application.
Provides DatabaseManager class for all database interactions.
"""

import sqlite3
from contextlib import closing
from typing import List, Tuple, Optional
import pandas as pd

from config import (
    DB_PATH,
    TABLE_TRANSACTIONS,
    TABLE_INVESTMENTS,
    TABLE_TAGS,
    TRANSACTION_TYPES,
    TRADE_TYPES,
)


class DatabaseManager:
    """Manages all database operations for InVesta."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """
        Initialize DatabaseManager.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.init_db()

    def get_conn(self) -> sqlite3.Connection:
        """
        Get a database connection.

        Returns:
            sqlite3.Connection: Database connection object.
        """
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self) -> None:
        """Initialize database tables if they don't exist."""
        with closing(self.get_conn()) as conn:
            c = conn.cursor()

            # Transactions Table
            c.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_TRANSACTIONS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    category TEXT,
                    tag TEXT,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Investments Table
            c.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_INVESTMENTS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    trade_type TEXT NOT NULL CHECK(trade_type IN ('Buy', 'Sell')),
                    shares REAL NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Tags Table
            c.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_TAGS} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            # Add currency column for existing tables (if it doesn't exist)
            try:
                c.execute(f"ALTER TABLE {TABLE_TRANSACTIONS} ADD COLUMN currency TEXT DEFAULT 'USD'")
            except sqlite3.OperationalError:
                pass
            
            try:
                c.execute(f"ALTER TABLE {TABLE_INVESTMENTS} ADD COLUMN currency TEXT DEFAULT 'USD'")
            except sqlite3.OperationalError:
                pass

            conn.commit()

    def fetch_tags(self) -> List[str]:
        """Fetch all tags from the database."""
        with closing(self.get_conn()) as conn:
            df = pd.read_sql(f"SELECT name FROM {TABLE_TAGS} ORDER BY name", conn)
        return df["name"].tolist()

    def insert_transaction(
        self,
        date: str,
        transaction_type: str,
        amount: float,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        note: Optional[str] = None,
        currency: str = "USD",
    ) -> bool:
        """Insert a new transaction."""
        try:
            with closing(self.get_conn()) as conn:
                c = conn.cursor()
                c.execute(
                    f"""
                    INSERT INTO {TABLE_TRANSACTIONS} 
                    (date, type, amount, currency, category, tag, note) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (date, transaction_type, amount, currency, category, tag, note),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting transaction: {e}")
            return False

    def insert_investment(
        self,
        date: str,
        ticker: str,
        trade_type: str,
        shares: float,
        price: float,
        note: Optional[str] = None,
        currency: str = "USD",
    ) -> bool:
        """Insert a new investment trade."""
        try:
            with closing(self.get_conn()) as conn:
                c = conn.cursor()
                c.execute(
                    f"""
                    INSERT INTO {TABLE_INVESTMENTS} 
                    (date, ticker, trade_type, shares, price, currency, note) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (date, ticker.upper(), trade_type, shares, price, currency, note),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting investment: {e}")
            return False

    def insert_tag(self, name: str) -> Tuple[bool, Optional[str]]:
        """Insert a new tag."""
        with closing(self.get_conn()) as conn:
            c = conn.cursor()
            try:
                c.execute(f"INSERT INTO {TABLE_TAGS} (name) VALUES (?)", (name,))
                conn.commit()
                return True, None
            except sqlite3.IntegrityError as e:
                return False, str(e)
            except sqlite3.Error as e:
                return False, str(e)

    def delete_record(self, table: str, record_id: int) -> bool:
        """Delete a record from the database."""
        try:
            with closing(self.get_conn()) as conn:
                c = conn.cursor()
                c.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting record: {e}")
            return False

    def fetch_transactions(self) -> pd.DataFrame:
        """Fetch all transactions ordered by date descending."""
        with closing(self.get_conn()) as conn:
            return pd.read_sql(
                f"SELECT * FROM {TABLE_TRANSACTIONS} ORDER BY date DESC, id DESC",
                conn,
            )

    def fetch_investments(self) -> pd.DataFrame:
        """Fetch all investments ordered by date descending."""
        with closing(self.get_conn()) as conn:
            return pd.read_sql(
                f"SELECT * FROM {TABLE_INVESTMENTS} ORDER BY date DESC, id DESC",
                conn,
            )

    def export_table_to_csv(self, table_name: str) -> bytes:
        """
        Export a database table to CSV format as bytes.
        
        Args:
            table_name: Name of the table to export
        
        Returns:
            CSV data as UTF-8 encoded bytes
        """
        try:
            with closing(self.get_conn()) as conn:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                return df.to_csv(index=False).encode('utf-8')
        except Exception as e:
            print(f"Error exporting table {table_name}: {e}")
            return b""
