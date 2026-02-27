"""
Finance Logic Module for InVesta
Handles portfolio aggregation, P&L calculations, and metrics
with support for realized P&L tracking
"""

from typing import Optional, Dict, Any, List
import logging
import pandas as pd
from datetime import datetime

from config import TRADE_TYPE_BUY, TRADE_TYPE_SELL

logging.getLogger('yfinance').setLevel(logging.ERROR)


class PortfolioCalculator:
    """Improved portfolio analysis with realized P&L support."""
    
    @staticmethod
    def aggregate_portfolio(
        investments_df: pd.DataFrame,
        ticker_prices: Dict[str, float],
    ) -> pd.DataFrame:
        """
        Aggregate investment data into portfolio summary with realized P&L.
        
        Args:
            investments_df: DataFrame with investment records
            ticker_prices: Dictionary of {ticker: current_price}
        
        Returns:
            DataFrame with portfolio summary including realized P&L
        """
        if investments_df.empty:
            return pd.DataFrame(
                columns=[
                    "Ticker",
                    "Total Shares",
                    "Avg Cost",
                    "Current Price",
                    "Current Value",
                    "Unrealized P&L",
                    "Unrealized P&L (%)",
                    "Realized P&L",
                    "Total P&L",
                ]
            )
        
        grouped = investments_df.groupby("ticker")
        summary = []
        
        for ticker, group in grouped:
            buys = group[group["trade_type"] == TRADE_TYPE_BUY]
            sells = group[group["trade_type"] == TRADE_TYPE_SELL]
            
            # Calculate aggregates
            buy_shares = buys["shares"].sum() if not buys.empty else 0
            buy_value = (buys["shares"] * buys["price"]).sum() if not buys.empty else 0
            
            sell_shares = sells["shares"].sum() if not sells.empty else 0
            sell_value = (sells["shares"] * sells["price"]).sum() if not sells.empty else 0
            
            net_shares = buy_shares - sell_shares
            avg_cost = (buy_value / buy_shares) if buy_shares > 0 else 0
            
            # Current price (fallback to average cost if unavailable)
            current_price = ticker_prices.get(ticker, avg_cost)
            
            # Calculate realized P&L (when position is closed or partially closed)
            realized_pnl = sell_value - (sell_shares * avg_cost) if sell_shares > 0 else 0
            
            # If position is closed (net_shares == 0), all P&L is realized
            if net_shares == 0 and buy_shares > 0:
                realized_pnl = sell_value - buy_value
                unrealized_pnl = 0
                unrealized_pct = 0
                current_value = 0
            else:
                # Unrealized P&L for remaining position
                current_value = net_shares * current_price
                unrealized_pnl = current_value - (net_shares * avg_cost)
                unrealized_pct = (unrealized_pnl / (net_shares * avg_cost) * 100) if (net_shares * avg_cost) > 0 else 0
            
            total_pnl = unrealized_pnl + realized_pnl
            
            summary.append({
                "Ticker": ticker,
                "Total Shares": int(buy_shares),
                "Sold Shares": int(sell_shares),
                "Net Shares": int(net_shares),
                "Avg Cost": avg_cost,
                "Current Price": current_price,
                "Current Value": current_value,
                "Unrealized P&L": unrealized_pnl,
                "Unrealized P&L (%)": unrealized_pct,
                "Realized P&L": realized_pnl,
                "Total P&L": total_pnl,
                "Status": "🔴 Closed" if net_shares == 0 else "🟢 Open",
            })
        
        df = pd.DataFrame(summary)
        
        # Sort by current value descending
        if not df.empty:
            df = df.sort_values("Current Value", ascending=False)
        
        return df
    
    @staticmethod
    def compute_metrics(
        transactions_df: pd.DataFrame,
        investments_df: pd.DataFrame,
        portfolio_df: pd.DataFrame,
        ticker_prices: Dict[str, float] = None,
    ) -> Dict[str, float]:
        """
        Compute key portfolio metrics.
        
        Args:
            transactions_df: DataFrame with transaction records
            investments_df: DataFrame with investment records
            portfolio_df: DataFrame with aggregated portfolio
            ticker_prices: Optional dictionary of current prices
        
        Returns:
            Dictionary with portfolio metrics
        """
        if ticker_prices is None:
            ticker_prices = {}
        
        # Total assets (current portfolio value)
        total_assets = float(portfolio_df["Current Value"].sum()) if not portfolio_df.empty else 0.0
        
        # Cash balance (from transactions if available)
        cash_balance = 0.0
        if not transactions_df.empty:
            cash_transactions = transactions_df.get("amount", pd.Series(dtype=float))
            cash_balance = float(cash_transactions.sum()) if not cash_transactions.empty else 0.0
        
        # Total P&L (both realized and unrealized)
        total_unrealized_pnl = float(portfolio_df["Unrealized P&L"].sum()) if not portfolio_df.empty else 0.0
        total_realized_pnl = float(portfolio_df["Realized P&L"].sum()) if not portfolio_df.empty else 0.0
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        # Cost basis (total amount invested)
        cost_basis = 0.0
        if not investments_df.empty:
            buys = investments_df[investments_df["trade_type"] == TRADE_TYPE_BUY]
            cost_basis = float((buys["shares"] * buys["price"]).sum()) if not buys.empty else 0.0
        
        # Return percentage
        return_pct = (total_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
        
        return {
            "total_assets": total_assets,
            "cash_balance": cash_balance,
            "cost_basis": cost_basis,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "total_pnl": total_pnl,
            "return_pct": return_pct,
            "portfolio_value": total_assets + cash_balance,
        }
    
    @staticmethod
    def get_portfolio_allocation(portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get portfolio allocation for pie chart.
        
        Args:
            portfolio_df: Aggregated portfolio DataFrame
        
        Returns:
            DataFrame with ticker and value columns
        """
        if portfolio_df.empty:
            return pd.DataFrame(columns=["Ticker", "Value"])
        
        # Filter to only open positions (net_shares > 0)
        open_positions = portfolio_df[portfolio_df["Net Shares"] > 0].copy()
        
        if open_positions.empty:
            return pd.DataFrame(columns=["Ticker", "Value"])
        
        allocation = open_positions[["Ticker", "Current Value"]].copy()
        allocation.columns = ["Ticker", "Value"]
        allocation = allocation[allocation["Value"] > 0]
        
        return allocation.sort_values("Value", ascending=False)
    
    @staticmethod
    def get_closed_positions(portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get list of closed positions with their realized P&L.
        
        Args:
            portfolio_df: Aggregated portfolio DataFrame
        
        Returns:
            DataFrame with closed positions and P&L details
        """
        if portfolio_df.empty:
            return pd.DataFrame()
        
        closed = portfolio_df[portfolio_df["Net Shares"] == 0].copy()
        if closed.empty:
            return pd.DataFrame()
        
        return closed[["Ticker", "Realized P&L", "Total Shares", "Avg Cost", "Status"]].sort_values(
            "Realized P&L",
            ascending=False
        )


class BatchPriceFetcher:
    """Handles batch price fetching and caching."""
    
    @staticmethod
    def fetch_missing_prices(
        tickers: List[str],
        current_prices: Dict[str, float],
        ticker_data_module,
    ) -> Dict[str, float]:
        """
        Fetch missing ticker prices in batch.
        
        Args:
            tickers: List of tickers to fetch
            current_prices: Dictionary of already-cached prices
            ticker_data_module: Reference to ticker_data module with batch_fetch_prices
        
        Returns:
            Updated dictionary with all prices
        """
        missing = [t for t in tickers if t not in current_prices]
        
        if missing:
            try:
                new_prices = ticker_data_module.batch_fetch_prices(missing)
                current_prices.update(new_prices)
            except Exception as e:
                logging.error(f"Error fetching prices for {missing}: {e}")
        
        return current_prices
