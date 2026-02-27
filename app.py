"""
Main Streamlit application for InVesta.
Investment Portfolio Management Dashboard.
"""

from datetime import date
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd

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
from finance_logic import PortfolioCalculator, BatchPriceFetcher
from ticker_data import (
    search_tickers,
    get_stock_stats_summary,
    get_historical_data,
    initialize_ticker_sync,
    get_formatted_ticker_options,
    get_ticker_from_option,
    batch_fetch_prices,
    DEFAULT_TICKER
)
from ui import display_metric_cards, display_empty_state, display_confirmation_message


@st.cache_resource
def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    return DatabaseManager()


@st.cache_resource
def init_ticker_sync():
    """Initialize ticker synchronization with Nasdaq FTP."""
    with st.spinner("🔄 Synchronizing ticker database..."):
        return initialize_ticker_sync()
    return None


def get_available_tickers(investments_df) -> list:
    """Get list of unique tickers from database."""
    if investments_df.empty:
        return []
    return sorted(investments_df['ticker'].unique().tolist())


def format_portfolio_with_links(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """
    Format portfolio dataframe with Yahoo Finance links for tickers.
    
    Args:
        portfolio_df: Portfolio dataframe
    
    Returns:
        Formatted dataframe with clickable ticker links
    """
    if portfolio_df.empty:
        return portfolio_df
    
    # Create a copy to avoid modifying original
    df = portfolio_df.copy()
    
    # Add Yahoo Finance links for ticker column
    if 'Ticker' in df.columns:
        df['Ticker'] = df['Ticker'].apply(
            lambda ticker: f"https://finance.yahoo.com/quote/{ticker}"
        )
    
    return df


def format_investments_with_links(investments_df: pd.DataFrame) -> pd.DataFrame:
    """
    Format investments dataframe with Yahoo Finance links for tickers.
    
    Args:
        investments_df: Investments dataframe
    
    Returns:
        Formatted dataframe with clickable ticker links
    """
    if investments_df.empty:
        return investments_df
    
    # Create a copy to avoid modifying original
    df = investments_df.copy()
    
    # Add Yahoo Finance links for ticker column
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].apply(
            lambda ticker: f"https://finance.yahoo.com/quote/{ticker}"
        )
    
    return df


def display_live_prices(portfolio_df: object) -> None:
    """Display real-time stock prices with scrollable container and expandable details."""
    if portfolio_df.empty:
        return
    
    st.subheader("📊 Live Stock Prices")
    
    # Fixed-height scrollable container for price list
    with st.container(height=500, border=True):
        for idx, row in portfolio_df.iterrows():
            ticker = row['Ticker']
            current_price = row['Current Price']
            avg_cost = row['Avg Cost']
            change = current_price - avg_cost
            change_pct = (change / avg_cost * 100) if avg_cost > 0 else 0
            
            color = "green" if change >= 0 else "red"
            symbol = "📈" if change >= 0 else "📉"
            yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"
            
            # Always visible: Core metrics (ticker as clickable link, price, P&L)
            st.markdown(
                f"[{symbol} **{ticker}**]({yahoo_link}) | Current: ${current_price:.2f} | "
                f"Avg Cost: ${avg_cost:.2f} | "
                f"<span style='color:{color}'>Change: {change:+.2f} ({change_pct:+.2f}%)</span>",
                unsafe_allow_html=True
            )
            
            # Expandable section: Extended stats and chart
            with st.expander(f"📊 View Details & Chart - {ticker}"):
                # Display extended stock statistics with smaller font
                stats = get_stock_stats_summary(ticker)
                if stats:
                    st.markdown("**Stock Statistics:**")
                    stats_cols = st.columns(4)
                    with stats_cols[0]:
                        st.markdown(f"<div style='font-size: 0.85em; text-align: center;'><b>Open</b><br>${stats.get('open', 0):.2f}</div>", unsafe_allow_html=True)
                    with stats_cols[1]:
                        st.markdown(f"<div style='font-size: 0.85em; text-align: center;'><b>High</b><br>${stats.get('high', 0):.2f}</div>", unsafe_allow_html=True)
                    with stats_cols[2]:
                        st.markdown(f"<div style='font-size: 0.85em; text-align: center;'><b>Low</b><br>${stats.get('low', 0):.2f}</div>", unsafe_allow_html=True)
                    with stats_cols[3]:
                        st.markdown(f"<div style='font-size: 0.85em; text-align: center;'><b>Volume</b><br>{stats.get('volume', 0):,.0f}</div>", unsafe_allow_html=True)
                    st.divider()
                
                    # Timeframe selector (collapsed label for compact layout)
                    chart_timeframe = st.radio(
                        f"Timeframe for {ticker}",
                        ["1D", "1W", "1M", "1Y"],
                        horizontal=True,
                        key=f"timeframe_{ticker}",
                        label_visibility="collapsed"
                    )
                    
                    # Fetch and display price chart
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
                        # Optimized layout for compact expander display
                        fig.update_layout(
                            title=f"{ticker} - {chart_timeframe}",
                            xaxis_title="",
                            yaxis_title="Price ($)",
                            hovermode='x unified',
                            height=250,
                            margin=dict(l=0, r=0, t=30, b=0)
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
        if st.button("✅ Confirm & Save", width='stretch'):
            st.session_state.trade_confirmed = True
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", width='stretch'):
            st.session_state.trade_confirmed = False
            st.rerun()


@st.dialog("�️ Delete Transaction")
def show_delete_confirmation(ticker: str, trade_type: str, shares: float, price: float, row_id: int, index: int, db_ref) -> None:
    """Show delete transaction confirmation dialog."""
    st.error(f"⚠️ Are you sure you want to delete this transaction?")
    
    st.write(f"**{trade_type}** {shares} shares of **{ticker}** @ ${price:.2f}")
    
    st.divider()
    
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ Confirm Delete", width='stretch', key=f"confirm_delete_dialog_{index}_{row_id}"):
            try:
                # Delete from database
                conn = db_ref.get_conn()
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {TABLE_INVESTMENTS} WHERE id = ?", (row_id,))
                conn.commit()
                conn.close()
                
                display_confirmation_message("✅ Transaction deleted successfully!")
                st.session_state[f"confirm_delete_{index}"] = False
                st.rerun()
            except Exception as e:
                display_confirmation_message(f"❌ Error: {str(e)}", "error")
                st.session_state[f"confirm_delete_{index}"] = False
    
    with col_cancel:
        if st.button("❌ Cancel", width='stretch', key=f"cancel_delete_dialog_{index}_{row_id}"):
            st.session_state[f"confirm_delete_{index}"] = False
            st.rerun()


@st.dialog("�🚨 Clear All Data")
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
        if st.button("🔴 Yes, Delete Everything", width='stretch'):
            st.session_state.clear_confirmed = True
            st.rerun()
    with col2:
        if st.button("🔵 Cancel", width='stretch'):
            st.session_state.clear_confirmed = False
            st.rerun()


def main() -> None:
    """Main Streamlit application."""
    # Page Configuration
    st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT, page_icon=PAGE_ICON)
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")

    # Initialize ticker synchronization (Nasdaq FTP sync)
    init_ticker_sync()

    # Initialize database manager
    db = get_db_manager()

    # Load Data
    transactions_df = db.fetch_transactions()
    investments_df = db.fetch_investments()
    
    # Fetch current prices using batch fetcher for performance
    ticker_prices = {}
    if not investments_df.empty:
        tickers = investments_df['ticker'].unique().tolist()
        ticker_prices = batch_fetch_prices(tickers)
    
    # Use PortfolioCalculator for portfolio aggregation with realized P&L
    portfolio_df = PortfolioCalculator.aggregate_portfolio(investments_df, ticker_prices)
    metrics = PortfolioCalculator.compute_metrics(
        transactions_df, investments_df, portfolio_df, ticker_prices
    )
    allocation_df = PortfolioCalculator.get_portfolio_allocation(portfolio_df)

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
        
        # Step 2: Ticker Selection from Nasdaq Database
        with col2:
            # Get formatted ticker options from Nasdaq database
            ticker_options = get_formatted_ticker_options()
            # Add empty placeholder as first option (no prefill)
            ticker_options_with_placeholder = [""] + ticker_options
            
            ticker_display = st.selectbox(
                "Select Ticker (Nasdaq Database)",
                ticker_options_with_placeholder,
                index=0,
                key="ticker_select",
                help="Select from 100,000+ tickers in Nasdaq database"
            )
            
            # Extract ticker symbol from display format (only if something is selected)
            ticker_input = get_ticker_from_option(ticker_display) if ticker_display else None
        
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
        
        # Check if trade was confirmed in dialog (must be checked FIRST, before form)
        if st.session_state.get('trade_confirmed', False):
            trade_data = st.session_state.get('pending_trade', {})
            if trade_data:
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
        
        # Show form for new trades
        # Confirm button (requires ticker selection)
        if ticker_input and shares > 0 and price > 0:
            if st.button("✅ Confirm Trade", width='stretch'):
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
        elif not ticker_input:
            st.warning("⚠️ Please select a ticker to proceed")
        elif shares <= 0 or price <= 0:
            st.warning("⚠️ Shares and price must be greater than 0")
        
        st.divider()
        st.subheader("📊 Current Portfolio")
        if not portfolio_df.empty:
            # Display portfolio with plain ticker symbols (no links)
            st.dataframe(
                portfolio_df,
                width='stretch',
                column_config={
                    "Ticker": st.column_config.TextColumn(
                        label="Ticker",
                        help="Stock symbol"
                    )
                }
            )
        else:
            display_empty_state("No active holdings yet.")

    # --- Tab 2: History ---
    with tabs[1]:
        st.header("Investment History")
        
        if not investments_df.empty:
            st.subheader("All Transactions")
            
            # Display transactions with delete option
            for idx, row in investments_df.iterrows():
                col_info, col_delete = st.columns([5, 1])
                
                with col_info:
                    # Display transaction info
                    ticker_link = f"https://finance.yahoo.com/quote/{row['ticker']}"
                    trade_icon = "🟢" if row['trade_type'] == "Buy" else "🔴"
                    st.markdown(
                        f"{trade_icon} [{row['ticker']}]({ticker_link}) | "
                        f"{row['trade_type']} {row['shares']} @ ${row['price']:.2f} | "
                        f"Date: {row['date']}",
                        unsafe_allow_html=True
                    )
                    if row['note']:
                        st.caption(f"📝 {row['note']}")
                
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_btn_{idx}_{row['id']}", help="Delete this transaction"):
                        st.session_state[f"confirm_delete_{idx}"] = True
            
            # Check for delete confirmations and show dialog
            for idx, row in investments_df.iterrows():
                if st.session_state.get(f"confirm_delete_{idx}", False):
                    show_delete_confirmation(
                        ticker=row['ticker'],
                        trade_type=row['trade_type'],
                        shares=row['shares'],
                        price=row['price'],
                        row_id=row['id'],
                        index=idx,
                        db_ref=db
                    )
                    st.session_state[f"confirm_delete_{idx}"] = False
            
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