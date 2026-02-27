"""
Nasdaq Ticker Synchronization Module
Manages dual-database system with assets.db for public market data
and automated FTP synchronization from nasdaqtrader.com
"""

from typing import List, Dict, Optional, Tuple
import sqlite3
import logging
from datetime import datetime, date
from pathlib import Path
import io
from ftplib import FTP

# Suppress warnings
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

# Database paths
DB_DIR = Path(__file__).parent
ASSETS_DB_PATH = DB_DIR / "assets.db"

# Nasdaq FTP settings
NASDAQ_FTP_HOST = "ftp.nasdaqtrader.com"
NASDAQ_FTP_DIR = "SymbolDirectory"
NASDAQ_LISTED_FILE = "nasdaqlisted.txt"
OTHERLISTED_FILE = "otherlisted.txt"


class TickerSyncManager:
    """Manages ticker data synchronization from Nasdaq."""
    
    def __init__(self, db_path: Path = ASSETS_DB_PATH):
        """Initialize ticker sync manager."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize assets.db with required schema."""
        from contextlib import closing
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable integrity check and repair mode
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()
        if integrity != ("ok",):
            logging.warning(f"Database integrity issue: {integrity}. Attempting recovery...")
        
        # Create tickers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickers (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                is_etf INTEGER NOT NULL DEFAULT 0,
                exchange TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create B-TREE index on symbol for O(1) exact-match lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickers_symbol ON tickers(symbol)
        """)
        
        # Try to handle FTS5 corruption by dropping and recreating if needed
        try:
            # First, try to verify FTS5 table exists
            cursor.execute("SELECT COUNT(*) FROM tickers_search LIMIT 1")
        except Exception as e:
            # FTS5 table is corrupted, drop and recreate
            logging.warning(f"FTS5 table corrupted: {e}. Recreating...")
            try:
                cursor.execute("DROP TABLE IF EXISTS tickers_search")
            except:
                pass
        
        # Create FTS5 virtual table for full-text search
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS tickers_search USING fts5(
                    symbol,
                    name,
                    is_etf,
                    exchange,
                    content=tickers,
                    content_rowid=rowid
                )
            """)
        except Exception as e:
            logging.error(f"Could not create FTS5 table: {e}")
        
        # Create sync_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Rebuild FTS5 index if tickers exist
        try:
            cursor.execute("SELECT COUNT(*) FROM tickers")
            ticker_count = cursor.fetchone()[0]
            if ticker_count > 0:
                try:
                    cursor.execute("DELETE FROM tickers_search")
                    cursor.execute("""
                        INSERT INTO tickers_search(rowid, symbol, name, is_etf, exchange)
                        SELECT rowid, symbol, name, is_etf, exchange FROM tickers
                    """)
                    logging.info(f"Rebuilt FTS5 index with {ticker_count} tickers")
                except Exception as e:
                    logging.warning(f"Could not rebuild FTS5 during init: {e}. Falling back to B-TREE search only.")
        except Exception as e:
            logging.error(f"Error during FTS5 rebuild: {e}")
        
        conn.commit()
        conn.close()
    
    def _get_last_sync_date(self) -> Optional[date]:
        """Get the last sync date from sync_log."""
        try:
            from contextlib import closing
            
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM sync_log WHERE key = 'last_updated_at'"
                )
                result = cursor.fetchone()
                
                if result:
                    return datetime.fromisoformat(result[0]).date()
            return None
        except Exception as e:
            logging.error(f"Error reading sync date: {e}")
            return None
    
    def _set_last_sync_date(self) -> None:
        """Update last sync date in sync_log."""
        try:
            from contextlib import closing
            
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO sync_log (key, value) VALUES (?, ?)",
                    ("last_updated_at", datetime.now().isoformat())
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Error updating sync date: {e}")
    
    def _fetch_nasdaq_file(self, filename: str) -> Optional[str]:
        """
        Fetch a file from Nasdaq FTP server.
        
        Args:
            filename: Name of file to fetch (nasdaqlisted.txt or otherlisted.txt)
        
        Returns:
            File contents as string or None on error
        """
        try:
            ftp = FTP(NASDAQ_FTP_HOST, timeout=10)
            ftp.login()
            
            # Navigate to directory
            ftp.cwd(NASDAQ_FTP_DIR)
            
            # Download file
            file_data = io.BytesIO()
            ftp.retrbinary(f"RETR {filename}", file_data.write)
            ftp.quit()
            
            return file_data.getvalue().decode('utf-8', errors='ignore')
        except Exception as e:
            logging.error(f"Error fetching {filename} from Nasdaq FTP: {e}")
            return None
    
    def _parse_nasdaq_file(
        self, content: str, is_nasdaqlisted: bool = True
    ) -> List[Dict]:
        """
        Parse Nasdaq ticker file.
        
        Args:
            content: File content
            is_nasdaqlisted: True if nasdaqlisted.txt, False if otherlisted.txt
        
        Returns:
            List of ticker dictionaries
        """
        tickers = []
        lines = content.split('\n')
        
        # Skip header and last line (summary)
        header = lines[0] if lines else ""
        data_lines = lines[1:-1] if len(lines) > 2 else []
        
        for line in data_lines:
            if not line.strip() or line.startswith('File'):
                continue
            
            parts = line.split('|')
            if len(parts) < 3:
                continue
            
            symbol = parts[0].strip()
            name = parts[1].strip()
            
            # Skip test issues
            if "Test Issue" in name:
                continue
            
            # Determine if ETF
            is_etf = 0
            if is_nasdaqlisted:
                # nasdaqlisted.txt: ETF column is at index 4
                if len(parts) > 4:
                    is_etf = 1 if parts[4].strip().upper() == 'Y' else 0
            else:
                # otherlisted.txt: ETF column is at index 5
                if len(parts) > 5:
                    is_etf = 1 if parts[5].strip().upper() == 'Y' else 0
            
            # Determine exchange
            exchange = "NASDAQ" if is_nasdaqlisted else "OTHER"
            
            tickers.append({
                "symbol": symbol,
                "name": name,
                "is_etf": is_etf,
                "exchange": exchange,
            })
        
        return tickers
    
    def _insert_tickers(self, tickers: List[Dict]) -> int:
        """
        Insert tickers into database using INSERT OR REPLACE and rebuild FTS5.
        
        Args:
            tickers: List of ticker dictionaries
        
        Returns:
            Number of tickers inserted
        """
        if not tickers:
            logging.warning("No tickers provided to insert")
            return 0
            
        try:
            from contextlib import closing
            
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                
                count = 0
                for ticker in tickers:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO tickers
                            (symbol, name, is_etf, exchange)
                            VALUES (?, ?, ?, ?)
                        """, (
                            ticker["symbol"],
                            ticker["name"],
                            ticker["is_etf"],
                            ticker["exchange"],
                        ))
                        count += 1
                    except Exception as e:
                        logging.error(f"Error inserting ticker: {ticker}: {e}")
                        continue
                
                conn.commit()
                
                # Rebuild FTS5 index for new tickers
                if count > 0:
                    try:
                        cursor.execute("DELETE FROM tickers_search")
                        cursor.execute("""
                            INSERT INTO tickers_search(rowid, symbol, name, is_etf, exchange)
                            SELECT rowid, symbol, name, is_etf, exchange FROM tickers
                        """)
                        conn.commit()
                        logging.info(f"Rebuilt FTS5 index with {count} tickers")
                    except Exception as e:
                        logging.warning(f"Could not rebuild FTS5 index: {e}")
                
                return count
        except Exception as e:
            logging.error(f"Error inserting tickers: {e}")
            return 0
    
    def sync_if_needed(self) -> bool:
        """
        Synchronize ticker data if not done today.
        
        Returns:
            True if sync performed, False if already up to date
        """
        last_sync = self._get_last_sync_date()
        today = date.today()
        
        # If synced today, skip
        if last_sync == today:
            logging.info("Ticker database already synced today")
            return False
        
        logging.info("Starting Nasdaq ticker synchronization...")
        
        # Fetch NASDAQ listed tickers
        nasdaq_content = self._fetch_nasdaq_file(NASDAQ_LISTED_FILE)
        if not nasdaq_content:
            logging.error("Failed to fetch NASDAQ listed file")
            return False
        
        # Fetch other listed tickers
        other_content = self._fetch_nasdaq_file(OTHERLISTED_FILE)
        if not other_content:
            logging.error("Failed to fetch other listed file")
            return False
        
        # Parse files
        nasdaq_tickers = self._parse_nasdaq_file(nasdaq_content, is_nasdaqlisted=True)
        other_tickers = self._parse_nasdaq_file(other_content, is_nasdaqlisted=False)
        
        # Combine and insert
        all_tickers = nasdaq_tickers + other_tickers
        count = self._insert_tickers(all_tickers)
        
        # Update sync timestamp
        self._set_last_sync_date()
        
        logging.info(f"Synchronized {count} tickers from Nasdaq")
        return True
    
    def get_ticker_options(self, search_query: str = "") -> List[str]:
        """
        Get formatted ticker options for selectbox with instant searching.
        Uses B-TREE index for symbol prefix searches and FTS5 for name searches.
        
        Args:
            search_query: Optional filter string
        
        Returns:
            List of formatted ticker strings: "{Symbol} | {Name} ({Type})", sorted by relevance
        """
        try:
            from contextlib import closing
            
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                
                if search_query:
                    # Two-tiered search: Symbol prefix (fast), then Name (broader search)
                    query = search_query.strip().upper()
                    
                    # First: Exact/prefix match on symbol column (uses B-TREE index)
                    # Then: Name contains match (for discovering by company name)
                    cursor.execute("""
                        SELECT symbol, name, is_etf
                        FROM tickers
                        WHERE symbol LIKE ?
                        UNION ALL
                        SELECT symbol, name, is_etf
                        FROM tickers
                        WHERE symbol NOT LIKE ? AND name LIKE ?
                        ORDER BY symbol
                    """, (f"{query}%", f"{query}%", f"%{query}%"))
                else:
                    # Return all tickers sorted by symbol (no LIMIT - all 12K+ available)
                    cursor.execute("""
                        SELECT symbol, name, is_etf
                        FROM tickers
                        ORDER BY symbol
                    """)
                
                results = cursor.fetchall()
            
            options = []
            for row in results:
                symbol = row[0]
                name = row[1]
                is_etf = row[2]
                ticker_type = "ETF" if is_etf else "Stock"
                display = f"{symbol} | {name} ({ticker_type})"
                options.append(display)
            
            return options
        except Exception as e:
            logging.error(f"Error getting ticker options: {e}")
            return []
    
    def get_ticker_from_option(self, option: str) -> Optional[str]:
        """
        Extract ticker symbol from formatted option string.
        
        Args:
            option: Formatted string like "AAPL | Apple Inc. (Stock)"
        
        Returns:
            Ticker symbol or None
        """
        if not option or '|' not in option:
            return None
        
        try:
            symbol = option.split('|')[0].strip()
            return symbol if symbol else None
        except Exception:
            return None
    
    def get_ticker_count(self) -> int:
        """Get total number of tickers in database."""
        try:
            from contextlib import closing
            
            with closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tickers")
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logging.error(f"Error counting tickers: {e}")
            return 0


# Global instance
_sync_manager: Optional[TickerSyncManager] = None


def get_sync_manager() -> TickerSyncManager:
    """Get or create the global ticker sync manager."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = TickerSyncManager()
    return _sync_manager
