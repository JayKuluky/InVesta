"""
Main Streamlit application for InVesta.
Investment Portfolio Management Dashboard.
"""

from datetime import date
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

from config import (
    PAGE_TITLE,
    PAGE_ICON,
    PAGE_LAYOUT,
    TRADE_TYPES,
    TABLE_INVESTMENTS,
    TABLE_TAGS,
)
from database import DatabaseManager
from portfolio import PortfolioAnalyzer
from ticker_data import search_tickers, get_stock_stats_summary, get_historical_data, DEFAULT_TICKER
from ui import display_metric_cards, display_empty_state, display_confirmation_message


@st.cache_resource
def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    return DatabaseManager()


def get_available_tickers(investments_df) -> list:
    """Get list of unique tickers from database."""
    if investments_df.empty:
        return []
    return sorted(investments_df['ticker'].unique().tolist())


def display_live_prices(portfolio_df: object) -> None:
    """Display real-time stock prices with expanded details."""
    if portfolio_df.empty:
        return
    
    st.subheader("📊 Live Stock Prices")
    for idx, row in portfolio_df.iterrows():
        ticker = row['Ticker']
        current_price = row['Current Price']
        avg_cost = row['Avg Cost']
        change = current_price - avg_cost
        change_pct = (change / avg_cost * 100) if avg_cost > 0 else 0
        
        # Get stock stats
        stats = get_stock_stats_summary(ticker)
        
        color = "green" if change >= 0 else "red"
        symbol = "📈" if change >= 0 else "📉"
        
        # Display basic info
        st.markdown(
            f"{symbol} **{ticker}** | Current: ${current_price:.2f} | "
            f"Avg Cost: ${avg_cost:.2f} | "
            f"<span style='color:{color}'>Change: {change:+.2f} ({change_pct:+.2f}%)</span>",
            unsafe_allow_html=True
        )
        
        # Display additional stats if available
        if stats:
            stats_text = (
                f"📊 Open: ${stats.get('open', 0):.2f} | "
                f"High: ${stats.get('high', 0):.2f} | "
                f"Low: ${stats.get('low', 0):.2f} | "
                f"Vol: {stats.get('volume', 0):,.0f}"
            )
            st.caption(stats_text)
        
        # Chart display button
        if st.button(f"📈 Show Chart - {ticker}", key=f"chart_{ticker}"):
            st.session_state[f"show_chart_{ticker}"] = not st.session_state.get(f"show_chart_{ticker}", False)
        
        # Display chart if selected
        if st.session_state.get(f"show_chart_{ticker}", False):
            chart_timeframe = st.radio(
                f"Select timeframe for {ticker}",
                ["1D", "1W", "1M", "1Y"],
                horizontal=True,
                key=f"timeframe_{ticker}"
            )
            
            period_map = {"1D": "1d", "1W": "5d", "1M": "1mo", "1Y": "1y"}
            hist_data = get_historical_data(ticker, period_map[chart_timeframe])
            
            if hist_data is not None and not hist_data.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=hist_data['Close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(color='#1f77b4', width=2)
                ))
                fig.update_layout(
                    title=f"{ticker} Stock Price - {chart_timeframe}",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning(f"Could not retrieve chart data for {ticker}")
        
        st.divider()


@st.dialog("📋 Confirm Trade")
def show_trade_confirmation(trade_data: dict) -> None:
    """Show trade confirmation dialog."""
    st.subheader("Trade Summary")
    
    # Display summary
    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.write(f"**Trade Type:** {trade_data.get('trade_type', 'N/A')}")
        st.write(f"**Ticker:** {trade_data.get('ticker', 'N/A')}")
        st.write(f"**Shares:** {trade_data.get('shares', 0):,}")
    with summary_cols[1]:
        st.write(f"**Price per Share:** ${trade_data.get('price', 0):.2f}")
        st.write(f"**Total Value:** ${trade_data.get('shares', 0) * trade_data.get('price', 0):,.2f}")
        st.write(f"**Date:** {trade_data.get('date', 'N/A')}")
    
    if trade_data.get('note'):
        st.write(f"**Note:** {trade_data['note']}")
    
    st.divider()
    
    # Confirmation buttons
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ Confirm & Save", use_container_width=True):
            st.session_state.trade_confirmed = True
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.trade_confirmed = False
            st.rerun()


@st.dialog("🚨 Clear All Data")
def show_clear_confirmation() -> None:
    """Show double confirmation for clearing all data."""
    st.error("⚠️ WARNING: This action cannot be undone!")
    st.write("You are about to permanently delete ALL records:")
    st.write("- All investment trades")
    st.write("- All transactions")
    st.write("- All tags")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Yes, Delete Everything", use_container_width=True):
            st.session_state.clear_confirmed = True
            st.rerun()
    with col2:
        if st.button("🔵 Cancel", use_container_width=True):
            st.session_state.clear_confirmed = False
            st.rerun()


def main() -> None:
    """Main Streamlit application."""
    # Page Configuration
    st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT, page_icon=PAGE_ICON)
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")

    # Initialize database manager
    db = get_db_manager()

    # Load Data
    transactions_df = db.fetch_transactions()
    investments_df = db.fetch_investments()
    portfolio_df = PortfolioAnalyzer.aggregate_portfolio(investments_df)
    metrics = PortfolioAnalyzer.compute_metrics(
        transactions_df, investments_df, portfolio_df
    )
    allocation_df = PortfolioAnalyzer.get_portfolio_allocation(portfolio_df)

    # Display Metrics Cards
    display_metric_cards(metrics)

    # Portfolio Allocation & Live Prices Section
    if not allocation_df.empty and allocation_df["Value"].sum() > 0:
        col_chart, col_prices = st.columns(2)
        
        with col_chart:
            fig = px.pie(
                allocation_df,
                names="Ticker",
                values="Value",
                title="Portfolio Allocation",
            )
            st.plotly_chart(fig, width='stretch')
        
        with col_prices:
            display_live_prices(portfolio_df)
    else:
        display_empty_state("No active investments to display.")

    # Main Tabs
    tabs = st.tabs(
        [
            "📈 Investment",
            "📊 History",
            "⚙️ Settings",
        ]
    )

    # --- Tab 1: Investment ---
    with tabs[0]:
        st.header("Record Investment Trade")
        
        # Initialize session state
        if 'trade_data' not in st.session_state:
            st.session_state.trade_data = {}
        
        # Step 1: Trade Type
        col1, col2 = st.columns(2)
        with col1:
            trade_type = st.selectbox(
                "Select Trade Type",
                TRADE_TYPES,
                key="trade_type_select"
            )
        
        # Step 2: Ticker Search
        with col2:
            ticker_search = st.text_input(
                "Search Ticker (e.g., NVDA, AAPL)",
                placeholder="Leave empty for AAPL...",
                key="ticker_search"
            )
            
            # Get ticker suggestions
            if ticker_search:
                matching_tickers = search_tickers(ticker_search, limit=10)
                ticker_input = st.selectbox(
                    "Select ticker",
                    matching_tickers,
                    key="ticker_select",
                    label_visibility="collapsed"
                )
            else:
                # Auto-select AAPL if no input
                matching_tickers = search_tickers("AAPL", limit=1)
                ticker_input = matching_tickers[0] if matching_tickers else DEFAULT_TICKER
                st.caption(f"Default ticker: **{ticker_input}**")
        
        st.divider()
        
        # Input fields
        col3, col4, col5 = st.columns(3)
        
        with col3:
            shares = st.number_input(
                "Number of Shares",
                min_value=1,
                step=1,
                value=st.session_state.trade_data.get('shares', 1),
                key="shares_input"
            )
        
        with col4:
            price = st.number_input(
                "Execution Price ($)",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                value=st.session_state.trade_data.get('price', 0.01),
                key="price_input"
            )
        
        with col5:
            trade_date = st.date_input(
                "Trade Date",
                value=date.today(),
                key="trade_date_input"
            )
        
        st.divider()
        
        # Trade note
        note = st.text_area(
            "Trade Note (optional)",
            height=50,
            placeholder="Add any notes about this trade...",
            key="trade_note"
        )
        
        st.divider()
        
        # Confirm button (always enabled now, ticker has auto-default)
        if shares > 0 and price > 0:
            if st.button("✅ Confirm Trade", use_container_width=True):
                # Prepare trade data for confirmation dialog
                trade_data = {
                    "trade_type": trade_type,
                    "ticker": ticker_input,
                    "shares": shares,
                    "price": price,
                    "date": trade_date,
                    "note": note
                }
                st.session_state.pending_trade = trade_data
                show_trade_confirmation(trade_data)
            
            # Check if trade was confirmed
            if st.session_state.get('trade_confirmed', False):
                trade_data = st.session_state.get('pending_trade', {})
                success = db.insert_investment(
                    str(trade_data['date']),
                    trade_data['ticker'],
                    trade_data['trade_type'],
                    trade_data['shares'],
                    trade_data['price'],
                    trade_data.get('note') if trade_data.get('note') else None
                )
                if success:
                    display_confirmation_message("✅ Trade recorded successfully!")
                    st.session_state.trade_data = {}
                    st.session_state.trade_confirmed = False
                    st.session_state.pending_trade = {}
                    st.rerun()
                else:
                    display_confirmation_message("❌ Failed to record trade.", "error")
                    st.session_state.trade_confirmed = False
        
        st.divider()
        st.subheader("📊 Current Portfolio")
        if not portfolio_df.empty:
            st.dataframe(portfolio_df, width='stretch')
        else:
            display_empty_state("No active holdings yet.")

    # --- Tab 2: History ---
    with tabs[1]:
        st.header("Investment History")
        
        if not investments_df.empty:
            st.subheader("All Transactions")
            st.dataframe(investments_df, width='stretch')
            
            # Statistics
            st.divider()
            st.subheader("Statistics")
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            total_trades = len(investments_df)
            buy_trades = len(investments_df[investments_df['trade_type'] == 'Buy'])
            sell_trades = len(investments_df[investments_df['trade_type'] == 'Sell'])
            
            with col_stats1:
                st.metric("Total Trades", total_trades)
            with col_stats2:
                st.metric("Buy Orders", buy_trades)
            with col_stats3:
                st.metric("Sell Orders", sell_trades)
        else:
            display_empty_state("No investment history yet.")

    # --- Tab 3: Settings ---
    with tabs[2]:
        st.header("Settings")
        
        st.subheader("🔧 General Settings")
        st.write("Settings for application configuration.")
        
        st.divider()
        
        st.subheader("⚠️ Advanced Settings")
        
        with st.expander("Advanced Options"):
            cols = st.columns(2)
            
            with cols[0]:
                st.warning("⚠️ Warning: These actions cannot be undone!")
                
            with cols[1]:
                if st.button("Clear All Data", help="Permanently delete all records"):
                    show_clear_confirmation()
            
            # Check if clear was confirmed
            if st.session_state.get('clear_confirmed', False):
                try:
                    # Delete all investments, transactions and tags
                    conn = db.get_conn()
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {TABLE_INVESTMENTS}")
                    cursor.execute("DELETE FROM transactions")
                    cursor.execute(f"DELETE FROM {TABLE_TAGS}")
                    conn.commit()
                    conn.close()
                    
                    display_confirmation_message(
                        "✅ All data has been deleted.",
                        "success"
                    )
                    st.session_state.clear_confirmed = False
                    st.rerun()
                except Exception as e:
                    display_confirmation_message(
                        f"❌ Error: {str(e)}", "error"
                    )
                    st.session_state.clear_confirmed = False


if __name__ == "__main__":
    main()