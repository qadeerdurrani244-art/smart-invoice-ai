"""
ledger.py
SQLite database: transactions save karna, padhna, delete karna, monthly summary.
Data 'data' folder mein rehta hai (smart-invoice\\data\\ledger.db).
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "ledger.db"


def _connect():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    date      TEXT NOT NULL,
                    vendor    TEXT,
                    amount    REAL NOT NULL,
                    currency  TEXT NOT NULL,
                    type      TEXT NOT NULL,
                    category  TEXT,
                    file_path TEXT,
                    notes     TEXT
                )
                """
            )
    finally:
        conn.close()


def add_transaction(t):
    """t = dict with: date, vendor, amount, currency, type, category, file_path, notes"""
    conn = _connect()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO transactions
                (date, vendor, amount, currency, type, category, file_path, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t["date"],
                    t.get("vendor", ""),
                    float(t["amount"]),
                    t["currency"],
                    t["type"],
                    t.get("category", ""),
                    t.get("file_path", ""),
                    t.get("notes", ""),
                ),
            )
    finally:
        conn.close()


def get_all():
    conn = _connect()
    try:
        return pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY date DESC, id DESC", conn
        )
    finally:
        conn.close()


def delete_transaction(tx_id):
    conn = _connect()
    try:
        with conn:
            conn.execute("DELETE FROM transactions WHERE id = ?", (int(tx_id),))
    finally:
        conn.close()


def monthly_summary(df, currency):
    """Month-wise income, expense, profit (ek currency ke liye)."""
    d = df[df["currency"] == currency].copy()
    if d.empty:
        return pd.DataFrame(columns=["income", "expense", "profit"])
    d["month"] = d["date"].str[:7]
    pivot = d.pivot_table(
        index="month", columns="type", values="amount", aggfunc="sum", fill_value=0
    )
    for col in ("income", "expense"):
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot["profit"] = pivot["income"] - pivot["expense"]
    return pivot[["income", "expense", "profit"]].sort_index()
