import streamlit as st
import pandas as pd
from data_cache import load_market_data


# ---------------------------------------------------------
# TITOLO
# ---------------------------------------------------------

st.markdown(
    """
    <div class="mt-hero">
        <div class="mt-hero-top">
            <div>
                <div class="mt-hero-title">📊 MT TECH Market Intelligence</div>
                <div class="mt-hero-subtitle">Controllo rapido di vendite, prezzi e velocità di mercato</div>
            </div>
            <div class="mt-live"><span class="mt-live-dot"></span> Monitor attivo</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATI CONDIVISI E GIÀ NORMALIZZATI
# ---------------------------------------------------------

df = load_market_data().copy()

if df.empty:
    st.warning("Nessun annuncio presente nel database.")
    st.stop()


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

st.subheader("🔎 Filtri")

col_search, col_categoria, col_periodo = st.columns(
    [2, 1, 1]
)


with col_search:
    ricerca = st.text_input(
        "Cerca prodotto",
        placeholder="Es. iPhone 15 Pro, Nintendo Switch, Dyson...",
    )


with col_categoria:
    categorie = sorted(
        df["category"]
        .dropna()
        .unique()
        .tolist()
    )

    categoria = st.selectbox(
        "Categoria",
        ["Tutte"] + categorie,
    )


with col_periodo:
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


# Ricerca prodotto
if ricerca:
    filtered = filtered[
        filtered["title"]
        .fillna("")
        .str.contains(
            ricerca,
            case=False,
            regex=False,
        )
    ]


# Categoria
if categoria != "Tutte":
    filtered = filtered[
        filtered["category"] == categoria
    ]


# Periodo
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
        filtered["reference_date"] >= data_limite
    ]


# ---------------------------------------------------------
# NESSUN RISULTATO
# ---------------------------------------------------------

if filtered.empty:
    st.info(
        "Nessun annuncio corrisponde ai filtri selezionati."
    )
    st.stop()


# ---------------------------------------------------------
# KPI
# ---------------------------------------------------------

st.divider()

totale = len(filtered)

prezzi = (
    filtered["price"]
    .dropna()
)

prezzo_medio = (
    prezzi.mean()
    if not prezzi.empty
    else 0
)

prezzo_mediano = (
    prezzi.median()
    if not prezzi.empty
    else 0
)

tempi_vendita = (
    filtered["sale_time_hours"]
    .dropna()
)

tempo_medio_ore = (
    tempi_vendita.mean()
    if not tempi_vendita.empty
    else None
)


def format_euro(value):
    return (
        f"€ {value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def format_tempo(hours):
    if hours is None or pd.isna(hours):
        return "-"

    if hours < 24:
        return f"{hours:.1f} ore"

    giorni = hours / 24

    if giorni < 30:
        return f"{giorni:.1f} giorni"

    mesi = giorni / 30
    return f"{mesi:.1f} mesi"


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "📦 Annunci venduti",
        f"{totale:,}".replace(",", "."),
    )


with col2:
    st.metric(
        "💰 Prezzo medio",
        format_euro(prezzo_medio),
    )


with col3:
    st.metric(
        "📊 Prezzo mediano",
        format_euro(prezzo_mediano),
    )


with col4:
    st.metric(
        "⏱️ Tempo medio vendita",
        format_tempo(tempo_medio_ore),
    )


# ---------------------------------------------------------
# ULTIMI ANNUNCI VENDUTI
# ---------------------------------------------------------

st.subheader("🕒 Ultimi annunci venduti")

ultimi_venduti = (
    filtered[
        filtered["detected_sold_at"].notna()
    ]
    .sort_values(
        "detected_sold_at",
        ascending=False,
    )
    .head(10)
)

if ultimi_venduti.empty:
    st.info("Nessun annuncio venduto disponibile.")
else:
    ultimi_rows = []

    for _, row in ultimi_venduti.iterrows():
        titolo = str(row["title"])
        url = row["url"]

        if pd.notna(url) and url:
            prodotto = (
                f'<a href="{url}" target="_blank">'
                f'{titolo}</a>'
            )
        else:
            prodotto = titolo

        prezzo = (
            format_euro(row["price"])
            if pd.notna(row["price"])
            else "-"
        )

        venduto = (
            row["detected_sold_at"]
            .tz_convert("Europe/Rome")
            .strftime("%d/%m/%Y %H:%M")
            if pd.notna(row["detected_sold_at"])
            else "-"
        )

        tempo = (
            format_tempo(row["sale_time_hours"])
            if pd.notna(row["sale_time_hours"])
            else "-"
        )

        ultimi_rows.append(
            {
                "Prodotto": prodotto,
                "Prezzo": prezzo,
                "Venduto in": tempo,
                "Venduto": venduto,
            }
        )

    ultimi_table = pd.DataFrame(ultimi_rows)

    ultimi_html = ultimi_table.to_html(
        escape=False,
        index=False,
    )

    st.markdown(
        """
        <style>
        .ultimi-venduti-table table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        .ultimi-venduti-table th,
        .ultimi-venduti-table td {
            padding: 9px 10px;
            border-bottom: 1px solid rgba(128,128,128,0.25);
            text-align: left;
            vertical-align: middle;
        }

        .ultimi-venduti-table th {
            font-weight: 700;
        }

        .ultimi-venduti-table a {
            font-weight: 600;
            text-decoration: none;
        }

        .ultimi-venduti-table a:hover {
            text-decoration: underline;
        }

        @media (max-width: 700px) {
            .ultimi-venduti-table {
                overflow-x: auto;
            }

            .ultimi-venduti-table table {
                min-width: 650px;
                font-size: 13px;
            }

            .ultimi-venduti-table th,
            .ultimi-venduti-table td {
                padding: 8px;
                white-space: nowrap;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="ultimi-venduti-table">{ultimi_html}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# ANDAMENTO VENDITE
# ---------------------------------------------------------

st.divider()

st.subheader("📈 Andamento vendite")

trend_df = (
    filtered[
        filtered["reference_date"].notna()
    ]
    .copy()
)

if not trend_df.empty:

    trend_df["Giorno"] = (
        trend_df["reference_date"]
        .dt.floor("D")
        .dt.tz_localize(None)
    )

    trend_giornaliero = (
        trend_df
        .groupby("Giorno")
        .size()
        .reset_index(name="Annunci venduti")
        .sort_values("Giorno")
    )

    st.line_chart(
        trend_giornaliero,
        x="Giorno",
        y="Annunci venduti",
        width="stretch",
    )

else:
    st.info(
        "Non ci sono abbastanza dati per mostrare il trend."
    )


# ---------------------------------------------------------
# GRAFICI PRINCIPALI
# ---------------------------------------------------------

st.divider()

col_grafico1, col_grafico2 = st.columns(2)


# CATEGORIE
with col_grafico1:

    st.subheader("🏷️ Venduti per categoria")

    categorie_df = (
        filtered
        .groupby("category")
        .size()
        .reset_index(name="Annunci")
        .sort_values(
            "Annunci",
            ascending=False,
        )
        .head(15)
    )

    st.bar_chart(
        categorie_df,
        x="category",
        y="Annunci",
        width="stretch",
    )


# PREZZI
with col_grafico2:

    st.subheader("💰 Distribuzione prezzi")

    prezzi_df = (
        filtered[["price"]]
        .dropna()
        .copy()
    )

    if not prezzi_df.empty:

        prezzi_df["fascia"] = (
            prezzi_df["price"] // 50
        ) * 50

        distribuzione = (
            prezzi_df
            .groupby("fascia")
            .size()
            .reset_index(name="Annunci")
            .sort_values("fascia")
        )

        distribuzione["Fascia prezzo"] = (
            distribuzione["fascia"]
            .apply(
                lambda x:
                f"€ {int(x)} - {int(x + 49)}"
            )
        )

        st.bar_chart(
            distribuzione,
            x="Fascia prezzo",
            y="Annunci",
            width="stretch",
        )

    else:
        st.info("Nessun prezzo disponibile.")


# ---------------------------------------------------------
# TOP CATEGORIE
# ---------------------------------------------------------

st.divider()

st.subheader("🏆 Categorie principali")

category_stats = (
    filtered
    .groupby("category")
    .agg(
        Annunci=("id", "count"),
        Prezzo_medio=("price", "mean"),
        Tempo_medio_ore=("sale_time_hours", "mean"),
    )
    .reset_index()
    .sort_values(
        "Annunci",
        ascending=False,
    )
    .head(10)
)


category_stats["Prezzo medio"] = (
    category_stats["Prezzo_medio"]
    .apply(
        lambda x:
        format_euro(x)
        if pd.notna(x)
        else "-"
    )
)

category_stats["Tempo medio vendita"] = (
    category_stats["Tempo_medio_ore"]
    .apply(format_tempo)
)

category_stats = category_stats.rename(
    columns={
        "category": "Categoria",
    }
)


st.dataframe(
    category_stats[
        [
            "Categoria",
            "Annunci",
            "Prezzo medio",
            "Tempo medio vendita",
        ]
    ],
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------
# ULTIMI ANNUNCI VENDUTI
# ---------------------------------------------------------

st.divider()

st.subheader("🕐 Ultimi annunci venduti")


ultimi = filtered.copy()

ultimi["_reference_date_sort"] = pd.to_datetime(
    ultimi["reference_date"],
    errors="coerce",
    utc=True,
)

ultimi = (
    ultimi
    .sort_values(
        "_reference_date_sort",
        ascending=False,
    )
    .head(20)
    .copy()
)

ultimi = ultimi.drop(
    columns=["_reference_date_sort"]
)


ultimi["Pubblicato"] = (
    ultimi["posted_at"]
    .dt.strftime("%d/%m/%Y %H:%M")
    .fillna("-")
)


ultimi["Rilevato venduto"] = (
    ultimi["detected_sold_at"]
    .dt.strftime("%d/%m/%Y %H:%M")
    .fillna("-")
)


ultimi["Prezzo"] = (
    ultimi["price"]
    .apply(
        lambda x:
        format_euro(x)
        if pd.notna(x)
        else "-"
    )
)


ultimi["Tempo vendita"] = (
    ultimi["sale_time_hours"]
    .apply(format_tempo)
)


ultimi = ultimi.rename(
    columns={
        "title": "Prodotto",
        "category": "Categoria",
    }
)


st.dataframe(
    ultimi[
        [
            "Prodotto",
            "Categoria",
            "Prezzo",
            "Tempo vendita",
            "Pubblicato",
            "Rilevato venduto",
        ]
    ],
    width="stretch",
    hide_index=True,
)