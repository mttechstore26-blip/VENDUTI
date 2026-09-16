import streamlit as st


st.set_page_config(
    page_title="MT TECH Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# STILE GLOBALE
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* CONTENUTO PRINCIPALE */
    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 4rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
    }

    /* FONT GENERALE */
    html, body, [class*="css"] {
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Roboto,
            Helvetica,
            Arial,
            sans-serif;
    }

    /* TITOLI */
    h1 {
        font-size: 2.25rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem !important;
    }

    h2 {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    h3 {
        font-weight: 700 !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        border-right: 1px solid
            rgba(128, 128, 128, 0.18);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    /* NAVIGAZIONE */
    div[data-testid="stSidebarNav"] a {
        border-radius: 10px;
        margin-bottom: 4px;
        transition: all 0.15s ease;
    }

    div[data-testid="stSidebarNav"] a:hover {
        background:
            rgba(128, 128, 128, 0.12);
    }

    /* METRICHE */
    div[data-testid="stMetric"] {
        border:
            1px solid rgba(128, 128, 128, 0.18);
        border-radius: 16px;
        padding: 18px 20px;
        min-height: 120px;
        box-shadow:
            0 2px 10px rgba(0, 0, 0, 0.04);
        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow:
            0 7px 22px rgba(0, 0, 0, 0.08);
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.92rem;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 750;
        letter-spacing: -0.03em;
    }

    /* INPUT */
    div[data-baseweb="input"] {
        border-radius: 10px;
    }

    div[data-baseweb="select"] > div {
        border-radius: 10px;
    }

    /* PULSANTI */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.15s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    /* DATAFRAME */
    div[data-testid="stDataFrame"] {
        border:
            1px solid rgba(128, 128, 128, 0.15);
        border-radius: 14px;
        overflow: hidden;
    }

    /* DIVISORI */
    hr {
        margin-top: 2.1rem !important;
        margin-bottom: 2.1rem !important;
        opacity: 0.18;
    }

    /* CAPTION */
    div[data-testid="stCaptionContainer"] {
        margin-bottom: 1.25rem;
    }

    /* GRAFICI */
    div[data-testid="stVegaLiteChart"] {
        border:
            1px solid rgba(128, 128, 128, 0.12);
        border-radius: 14px;
        padding: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# PAGINE
# ---------------------------------------------------------

dashboard = st.Page(
    "pages/dashboard.py",
    title="Dashboard",
    icon="📊",
    default=True,
)

annunci = st.Page(
    "pages/annunci.py",
    title="Annunci venduti",
    icon="📦",
)

categorie = st.Page(
    "pages/categorie.py",
    title="Categorie",
    icon="🏷️",
)

prezzi = st.Page(
    "pages/prezzi.py",
    title="Prezzi",
    icon="💰",
)

trend = st.Page(
    "pages/trend.py",
    title="Trend",
    icon="📈",
)


pg = st.navigation(
    {
        "MT TECH Market Intelligence": [
            dashboard,
            annunci,
            categorie,
            prezzi,
            trend,
        ]
    }
)

pg.run()