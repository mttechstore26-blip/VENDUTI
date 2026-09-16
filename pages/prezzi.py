import streamlit as st
import pandas as pd

from database import get_connection


st.title("💰 Analisi prezzi")
st.caption("Distribuzione, fasce di prezzo e confronto tra categorie")


@st.cache_data(ttl=60)
def load_data():
    conn = get_connection()

    query = """
        SELECT
            l.id,
            l.title,
            l.price,
            l.detected_sold_at,
            m.name AS category
        FROM listings l
        LEFT JOIN monitorings m
            ON l.monitoring_id = m.id
        WHERE l.detected_sold_at IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def format_price(value):
    if pd.isna(value):
        return "-"

    return (
        f"€ {value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


df = load_data()

if df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()


# ---------------------------------------------------------
# NORMALIZZAZIONE
# ---------------------------------------------------------

df["price"] = pd.to_numeric(
    df["price"],
    errors="coerce",
)

df["detected_sold_at"] = pd.to_datetime(
    df["detected_sold_at"],
    errors="coerce",
    utc=True,
)

df["category"] = (
    df["category"]
    .fillna("Senza categoria")
)

df["title"] = (
    df["title"]
    .fillna("Senza titolo")
)


# Elimina prezzi non validi
df = df[
    df["price"].notna()
    & (df["price"] >= 0)
].copy()


if df.empty:
    st.warning("Nessun prezzo valido disponibile.")
    st.stop()


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

st.subheader("🔎 Filtri")

col1, col2 = st.columns(2)


with col1:
    categorie = sorted(
        df["category"]
        .unique()
        .tolist()
    )

    categoria = st.selectbox(
        "Categoria",
        ["Tutte"] + categorie,
    )


with col2:
    periodo = st.selectbox(
        "Periodo",
        [
            "Tutto",
            "Ultimi 7 giorni",
            "Ultimi 30 giorni",
            "Ultimi 90 giorni",
            "Ultimi 365 giorni",
        ],
    )


filtered = df.copy()


if categoria != "Tutte":
    filtered = filtered[
        filtered["category"] == categoria
    ]


if periodo != "Tutto":

    giorni = {
        "Ultimi 7 giorni": 7,
        "Ultimi 30 giorni": 30,
        "Ultimi 90 giorni": 90,
        "Ultimi 365 giorni": 365,
    }[periodo]

    data_limite = (
        pd.Timestamp.now(tz="UTC")
        - pd.Timedelta(days=giorni)
    )

    filtered = filtered[
        filtered["detected_sold_at"]
        >= data_limite
    ]


if filtered.empty:
    st.info(
        "Nessun annuncio corrisponde ai filtri selezionati."
    )
    st.stop()


# ---------------------------------------------------------
# KPI
# ---------------------------------------------------------

st.divider()

prezzi = filtered["price"]

prezzo_medio = prezzi.mean()
prezzo_mediano = prezzi.median()
prezzo_min = prezzi.min()
prezzo_max = prezzi.max()


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "📊 Prezzo medio",
        format_price(prezzo_medio),
    )


with col2:
    st.metric(
        "💰 Prezzo mediano",
        format_price(prezzo_mediano),
    )


with col3:
    st.metric(
        "⬇️ Prezzo minimo",
        format_price(prezzo_min),
    )


with col4:
    st.metric(
        "⬆️ Prezzo massimo",
        format_price(prezzo_max),
    )


# ---------------------------------------------------------
# FASCE DI PREZZO
# ---------------------------------------------------------

st.divider()

st.subheader("📦 Distribuzione per fascia di prezzo")


def price_band(value):
    if value < 50:
        return "0 - 49 €"

    if value < 100:
        return "50 - 99 €"

    if value < 150:
        return "100 - 149 €"

    if value < 200:
        return "150 - 199 €"

    if value < 300:
        return "200 - 299 €"

    if value < 500:
        return "300 - 499 €"

    if value < 750:
        return "500 - 749 €"

    if value < 1000:
        return "750 - 999 €"

    return "1000 €+"


band_order = [
    "0 - 49 €",
    "50 - 99 €",
    "100 - 149 €",
    "150 - 199 €",
    "200 - 299 €",
    "300 - 499 €",
    "500 - 749 €",
    "750 - 999 €",
    "1000 €+",
]


filtered["Fascia prezzo"] = (
    filtered["price"]
    .apply(price_band)
)


band_stats = (
    filtered
    .groupby("Fascia prezzo")
    .size()
    .reindex(
        band_order,
        fill_value=0,
    )
    .reset_index(name="Annunci")
)


band_stats = band_stats[
    band_stats["Annunci"] > 0
]


st.bar_chart(
    band_stats,
    x="Fascia prezzo",
    y="Annunci",
    width="stretch",
)


# ---------------------------------------------------------
# CONFRONTO CATEGORIE
# ---------------------------------------------------------

st.divider()

st.subheader("🏷️ Prezzi per categoria")


category_prices = (
    filtered
    .groupby("category")
    .agg(
        Annunci=("id", "count"),
        Prezzo_medio=("price", "mean"),
        Prezzo_mediano=("price", "median"),
        Prezzo_min=("price", "min"),
        Prezzo_max=("price", "max"),
    )
    .reset_index()
)


chart_categories = (
    category_prices
    .sort_values(
        "Prezzo_mediano",
        ascending=False,
    )
    .head(15)
)


st.bar_chart(
    chart_categories,
    x="category",
    y="Prezzo_mediano",
    width="stretch",
)


# ---------------------------------------------------------
# FASCIA PIÙ FREQUENTE
# ---------------------------------------------------------

st.divider()

st.subheader("🎯 Fascia di mercato principale")


if not band_stats.empty:

    top_band = (
        band_stats
        .sort_values(
            "Annunci",
            ascending=False,
        )
        .iloc[0]
    )

    percentuale = (
        int(top_band["Annunci"])
        / len(filtered)
        * 100
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "🏆 Fascia più frequente",
            top_band["Fascia prezzo"],
        )

    with col2:
        st.metric(
            "📦 Annunci nella fascia",
            f'{int(top_band["Annunci"])} ({percentuale:.1f}%)',
        )


# ---------------------------------------------------------
# ANNUNCI PIÙ COSTOSI
# ---------------------------------------------------------

st.divider()

st.subheader("💎 Annunci con prezzo più alto")


top_expensive = (
    filtered
    .sort_values(
        "price",
        ascending=False,
    )
    .head(20)
    .copy()
)


top_expensive["Prezzo"] = (
    top_expensive["price"]
    .apply(format_price)
)


top_expensive["Venduto rilevato"] = (
    top_expensive["detected_sold_at"]
    .dt.tz_convert("Europe/Rome")
    .dt.strftime("%d/%m/%Y %H:%M")
    .fillna("-")
)


top_expensive = top_expensive.rename(
    columns={
        "title": "Prodotto",
        "category": "Categoria",
    }
)


st.dataframe(
    top_expensive[
        [
            "Prodotto",
            "Categoria",
            "Prezzo",
            "Venduto rilevato",
        ]
    ],
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------
# TABELLA CATEGORIE
# ---------------------------------------------------------

st.divider()

st.subheader("📋 Dettaglio prezzi per categoria")


table = (
    category_prices
    .sort_values(
        "Annunci",
        ascending=False,
    )
    .copy()
)


table["Prezzo medio"] = (
    table["Prezzo_medio"]
    .apply(format_price)
)

table["Prezzo mediano"] = (
    table["Prezzo_mediano"]
    .apply(format_price)
)

table["Prezzo minimo"] = (
    table["Prezzo_min"]
    .apply(format_price)
)

table["Prezzo massimo"] = (
    table["Prezzo_max"]
    .apply(format_price)
)


table = table.rename(
    columns={
        "category": "Categoria",
    }
)


st.dataframe(
    table[
        [
            "Categoria",
            "Annunci",
            "Prezzo medio",
            "Prezzo mediano",
            "Prezzo minimo",
            "Prezzo massimo",
        ]
    ],
    width="stretch",
    hide_index=True,
    height=600,
)