import streamlit as st
import pandas as pd

from data_cache import load_market_data


st.markdown(
    """
    <div class="mt-hero">
        <div class="mt-hero-top">
            <div>
                <div class="mt-hero-title">📈 Trend</div>
                <div class="mt-hero-subtitle">Segui l'andamento delle vendite e confronta i periodi</div>
            </div>
            <div class="mt-live"><span class="mt-live-dot"></span> Trend attivi</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


df = load_market_data().copy()

if df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

df = df[df["detected_sold_at"].notna()].copy()

if df.empty:
    st.warning("Nessun venduto disponibile.")
    st.stop()


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

st.subheader("🔎 Filtri")

col1, col2 = st.columns(2)


with col1:

    periodo = st.selectbox(
        "Periodo",
        [
            "Ultimi 7 giorni",
            "Ultimi 30 giorni",
            "Ultimi 90 giorni",
            "Ultimi 365 giorni",
            "Tutto",
        ],
        index=1,
    )


with col2:

    categorie = sorted(
        df["category"]
        .unique()
        .tolist()
    )

    selected_categories = st.multiselect(
        "Categorie",
        categorie,
        default=[],
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


if selected_categories:

    filtered = filtered[
        filtered["category"]
        .isin(selected_categories)
    ]


if filtered.empty:
    st.info(
        "Nessun dato disponibile per i filtri selezionati."
    )
    st.stop()


# ---------------------------------------------------------
# KPI
# ---------------------------------------------------------

st.divider()


totale_venduti = len(filtered)

prezzo_medio = (
    filtered["price"]
    .mean()
)

giorni_attivi = (
    filtered["detected_sold_at"]
    .dt.floor("D")
    .nunique()
)

media_giornaliera = (
    totale_venduti / giorni_attivi
    if giorni_attivi > 0
    else 0
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "📦 Venduti nel periodo",
        f"{totale_venduti:,}".replace(",", "."),
    )


with col2:

    st.metric(
        "📅 Media venduti/giorno",
        f"{media_giornaliera:.1f}",
    )


with col3:

    st.metric(
        "💰 Prezzo medio",
        format_price(prezzo_medio),
    )


# ---------------------------------------------------------
# VENDITE GIORNALIERE
# ---------------------------------------------------------

st.divider()

st.subheader("📈 Venduti nel tempo")


daily = filtered.copy()

daily["Giorno"] = (
    daily["detected_sold_at"]
    .dt.floor("D")
    .dt.tz_localize(None)
)


daily_sales = (
    daily
    .groupby("Giorno")
    .size()
    .reset_index(name="Venduti")
    .sort_values("Giorno")
)


st.line_chart(
    daily_sales,
    x="Giorno",
    y="Venduti",
    width="stretch",
)


# ---------------------------------------------------------
# MEDIA MOBILE
# ---------------------------------------------------------

st.subheader("📊 Media mobile vendite")


moving = daily_sales.copy()

moving["Media 7 giorni"] = (
    moving["Venduti"]
    .rolling(
        window=7,
        min_periods=1,
    )
    .mean()
)


st.line_chart(
    moving,
    x="Giorno",
    y=[
        "Venduti",
        "Media 7 giorni",
    ],
    width="stretch",
)


# ---------------------------------------------------------
# CONFRONTO PER CATEGORIA
# ---------------------------------------------------------

st.divider()

st.subheader("🏷️ Trend per categoria")


category_daily = (
    filtered
    .assign(
        Giorno=(
            filtered["detected_sold_at"]
            .dt.floor("D")
            .dt.tz_localize(None)
        )
    )
    .groupby(
        [
            "Giorno",
            "category",
        ]
    )
    .size()
    .reset_index(name="Venduti")
)


top_categories = (
    filtered
    .groupby("category")
    .size()
    .sort_values(
        ascending=False,
    )
    .head(8)
    .index
)


category_daily = category_daily[
    category_daily["category"]
    .isin(top_categories)
]


if not category_daily.empty:

    pivot_category = (
        category_daily
        .pivot(
            index="Giorno",
            columns="category",
            values="Venduti",
        )
        .fillna(0)
    )

    st.line_chart(
        pivot_category,
        width="stretch",
    )

else:

    st.info(
        "Dati insufficienti per il trend delle categorie."
    )


# ---------------------------------------------------------
# TREND PREZZO MEDIO
# ---------------------------------------------------------

st.divider()

st.subheader("💰 Andamento prezzo medio")


price_daily = (
    filtered[
        filtered["price"].notna()
    ]
    .assign(
        Giorno=(
            filtered[
                filtered["price"].notna()
            ]["detected_sold_at"]
            .dt.floor("D")
            .dt.tz_localize(None)
        )
    )
    .groupby("Giorno")
    .agg(
        Prezzo_medio=("price", "mean"),
        Prezzo_mediano=("price", "median"),
    )
    .reset_index()
    .sort_values("Giorno")
)


if not price_daily.empty:

    st.line_chart(
        price_daily,
        x="Giorno",
        y=[
            "Prezzo_medio",
            "Prezzo_mediano",
        ],
        width="stretch",
    )

else:

    st.info(
        "Prezzi insufficienti per mostrare il trend."
    )


# ---------------------------------------------------------
# CONFRONTO ULTIMI 7 GIORNI
# ---------------------------------------------------------

st.divider()

st.subheader("⚖️ Confronto ultimi 7 giorni")


now = pd.Timestamp.now(tz="UTC")

current_start = (
    now
    - pd.Timedelta(days=7)
)

previous_start = (
    now
    - pd.Timedelta(days=14)
)


current_period = df[
    df["detected_sold_at"] >= current_start
]


previous_period = df[
    (df["detected_sold_at"] >= previous_start)
    & (df["detected_sold_at"] < current_start)
]


current_count = len(current_period)
previous_count = len(previous_period)


if previous_count > 0:

    variation = (
        (current_count - previous_count)
        / previous_count
        * 100
    )

else:

    variation = None


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "📦 Ultimi 7 giorni",
        current_count,
    )


with col2:

    st.metric(
        "📦 7 giorni precedenti",
        previous_count,
    )


with col3:

    if variation is not None:

        st.metric(
            "📈 Variazione",
            f"{variation:+.1f}%",
        )

    else:

        st.metric(
            "📈 Variazione",
            "-",
        )


# ---------------------------------------------------------
# GIORNI MIGLIORI
# ---------------------------------------------------------

st.divider()

st.subheader("🏆 Giorni con più vendite")


best_days = (
    daily_sales
    .sort_values(
        "Venduti",
        ascending=False,
    )
    .head(10)
    .copy()
)


best_days["Data"] = (
    best_days["Giorno"]
    .dt.strftime("%d/%m/%Y")
)


st.dataframe(
    best_days[
        [
            "Data",
            "Venduti",
        ]
    ],
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------
# CATEGORIE IN CRESCITA
# ---------------------------------------------------------

st.divider()

st.subheader("🚀 Categorie in crescita")


current_categories = (
    current_period
    .groupby("category")
    .size()
)

previous_categories = (
    previous_period
    .groupby("category")
    .size()
)


all_categories = sorted(
    set(current_categories.index)
    | set(previous_categories.index)
)


growth_rows = []


for category in all_categories:

    current_value = int(
        current_categories.get(
            category,
            0,
        )
    )

    previous_value = int(
        previous_categories.get(
            category,
            0,
        )
    )

    difference = (
        current_value
        - previous_value
    )

    if previous_value > 0:

        growth_percentage = (
            difference
            / previous_value
            * 100
        )

    elif current_value > 0:

        growth_percentage = 100.0

    else:

        growth_percentage = 0.0


    growth_rows.append(
        {
            "Categoria": category,
            "Ultimi 7 giorni": current_value,
            "7 giorni precedenti": previous_value,
            "Differenza": difference,
            "Variazione %": growth_percentage,
        }
    )


growth_df = pd.DataFrame(
    growth_rows
)


growth_df = (
    growth_df
    .sort_values(
        [
            "Differenza",
            "Ultimi 7 giorni",
        ],
        ascending=[
            False,
            False,
        ],
    )
)


growth_df["Variazione"] = (
    growth_df["Variazione %"]
    .apply(
        lambda x: f"{x:+.1f}%"
    )
)


st.dataframe(
    growth_df[
        [
            "Categoria",
            "Ultimi 7 giorni",
            "7 giorni precedenti",
            "Differenza",
            "Variazione",
        ]
    ],
    width="stretch",
    hide_index=True,
    height=550,
)