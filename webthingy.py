"""
Automated Web Data Tracker & Dashboard
Tracks a product's price, stores history in SQLite,
provides a dashboard, and sends alerts when price drops.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import smtplib
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------
# CONFIGURATION
# ------------------------
DB_FILE = "prices.db"
PRODUCT_URL = "https://example.com/product"
CSS_SELECTOR = ".price"   # Update to match target site
ALERT_PRICE = 50.00

EMAIL_USER = os.getenv("EMAIL_USER")      # e.g., your Gmail address
EMAIL_PASS = os.getenv("EMAIL_PASS")      # app-specific password
EMAIL_TO = os.getenv("EMAIL_TO")          # recipient address

# ------------------------
# DATABASE FUNCTIONS
# ------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            date TEXT,
            price REAL
        )
    """)
    conn.commit()
    conn.close()

def save_price(price: float):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO prices VALUES (?, ?)", (datetime.now().isoformat(), price))
    conn.commit()
    conn.close()

def get_price_history():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM prices", conn)
    conn.close()
    return df

# ------------------------
# SCRAPER FUNCTION
# ------------------------
def get_price():
    """Scrapes the product page and returns the price as a float."""
    r = requests.get(PRODUCT_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    element = soup.select_one(CSS_SELECTOR)
    if not element:
        raise ValueError("Price element not found. Check CSS_SELECTOR.")
    price_text = element.text.strip().replace("$", "").replace(",", "")
    return float(price_text)

# ------------------------
# ALERT FUNCTION
# ------------------------
def send_alert(price: float):
    """Send an email alert if the price drops below threshold."""
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("Email credentials not set. Skipping alert.")
        return

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        message = (
            f"Subject: Price Alert!\n\n"
            f"The price is now ${price}.\n"
            f"Link: {PRODUCT_URL}"
        )
        server.sendmail(EMAIL_USER, EMAIL_TO, message)
    print(f"Alert sent: Price ${price}")

# ------------------------
# DASHBOARD
# ------------------------
def run_dashboard():
    st.title("📊 Price Tracker Dashboard")
    df = get_price_history()
    if df.empty:
        st.warning("No price data yet. Run the tracker first.")
        return

    fig = px.line(df, x="date", y="price", title="Price History Over Time")
    st.plotly_chart(fig)
    st.write("Latest Price:", df.iloc[-1]["price"])
    st.write("Total Records:", len(df))

# ------------------------
# MAIN SCRIPT
# ------------------------
def run_tracker():
    init_db()
    try:
        price = get_price()
        save_price(price)
        print(f"[{datetime.now().isoformat()}] Price recorded: ${price}")
        if price <= ALERT_PRICE:
            send_alert(price)
    except Exception as e:
        print(f"Error tracking price: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        run_dashboard()
    else:
        run_tracker()
