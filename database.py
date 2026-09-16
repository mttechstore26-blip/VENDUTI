import sqlite3
from pathlib import Path


DB_PATH = Path("/opt/mt-tech-telegram/data/market.db")


def get_connection():
    conn = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True,
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")

    return conn
