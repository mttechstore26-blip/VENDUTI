import streamlit as st
import pandas as pd

from database import get_connection


st.title("🏷️ Categorie")
st.caption("Confronto delle performance di vendita per categoria")


@st.cache_data(ttl=60)
def load_data():
    conn = get_connection()

    query = """
        SELECT
            l.id,
            l.title,
            l.price,
            l.posted_at,
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


def format_duration(hours):
    if pd.isna(hours):
        return "-"

    total_minutes = int(hours * 60)

    days = total_minutes // (24 * 60)
    remaining_minutes = total_minutes % (24 * 60)

    h = remaining_minutes // 60
    minutes = remaining_minutes % 60

    if days > 0:
        return f"{days}g {h}h"

    if h > 0:
        return f"{h}h {minutes}m"

    return f"{minutes}m"


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

df["category"] = (
    df["category"]
    .fillna("Senza categoria")
)


# ---------------------------------------------------------
# TEMPO DI VENDITA
# ---------------------------------------------------------

df["sale_time_hours"] = (
    df["detected_sold_at"]
    - df["posted_at"]
).dt.total_seconds() / 3600


df.loc[
    df["sale_time_hours"] < 0,
    "sale_time_hours",
] = pd.NA


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

st.subheader("🔎 Filtri")

col1, col2 = st.columns(2)


with col1:
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


with col2:
    minimo_annunci = st.number_input(
        "Minimo annunci per categoria",
        min_value=1,
        value=1,
        step=1,
    )


filtered = df.copy()


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
    st.info("Nessun dato disponibile per il periodo selezionato.")
    st.stop()


# ---------------------------------------------------------
# STATISTICHE PER CATEGORIA
# ---------------------------------------------------------

stats = (
    filtered
    .groupby("category")
    .agg(
        Annunci=("id", "count"),
        Prezzo_medio=("price", "mean"),
        Prezzo_mediano=("price", "median"),
        Prezzo_min=("price", "min"),
        Prezzo_max=("price", "max"),
        Tempo_medio_ore=("sale_time_hours", "mean"),
        Tempo_mediano_ore=("sale_time_hours", "median"),
    )
    .reset_index()
)


stats = stats[
    stats["Annunci"] >= minimo_annunci
].copy()


if stats.empty:
    st.info(
        "Nessuna categoria soddisfa i filtri selezionati."
    )
    st.stop()


# ---------------------------------------------------------
# KPI
# ---------------------------------------------------------

st.divider()

categoria_top = (
    stats
    .sort_values(
        "Annunci",
        ascending=False,
    )
    .iloc[0]
)


valid_speed = (
    stats[
        stats["Tempo_mediano_ore"].notna()
    ]
    .copy()
)


if not valid_speed.empty:
    categoria_piu_veloce = (
        valid_speed
        .sort_values(
            "Tempo_mediano_ore",
            ascending=True,
        )
        .iloc[0]
    )
else:
    categoria_piu_veloce = None


valid_price = (
    stats[
        stats["Prezzo_mediano"].notna()
    ]
    .copy()
)


if not valid_price.empty:
    categoria_piu_costosa = (
        valid_price
        .sort_values(
            "Prezzo_mediano",
            ascending=False,
        )
        .iloc[0]
    )
else:
    categoria_piu_costosa = None


col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "🏆 Categoria con più venduti",
        categoria_top["category"],
        f'{int(categoria_top["Annunci"])} annunci',
    )


with col2:
    if categoria_piu_veloce is not None:
        st.metric(
            "⚡ Categoria più veloce",
            categoria_piu_veloce["category"],
            format_duration(
                categoria_piu_veloce["Tempo_mediano_ore"]
            ),
        )
    else:
        st.metric(
            "⚡ Categoria più veloce",
            "-",
        )


with col3:
    if categoria_piu_costosa is not None:
        st.metric(
            "💰 Prezzo mediano più alto",
            categoria_piu_costosa["category"],
            format_price(
                categoria_piu_costosa["Prezzo_mediano"]
            ),
        )
    else:
        st.metric(
            "💰 Prezzo mediano più alto",
            "-",
        )


# ---------------------------------------------------------
# GRAFICI
# ---------------------------------------------------------

st.divider()

col_grafico1, col_grafico2 = st.columns(2)


with col_grafico1:

    st.subheader("📦 Venduti per categoria")

    chart_annunci = (
        stats
        .sort_values(
            "Annunci",
            ascending=False,
        )
        .head(15)
    )

    st.bar_chart(
        chart_annunci,
        x="category",
        y="Annunci",
        width="stretch",
    )


with col_grafico2:

    st.subheader("⏱️ Tempo mediano di vendita")

    chart_speed = (
        stats[
            stats["Tempo_mediano_ore"].notna()
        ]
        .sort_values(
            "Tempo_mediano_ore",
            ascending=True,
        )
        .head(15)
    )

    if not chart_speed.empty:
        st.bar_chart(
            chart_speed,
            x="category",
            y="Tempo_mediano_ore",
            width="stretch",
        )
    else:
        st.info(
            "Tempo di vendita non disponibile."
        )


# ---------------------------------------------------------
# PREZZI PER CATEGORIA
# ---------------------------------------------------------

st.divider()

st.subheader("💰 Prezzo mediano per categoria")


chart_price = (
    stats[
        stats["Prezzo_mediano"].notna()
    ]
    .sort_values(
        "Prezzo_mediano",
        ascending=False,
    )
    .head(15)
)


if not chart_price.empty:
    st.bar_chart(
        chart_price,
        x="category",
        y="Prezzo_mediano",
        width="stretch",
    )
else:
    st.info(
        "Prezzi non disponibili."
    )


# ---------------------------------------------------------
# TABELLA COMPLETA
# ---------------------------------------------------------

st.divider()

st.subheader("📋 Analisi dettagliata")


table = (
    stats
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

table["Tempo medio vendita"] = (
    table["Tempo_medio_ore"]
    .apply(format_duration)
)

table["Tempo mediano vendita"] = (
    table["Tempo_mediano_ore"]
    .apply(format_duration)
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
            "Tempo medio vendita",
            "Tempo mediano vendita",
        ]
    ],
    width="stretch",
    hide_index=True,
    height=650,
)