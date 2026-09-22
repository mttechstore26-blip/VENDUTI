import pandas as pd
import streamlit as st

from database import get_connection


@st.cache_data(ttl=60, show_spinner=False)
def load_market_data():
    """Carica e normalizza una sola volta i dati usati da tutta la webapp."""
    conn = get_connection()

    query = """
        SELECT
            l.id,
            l.external_id,
            l.title,
            l.url,
            l.price,
            l.posted_at,
            l.detected_sold_at,
            l.imported_at,
            l.transaction_status,
            m.name AS category
        FROM listings l
        LEFT JOIN monitorings m
            ON l.monitoring_id = m.id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return df

    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    df["posted_at"] = pd.to_datetime(
        df["posted_at"],
        errors="coerce",
    )
    df["posted_at"] = (
        df["posted_at"]
        .dt.tz_localize(
            "Europe/Rome",
            ambiguous="NaT",
            nonexistent="NaT",
        )
        .dt.tz_convert("UTC")
    )

    df["detected_sold_at"] = pd.to_datetime(
        df["detected_sold_at"],
        errors="coerce",
        utc=True,
    )

    df["imported_at"] = pd.to_datetime(
        df["imported_at"],
        errors="coerce",
        utc=True,
    )

    df["category"] = df["category"].fillna("Senza categoria")
    df["title"] = df["title"].fillna("Senza titolo")

    df["reference_date"] = df["detected_sold_at"].fillna(df["posted_at"])

    df["sale_time_hours"] = (
        df["detected_sold_at"] - df["posted_at"]
    ).dt.total_seconds() / 3600

    df.loc[df["sale_time_hours"] < 0, "sale_time_hours"] = pd.NA

    return df
