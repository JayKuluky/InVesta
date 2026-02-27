"""
Portfolio analysis module for InVesta application.
Provides PortfolioAnalyzer class for portfolio calculations and analysis.
"""

from typing import Optional, Dict, Any
import logging
import pandas as pd
import streamlit as st
import yfinance as yf

# Suppress yfinance and urllib3 warnings
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

from config import (
    TRADE_TYPE_BUY,
    TRADE_TYPE_SELL,
    TRANSACTION_TYPE_INCOME,
    TRANSACTION_TYPE_EXPENSE,
    YFINANCE_CACHE_TTL,
    CURRENCY_SYMBOL,
    PRICE_PRECISION,
    PERCENTAGE_PRECISION,
)


class PortfolioAnalyzer:
    """Analyzes investment portfolio and calculates financial metrics."""

    @staticmethod
    @st.cache_data(ttl=YFINANCE_CACHE_TTL, show_spinner=False)
    def fetch_latest_price(ticker: str) -> Optional[float]:
        """Fetch the latest price for a given ticker."""
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
            else:
                return None
        except Exception:
            # Silently return None for invalid tickers
            return None

    @staticmethod
    def aggregate_portfolio(investments_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate investment data into portfolio summary."""
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
                ]
            )

        grouped = investments_df.groupby("ticker")
        summary = []

        for ticker, group in grouped:
            buys = group[group["trade_type"] == TRADE_TYPE_BUY]
            sells = group[group["trade_type"] == TRADE_TYPE_SELL]

            total_bought = buys["shares"].sum()
            total_sold = sells["shares"].sum()
            net_shares = total_bought - total_sold

            # Skip closed positions
            if net_shares <= 0:
                continue

            # Calculate average cost
            invested = (buys["shares"] * buys["price"]).sum() - (
                sells["shares"] * sells["price"]
            ).sum()
            avg_cost = invested / net_shares if net_shares else 0

            # Fetch current price
            latest_price = PortfolioAnalyzer.fetch_latest_price(ticker)
            if latest_price is None:
                latest_price = avg_cost  # Fallback to average cost

            # Calculate current value and P&L
            current_value = net_shares * latest_price
            unrealized_pnl = current_value - (net_shares * avg_cost)
            unrealized_pct = (
                (unrealized_pnl / (net_shares * avg_cost) * 100) if avg_cost else 0
            )

            summary.append(
                {
                    "Ticker": ticker,
                    "Total Shares": net_shares,
                    "Avg Cost": round(avg_cost, PRICE_PRECISION),
                    "Current Price": round(latest_price, PRICE_PRECISION),
                    "Current Value": round(current_value, PRICE_PRECISION),
                    "Unrealized P&L": round(unrealized_pnl, PRICE_PRECISION),
                    "Unrealized P&L (%)": round(unrealized_pct, PERCENTAGE_PRECISION),
                }
            )

        return pd.DataFrame(summary)

    @staticmethod
    def compute_metrics(
        transactions_df: pd.DataFrame,
        investments_df: pd.DataFrame,
        portfolio_df: pd.DataFrame,
    ) -> Dict[str, float]:
        """Compute key financial metrics."""
        # Calculate cash balance
        total_income = transactions_df[
            transactions_df["type"] == TRANSACTION_TYPE_INCOME
        ]["amount"].sum()
        total_expense = transactions_df[
            transactions_df["type"] == TRANSACTION_TYPE_EXPENSE
        ]["amount"].sum()

        buys = investments_df[investments_df["trade_type"] == TRADE_TYPE_BUY]
        sells = investments_df[investments_df["trade_type"] == TRADE_TYPE_SELL]

        invested_principal = (buys["shares"] * buys["price"]).sum()
        cash_from_sales = (sells["shares"] * sells["price"]).sum()

        cash_balance = (
            total_income - total_expense - invested_principal + cash_from_sales
        )

        # Calculate investment metrics
        current_invest_value = portfolio_df["Current Value"].sum()
        total_assets = cash_balance + current_invest_value
        total_unrealized_pnl = portfolio_df["Unrealized P&L"].sum()

        return {
            "Total Assets": round(total_assets, PRICE_PRECISION),
            "Cash Balance": round(cash_balance, PRICE_PRECISION),
            "Current Invest Value": round(current_invest_value, PRICE_PRECISION),
            "Total Unrealized P&L": round(total_unrealized_pnl, PRICE_PRECISION),
        }

    @staticmethod
    def get_portfolio_allocation(portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """Get portfolio allocation data for visualization."""
        if portfolio_df.empty:
            return pd.DataFrame(columns=["Ticker", "Value"])

        return portfolio_df[["Ticker", "Current Value"]].rename(
            columns={"Current Value": "Value"}
        )
