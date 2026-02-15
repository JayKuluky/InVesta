# app.py

import os
import sqlite3
from contextlib import closing
from datetime import date
import pandas as pd
import streamlit as st
import plotly.express as px
import yfinance as yf

DB_PATH = "finance.db"

# --- DB Initialization ---
def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        # Transactions Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                type TEXT CHECK(type IN ('Income', 'Expense')),
                amount REAL,
                category TEXT,
                tag TEXT,
                note TEXT
            )
        """)
        # Investments Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                trade_type TEXT CHECK(trade_type IN ('Buy', 'Sell')),
                shares REAL,
                price REAL,
                note TEXT
            )
        """)
        # Tags Table
        c.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        conn.commit()

init_db()

# --- Helper Functions ---

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def fetch_tags():
    with closing(get_conn()) as conn:
        df = pd.read_sql("SELECT name FROM tags ORDER BY name", conn)
    return df['name'].tolist()

def insert_transaction(date, type_, amount, category, tag, note):
    with closing(get_conn()) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO transactions (date, type, amount, category, tag, note) VALUES (?, ?, ?, ?, ?, ?)",
            (date, type_, amount, category, tag, note)
        )
        conn.commit()

def insert_investment(date, ticker, trade_type, shares, price, note):
    with closing(get_conn()) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO investments (date, ticker, trade_type, shares, price, note) VALUES (?, ?, ?, ?, ?, ?)",
            (date, ticker.upper(), trade_type, shares, price, note)
        )
        conn.commit()

def insert_tag(name):
    with closing(get_conn()) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO tags (name) VALUES (?)", (name,))
            conn.commit()
            return True, None
        except sqlite3.IntegrityError as e:
            return False, str(e)

def delete_record(table, record_id):
    with closing(get_conn()) as conn:
        c = conn.cursor()
        c.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        conn.commit()

def fetch_transactions():
    with closing(get_conn()) as conn:
        return pd.read_sql("SELECT * FROM transactions ORDER BY date DESC, id DESC", conn)

def fetch_investments():
    with closing(get_conn()) as conn:
        return pd.read_sql("SELECT * FROM investments ORDER BY date DESC, id DESC", conn)

# --- yfinance Price Fetcher with Exception Handling ---
@st.cache_data(ttl=300, show_spinner=False)
def fetch_latest_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        else:
            raise ValueError("No data")
    except Exception:
        return None  # Will fallback to avg cost

# --- Portfolio Aggregation ---
def aggregate_portfolio(investments_df):
    if investments_df.empty:
        return pd.DataFrame(columns=[
            "Ticker", "Total Shares", "Avg Cost", "Current Price", "Current Value", "Unrealized P&L", "Unrealized P&L (%)"
        ])
    grouped = investments_df.groupby(['ticker'])
    summary = []
    for ticker, group in grouped:
        buys = group[group['trade_type'] == 'Buy']
        sells = group[group['trade_type'] == 'Sell']
        total_bought = buys['shares'].sum()
        total_sold = sells['shares'].sum()
        net_shares = total_bought - total_sold
        if net_shares <= 0:
            continue  # Don't show closed positions
        invested = (buys['shares'] * buys['price']).sum() - (sells['shares'] * sells['price']).sum()
        avg_cost = invested / net_shares if net_shares else 0
        latest_price = fetch_latest_price(ticker)
        if latest_price is None:
            latest_price = avg_cost  # Fallback
        current_value = net_shares * latest_price
        unrealized_pnl = current_value - (net_shares * avg_cost)
        unrealized_pct = (unrealized_pnl / (net_shares * avg_cost) * 100) if avg_cost else 0
        summary.append({
            "Ticker": ticker,
            "Total Shares": net_shares,
            "Avg Cost": round(avg_cost, 2),
            "Current Price": round(latest_price, 2),
            "Current Value": round(current_value, 2),
            "Unrealized P&L": round(unrealized_pnl, 2),
            "Unrealized P&L (%)": round(unrealized_pct, 2)
        })
    return pd.DataFrame(summary)

# --- Financial Calculations ---
def compute_metrics(transactions_df, investments_df, portfolio_df):
    # 1. Cash Balance
    total_income = transactions_df[transactions_df['type'] == 'Income']['amount'].sum()
    total_expense = transactions_df[transactions_df['type'] == 'Expense']['amount'].sum()
    buys = investments_df[investments_df['trade_type'] == 'Buy']
    sells = investments_df[investments_df['trade_type'] == 'Sell']
    invested_principal = (buys['shares'] * buys['price']).sum()
    cash_from_sales = (sells['shares'] * sells['price']).sum()
    cash_balance = total_income - total_expense - invested_principal + cash_from_sales

    # 2. Current Invest Value
    current_invest_value = portfolio_df['Current Value'].sum()

    # 3. Total Assets
    total_assets = cash_balance + current_invest_value

    # 4. Total Unrealized P&L
    total_unrealized_pnl = portfolio_df['Unrealized P&L'].sum()

    return {
        "Total Assets": round(total_assets, 2),
        "Cash Balance": round(cash_balance, 2),
        "Current Invest Value": round(current_invest_value, 2),
        "Total Unrealized P&L": round(total_unrealized_pnl, 2)
    }

def get_portfolio_allocation(portfolio_df):
    if portfolio_df.empty:
        return pd.DataFrame(columns=["Ticker", "Value"])
    return portfolio_df[["Ticker", "Current Value"]].rename(columns={"Current Value": "Value"})

# --- Streamlit UI ---
st.set_page_config(page_title="Personal Finance & Portfolio Dashboard", layout="wide")
st.title("💹 Personal Finance & Portfolio Dashboard")

# --- Load Data ---
transactions_df = fetch_transactions()
investments_df = fetch_investments()
portfolio_df = aggregate_portfolio(investments_df)
metrics = compute_metrics(transactions_df, investments_df, portfolio_df)
allocation_df = get_portfolio_allocation(portfolio_df)

# --- Metrics Cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Assets", f"${metrics['Total Assets']:,}")
col2.metric("Cash Balance", f"${metrics['Cash Balance']:,}")
col3.metric("Current Invest Value", f"${metrics['Current Invest Value']:,}")
col4.metric("Total Unrealized P&L", f"${metrics['Total Unrealized P&L']:,}")

# --- Portfolio Allocation Pie Chart ---
if not allocation_df.empty and allocation_df['Value'].sum() > 0:
    fig = px.pie(allocation_df, names="Ticker", values="Value", title="Portfolio Allocation")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active investments to display allocation.")

# --- Main Tabs ---
tabs = st.tabs(["💰 Income & Expense", "📈 Investment", "⚙️ Tag Settings", "📝 History Management"])

# --- Tab 1: Income & Expense ---
with tabs[0]:
    st.header("Income & Expense Entry")
    col_inc, col_exp = st.columns(2)
    with col_inc:
        st.subheader("Add Income")
        with st.form("income_form", clear_on_submit=True):
            inc_cat = st.selectbox("Category", ["Regular Salary", "One-time Income", "Passive Income"])
            inc_amt = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
            inc_date = st.date_input("Date", value=date.today())
            inc_note = st.text_input("Note (optional)")
            submitted = st.form_submit_button("Add Income")
            if submitted:
                insert_transaction(str(inc_date), "Income", inc_amt, inc_cat, None, inc_note)
                st.success("Income recorded. Please refresh to update metrics.")

    with col_exp:
        st.subheader("Add Expense")
        tags = fetch_tags()
        with st.form("expense_form", clear_on_submit=True):
            exp_tag = st.selectbox("Tag", tags) if tags else st.warning("No tags found. Add tags in Tag Settings.")
            exp_amt = st.number_input("Amount ", min_value=0.01, step=0.01, format="%.2f", key="exp_amt")
            exp_date = st.date_input("Date ", value=date.today(), key="exp_date")
            exp_note = st.text_input("Note (optional)", key="exp_note")
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                if tags:
                    insert_transaction(str(exp_date), "Expense", exp_amt, None, exp_tag, exp_note)
                    st.success("Expense recorded. Please refresh to update metrics.")

# --- Tab 2: Investment ---
with tabs[1]:
    st.header("Investment Trades & Portfolio")
    with st.form("investment_form", clear_on_submit=True):
        trade_type = st.selectbox("Trade Type", ["Buy", "Sell"])
        ticker = st.text_input("Ticker (e.g., AAPL, URNM)").upper()
        shares = st.number_input("Shares", min_value=0.0001, step=0.0001, format="%.4f")
        price = st.number_input("Execution Price", min_value=0.01, step=0.01, format="%.2f")
        inv_date = st.date_input("Date", value=date.today(), key="inv_date")
        inv_note = st.text_input("Note (optional)", key="inv_note")
        submitted = st.form_submit_button("Record Trade")
        if submitted:
            if ticker:
                insert_investment(str(inv_date), ticker, trade_type, shares, price, inv_note)
                st.success("Trade recorded. Please refresh to update portfolio.")

    st.subheader("Current Portfolio")
    if not portfolio_df.empty:
        st.dataframe(portfolio_df, width='stretch')
    else:
        st.info("No active holdings.")

# --- Tab 3: Tag Settings ---
with tabs[2]:
    st.header("Manage Tags")
    with st.form("tag_form", clear_on_submit=True):
        tag_name = st.text_input("New Tag Name")
        submitted = st.form_submit_button("Add Tag")
        if submitted:
            if tag_name.strip():
                ok, err = insert_tag(tag_name.strip())
                if ok:
                    st.success("Tag added. Please refresh to update tag list.")
                else:
                    st.error(f"Failed to add tag: {err}")
            else:
                st.warning("Tag name cannot be empty.")
    st.subheader("Existing Tags")
    tags = fetch_tags()
    if tags:
        st.write(", ".join(tags))
    else:
        st.info("No tags found.")

# --- Tab 4: History Management ---
with tabs[3]:
    st.header("History Management")
    st.subheader("Transactions")
    st.dataframe(transactions_df, width='stretch')
    st.subheader("Investments")
    st.dataframe(investments_df, width='stretch')

    st.markdown("---")
    st.subheader("Delete Record")
    del_col1, del_col2 = st.columns(2)
    with del_col1:
        del_table = st.selectbox("Table", ["transactions", "investments"])
    with del_col2:
        del_id = st.number_input("Record ID", min_value=1, step=1)
    if st.button("Delete Record"):
        delete_record(del_table, int(del_id))
        st.success("Record deleted. Please refresh to update all metrics and tables.")

# --- End of app.py ---