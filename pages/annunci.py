import re
import streamlit as st
import pandas as pd

from database import get_connection


st.markdown(
    """
    <div class="mt-hero">
        <div class="mt-hero-top">
            <div>
                <div class="mt-hero-title">📦 Annunci venduti</div>
                <div class="mt-hero-subtitle">Trova cosa si vende, a che prezzo e in quanto tempo</div>
            </div>
            <div class="mt-live"><span class="mt-live-dot"></span> Dati aggiornati</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_data():
    conn = get_connection()

    query = """
        SELECT
            l.external_id,
            l.title,
            l.url,
            l.price,
            l.posted_at,
            l.detected_sold_at,
            m.name AS category
        FROM listings l
        LEFT JOIN monitorings m
            ON l.monitoring_id = m.id
        WHERE l.detected_sold_at IS NOT NULL
        ORDER BY l.detected_sold_at DESC
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
    if pd.isna(hours) or hours < 0:
        return "-"

    total_minutes = int(hours * 60)

    days = total_minutes // (24 * 60)
    remaining_minutes = total_minutes % (24 * 60)

    h = remaining_minutes // 60
    minutes = remaining_minutes % 60

    if days > 0:
        return f"{days}g {h}h {minutes}m"

    if h > 0:
        return f"{h}h {minutes}m"

    return f"{minutes}m"


def speed_emoji(hours):
    if pd.isna(hours) or hours < 0:
        return ""

    if hours <= 6:
        return "🔥🔥🔥🔥"

    if hours <= 12:
        return "🔥🔥🔥"

    if hours <= 24:
        return "🔥🔥"

    if hours <= 48:
        return "🔥"

    return "🐢"


def speed_category(hours):
    if pd.isna(hours) or hours < 0:
        return "Non disponibile"

    if hours <= 6:
        return "🔥🔥🔥🔥 0-6 ore"

    if hours <= 12:
        return "🔥🔥🔥 6-12 ore"

    if hours <= 24:
        return "🔥🔥 12-24 ore"

    if hours <= 48:
        return "🔥 24-48 ore"

    return "🐢 Oltre 48 ore"

def detect_iphone_model(title):
    text = str(title).lower()

    text = (
        text
        .replace("pro-max", "pro max")
        .replace("promax", "pro max")
        .replace("pro/max", "pro max")
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    generations = [
        "17",
        "16",
        "15",
        "14",
        "13",
        "12",
        "11",
    ]

    for generation in generations:

        if re.search(
            rf"\biphone\s*{generation}\s*pro\s*max\b",
            text,
        ):
            return f"iPhone {generation} Pro Max"

        if re.search(
            rf"\biphone\s*{generation}\s*pro\b",
            text,
        ):
            return f"iPhone {generation} Pro"

        if re.search(
            rf"\biphone\s*{generation}\s*plus\b",
            text,
        ):
            return f"iPhone {generation} Plus"

        if re.search(
            rf"\biphone\s*{generation}\s*mini\b",
            text,
        ):
            return f"iPhone {generation} mini"

        if re.search(
            rf"\biphone\s*{generation}\b",
            text,
        ):
            return f"iPhone {generation}"

    old_models = [
        (r"\biphone\s*xs\s*max\b", "iPhone XS Max"),
        (r"\biphone\s*xs\b", "iPhone XS"),
        (r"\biphone\s*xr\b", "iPhone XR"),
        (r"\biphone\s*x\b", "iPhone X"),
        (r"\biphone\s*8\s*plus\b", "iPhone 8 Plus"),
        (r"\biphone\s*8\b", "iPhone 8"),
        (r"\biphone\s*7\s*plus\b", "iPhone 7 Plus"),
        (r"\biphone\s*7\b", "iPhone 7"),
        (r"\biphone\s*se\b", "iPhone SE"),
    ]

    for pattern, model in old_models:
        if re.search(pattern, text):
            return model

    if "iphone" in text:
        return "iPhone non classificato"

    return None

df = load_data()

if df.empty:
    st.warning("Nessun annuncio venduto presente.")
    st.stop()


# -----------------------------------
# NORMALIZZAZIONE DATI
# -----------------------------------

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

df["title"] = (
    df["title"]
    .fillna("Senza titolo")
)


# -----------------------------------
# TEMPO DI VENDITA
# -----------------------------------

df["sale_time_hours"] = (
    df["detected_sold_at"]
    - df["posted_at"]
).dt.total_seconds() / 3600


df.loc[
    df["sale_time_hours"] < 0,
    "sale_time_hours",
] = pd.NA


df["speed_category"] = (
    df["sale_time_hours"]
    .apply(speed_category)
)


# -----------------------------------
# SIDEBAR
# -----------------------------------

st.sidebar.header("🔎 Filtri")


search = st.sidebar.text_input(
    "Cerca prodotto",
    placeholder="Es. PS5, Canon, iPhone...",
)


categories = sorted(
    df["category"]
    .dropna()
    .unique()
    .tolist()
)


selected_categories = st.sidebar.multiselect(
    "Categorie",
    categories,
    default=[],
)


min_price = (
    int(df["price"].min())
    if df["price"].notna().any()
    else 0
)

max_price = (
    int(df["price"].max())
    if df["price"].notna().any()
    else 1000
)

if max_price <= min_price:
    max_price = min_price + 1


price_range = st.sidebar.slider(
    "Fascia di prezzo",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
)


periodo = st.sidebar.selectbox(
    "Periodo",
    [
        "Tutto",
        "Ultimi 7 giorni",
        "Ultimi 30 giorni",
        "Ultimi 90 giorni",
        "Ultimi 365 giorni",
    ],
)


speed_options = [
    "🔥🔥🔥🔥 0-6 ore",
    "🔥🔥🔥 6-12 ore",
    "🔥🔥 12-24 ore",
    "🔥 24-48 ore",
    "🐢 Oltre 48 ore",
]


selected_speed = st.sidebar.multiselect(
    "Velocità di vendita",
    speed_options,
    default=[],
)


sort_option = st.sidebar.selectbox(
    "Ordina per",
    [
        "Più recenti",
        "Venduti più velocemente",
        "Venduti più lentamente",
        "Prezzo più basso",
        "Prezzo più alto",
    ],
)


# -----------------------------------
# FILTRI
# -----------------------------------

filtered = df.copy()


if search:
    filtered = filtered[
        filtered["title"]
        .str.contains(
            search,
            case=False,
            regex=False,
            na=False,
        )
    ]


if selected_categories:
    filtered = filtered[
        filtered["category"]
        .isin(selected_categories)
    ]


filtered = filtered[
    filtered["price"].isna()
    | filtered["price"].between(
        price_range[0],
        price_range[1],
    )
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


if selected_speed:
    filtered = filtered[
        filtered["speed_category"]
        .isin(selected_speed)
    ]


# -----------------------------------
# ORDINAMENTO
# -----------------------------------

if sort_option == "Più recenti":
    filtered = filtered.sort_values(
        "detected_sold_at",
        ascending=False,
    )

elif sort_option == "Venduti più velocemente":
    filtered = filtered.sort_values(
        "sale_time_hours",
        ascending=True,
        na_position="last",
    )

elif sort_option == "Venduti più lentamente":
    filtered = filtered.sort_values(
        "sale_time_hours",
        ascending=False,
        na_position="last",
    )

elif sort_option == "Prezzo più basso":
    filtered = filtered.sort_values(
        "price",
        ascending=True,
        na_position="last",
    )

elif sort_option == "Prezzo più alto":
    filtered = filtered.sort_values(
        "price",
        ascending=False,
        na_position="last",
    )


# -----------------------------------
# NESSUN RISULTATO
# -----------------------------------

if filtered.empty:
    st.info(
        "Nessun annuncio corrisponde ai filtri selezionati."
    )
    st.stop()


# -----------------------------------
# STATISTICHE PREZZO
# -----------------------------------

col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "📦 Annunci trovati",
        f"{len(filtered):,}".replace(",", "."),
    )


with col2:
    median_price = filtered["price"].median()

    st.metric(
        "💰 Prezzo mediano",
        format_price(median_price),
    )


with col3:
    average_price = filtered["price"].mean()

    st.metric(
        "📊 Prezzo medio",
        format_price(average_price),
    )


# -----------------------------------
# TABELLA
# -----------------------------------

st.divider()

with st.expander("📋 Elenco annunci venduti", expanded=True):


    table = filtered[
        [
            "title",
            "url",
            "category",
            "price",
            "posted_at",
            "detected_sold_at",
            "sale_time_hours",
        ]
    ].copy()


    table["Velocità"] = (
        table["sale_time_hours"]
        .apply(
            lambda hours: (
                f"{speed_emoji(hours)} "
                f"{format_duration(hours)}"
            ).strip()
        )
    )


    table["price"] = (
        table["price"]
        .apply(format_price)
    )


    table["posted_at"] = (
        table["posted_at"]
        .dt.tz_convert("Europe/Rome")
        .dt.strftime("%d/%m/%Y %H:%M")
        .fillna("-")
    )


    table["detected_sold_at"] = (
        table["detected_sold_at"]
        .dt.tz_convert("Europe/Rome")
        .dt.strftime("%d/%m/%Y %H:%M")
        .fillna("-")
    )


    table["Prodotto"] = table.apply(
        lambda row: (
            f'<a href="{row["url"]}" target="_blank">{row["title"]}</a>'
            if pd.notna(row["url"]) and row["url"]
            else row["title"]
        ),
        axis=1,
    )


    table = table[
        [
            "Prodotto",
            "category",
            "price",
            "Velocità",
            "posted_at",
            "detected_sold_at",
        ]
    ]


    table.columns = [
        "Prodotto",
        "Categoria",
        "Prezzo",
        "Venduto in",
        "Pubblicato",
        "Venduto rilevato",
    ]


    html_table = table.to_html(
        escape=False,
        index=False,
    )

    st.markdown(
        """
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th, td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(128,128,128,0.25);
            text-align: left;
            vertical-align: middle;
        }

        th {
            font-weight: 700;
            position: sticky;
            top: 0;
        }

        td a {
            text-decoration: none;
            font-weight: 600;
        }

        td a:hover {
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        html_table,
        unsafe_allow_html=True,
    )


# -----------------------------------
# STATISTICHE VELOCITÀ
# -----------------------------------

col4, col5, col6 = st.columns(3)


valid_sale_times = (
    filtered["sale_time_hours"]
    .dropna()
)


with col4:

    if not valid_sale_times.empty:
        median_sale_time = valid_sale_times.median()
        value = format_duration(median_sale_time)
    else:
        value = "-"

    st.metric(
        "⏱️ Tempo mediano vendita",
        value,
    )


with col5:

    if not valid_sale_times.empty:
        average_sale_time = valid_sale_times.mean()
        value = format_duration(average_sale_time)
    else:
        value = "-"

    st.metric(
        "⏳ Tempo medio vendita",
        value,
    )


with col6:

    fast_sales = filtered[
        filtered["sale_time_hours"] <= 6
    ]

    fast_percentage = (
        len(fast_sales)
        / len(filtered)
        * 100
    )

    st.metric(
        "🔥 Venduti entro 6h",
        f"{len(fast_sales)} ({fast_percentage:.1f}%)",
    )


# -----------------------------------
# INDICE DI INTERESSE
# -----------------------------------

if not valid_sale_times.empty:

    median_hours = valid_sale_times.median()

    if median_hours <= 6:
        interest_label = "Molto alto 🔥🔥🔥🔥"

    elif median_hours <= 12:
        interest_label = "Alto 🔥🔥🔥"

    elif median_hours <= 24:
        interest_label = "Medio 🔥🔥"

    elif median_hours <= 48:
        interest_label = "Basso 🔥"

    else:
        interest_label = "Lento 🐢"

else:
    interest_label = "-"


st.metric(
    "📈 Indice di interesse",
    interest_label,
)


# -----------------------------------
# ANALISI VELOCITÀ
# -----------------------------------

st.divider()

st.subheader("🔥 Analisi velocità di vendita")


speed_counts = {
    "🔥🔥🔥🔥 0-6 ore": len(
        filtered[
            (filtered["sale_time_hours"] >= 0)
            & (filtered["sale_time_hours"] <= 6)
        ]
    ),
    "🔥🔥🔥 6-12 ore": len(
        filtered[
            (filtered["sale_time_hours"] > 6)
            & (filtered["sale_time_hours"] <= 12)
        ]
    ),
    "🔥🔥 12-24 ore": len(
        filtered[
            (filtered["sale_time_hours"] > 12)
            & (filtered["sale_time_hours"] <= 24)
        ]
    ),
    "🔥 24-48 ore": len(
        filtered[
            (filtered["sale_time_hours"] > 24)
            & (filtered["sale_time_hours"] <= 48)
        ]
    ),
    "🐢 Oltre 48 ore": len(
        filtered[
            filtered["sale_time_hours"] > 48
        ]
    ),
}


speed_df = pd.DataFrame(
    {
        "Fascia": list(speed_counts.keys()),
        "Annunci": list(speed_counts.values()),
    }
)


col_speed_1, col_speed_2 = st.columns(2)


with col_speed_1:

    for label, count in speed_counts.items():
        st.metric(
            label,
            count,
        )


with col_speed_2:

    st.bar_chart(
        speed_df,
        x="Fascia",
        y="Annunci",
        horizontal=True,
        width="stretch",
    )

# -----------------------------------
# ANALISI MODELLI IPHONE
# -----------------------------------

iphone_df = filtered[
    filtered["title"]
    .str.contains(
        "iphone",
        case=False,
        regex=False,
        na=False,
    )
].copy()


if not iphone_df.empty:

    st.divider()

    st.subheader("📱 Analisi modelli iPhone")

    iphone_df["Modello iPhone"] = (
        iphone_df["title"]
        .apply(detect_iphone_model)
    )

    classified_iphone = iphone_df[
        iphone_df["Modello iPhone"]
        .notna()
    ].copy()


    iphone_stats = (
        classified_iphone
        .groupby("Modello iPhone")
        .agg(
            Venduti=("external_id", "count"),
            Prezzo_medio=("price", "mean"),
            Prezzo_mediano=("price", "median"),
            Tempo_medio=("sale_time_hours", "mean"),
            Tempo_mediano=("sale_time_hours", "median"),
        )
        .reset_index()
        .sort_values(
            "Venduti",
            ascending=False,
        )
    )


    if not iphone_stats.empty:

        iphone_stats_display = iphone_stats.copy()

        iphone_stats_display["Prezzo medio"] = (
            iphone_stats_display["Prezzo_medio"]
            .apply(format_price)
        )

        iphone_stats_display["Prezzo mediano"] = (
            iphone_stats_display["Prezzo_mediano"]
            .apply(format_price)
        )

        iphone_stats_display["Tempo medio"] = (
            iphone_stats_display["Tempo_medio"]
            .apply(format_duration)
        )

        iphone_stats_display["Tempo mediano"] = (
            iphone_stats_display["Tempo_mediano"]
            .apply(format_duration)
        )


        st.dataframe(
            iphone_stats_display[
                [
                    "Modello iPhone",
                    "Venduti",
                    "Prezzo medio",
                    "Prezzo mediano",
                    "Tempo medio",
                    "Tempo mediano",
                ]
            ],
            width="stretch",
            hide_index=True,
        )


        st.subheader(
            "🔍 Dettaglio modello"
        )


        selected_iphone_model = st.selectbox(
            "Scegli il modello iPhone",
            iphone_stats[
                "Modello iPhone"
            ].tolist(),
        )


        selected_iphone_df = (
            classified_iphone[
                classified_iphone["Modello iPhone"]
                == selected_iphone_model
            ]
            .sort_values(
                "detected_sold_at",
                ascending=False,
            )
            .copy()
        )


        prices = (
            selected_iphone_df["price"]
            .dropna()
        )

        times = (
            selected_iphone_df["sale_time_hours"]
            .dropna()
        )


        iphone_col1, iphone_col2, iphone_col3, iphone_col4 = (
            st.columns(4)
        )


        with iphone_col1:
            st.metric(
                "📦 Venduti",
                len(selected_iphone_df),
            )


        with iphone_col2:
            st.metric(
                "💰 Prezzo medio",
                format_price(
                    prices.mean()
                    if not prices.empty
                    else pd.NA
                ),
            )


        with iphone_col3:
            st.metric(
                "📊 Prezzo mediano",
                format_price(
                    prices.median()
                    if not prices.empty
                    else pd.NA
                ),
            )


        with iphone_col4:
            st.metric(
                "⏱️ Tempo mediano",
                format_duration(
                    times.median()
                    if not times.empty
                    else pd.NA
                ),
            )


        st.markdown(
            f"### 📋 Annunci venduti — {selected_iphone_model}"
        )


        iphone_rows = []

        for _, row in selected_iphone_df.iterrows():

            title = str(row["title"])
            url = row["url"]

            if pd.notna(url) and url:
                prodotto = (
                    f'<a href="{url}" target="_blank">'
                    f'{title}</a>'
                )
            else:
                prodotto = title


            pubblicato = "-"

            if pd.notna(row["posted_at"]):
                pubblicato = (
                    row["posted_at"]
                    .tz_convert("Europe/Rome")
                    .strftime("%d/%m/%Y %H:%M")
                )


            venduto = "-"

            if pd.notna(row["detected_sold_at"]):
                venduto = (
                    row["detected_sold_at"]
                    .tz_convert("Europe/Rome")
                    .strftime("%d/%m/%Y %H:%M")
                )


            iphone_rows.append(
                {
                    "Prodotto": prodotto,
                    "Prezzo": format_price(
                        row["price"]
                    ),
                    "Venduto in": format_duration(
                        row["sale_time_hours"]
                    ),
                    "Pubblicato": pubblicato,
                    "Venduto rilevato": venduto,
                }
            )


        iphone_table = pd.DataFrame(
            iphone_rows
        )


        iphone_html = iphone_table.to_html(
            escape=False,
            index=False,
        )


        st.markdown(
            iphone_html,
            unsafe_allow_html=True,
        )

