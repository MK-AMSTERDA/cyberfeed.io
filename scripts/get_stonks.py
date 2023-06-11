import requests
import sqlite3
import os


def get_db_connection():
    conn = sqlite3.connect("/app/rss.db")
    conn.row_factory = sqlite3.Row
    return conn


tickers = ["NDAQ", "VTI", "SPY", "AAPL", "JAMF", "CIBR"]
FINNHUB_SECRET = os.environ["FINNHUB_SECRET"]

with get_db_connection() as conn:
    cur = conn.cursor()

    for stock_name in tickers:
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": stock_name, "token": FINNHUB_SECRET}
        stock_info = requests.get(url, params=params).json()
        percentage = round(stock_info["dp"], 2)

        if percentage < 0:
            status = "red"
        elif percentage > 0:
            status = "green"
        else:
            status = "black"

        cur.execute(
            "UPDATE stocks SET percentage=?, status=? WHERE ticker=?",
            [percentage, status, stock_name],
        )
        conn.commit()
