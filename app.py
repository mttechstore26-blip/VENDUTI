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

    :root {
        --mt-bg: #f5f7fb;
        --mt-card: rgba(255,255,255,0.78);
        --mt-border: rgba(15,23,42,0.08);
        --mt-text: #0f172a;
        --mt-muted: #64748b;
        --mt-blue: #2563eb;
        --mt-violet: #7c3aed;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(37,99,235,0.10), transparent 30%),
            radial-gradient(circle at 94% 8%, rgba(124,58,237,0.09), transparent 28%),
            linear-gradient(180deg, #fbfdff 0%, #f6f8fc 48%, #eef3f9 100%);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.25rem;
        padding-bottom: 4rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    h1, h2, h3 {
        color: var(--mt-text);
        letter-spacing: -0.03em;
    }

    h1 {
        font-size: 2.25rem !important;
        font-weight: 900 !important;
    }

    h2 {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
    }

    h3 {
        font-weight: 800 !important;
    }

    /* HERO */
    .mt-hero {
        position: relative;
        overflow: hidden;
        border-radius: 28px;
        padding: 28px 30px;
        margin-bottom: 1.6rem;
        color: white;
        background:
            radial-gradient(circle at 92% 12%, rgba(168,85,247,0.34), transparent 28%),
            radial-gradient(circle at 8% 90%, rgba(59,130,246,0.28), transparent 35%),
            linear-gradient(135deg, #0f172a 0%, #172554 56%, #312e81 100%);
        box-shadow: 0 20px 48px rgba(15,23,42,0.18);
    }

    .mt-hero::after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        border-radius: 50%;
        right: -90px;
        bottom: -120px;
        background: rgba(255,255,255,0.07);
    }

    .mt-hero-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 18px;
        position: relative;
        z-index: 1;
    }

    .mt-hero-title {
        font-size: 2rem;
        line-height: 1.08;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin-bottom: 8px;
    }

    .mt-hero-subtitle {
        color: rgba(255,255,255,0.72);
        font-size: 0.98rem;
    }

    .mt-live {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.11);
        border: 1px solid rgba(255,255,255,0.15);
        font-size: 0.78rem;
        font-weight: 800;
        white-space: nowrap;
    }

    .mt-live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4ade80;
        box-shadow: 0 0 0 0 rgba(74,222,128,0.5);
        animation: mtPulse 1.8s infinite;
    }

    @keyframes mtPulse {
        0% { box-shadow: 0 0 0 0 rgba(74,222,128,0.55); }
        70% { box-shadow: 0 0 0 8px rgba(74,222,128,0); }
        100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); }
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,250,252,0.90));
        border-right: 1px solid var(--mt-border);
        /* niente blur globale: più fluido durante scroll e rerun */
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.2rem;
    }

    div[data-testid="stSidebarNav"] a {
        border-radius: 13px;
        margin-bottom: 5px;
        transition: all 0.18s ease;
        font-weight: 700;
    }

    div[data-testid="stSidebarNav"] a:hover {
        background: rgba(37,99,235,0.08);
        transform: translateX(2px);
    }

    /* KPI */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(255,255,255,0.82);
        border-radius: 20px;
        padding: 18px 20px;
        min-height: 118px;
        background: rgba(255,255,255,0.72);
        box-shadow: 0 10px 28px rgba(15,23,42,0.06);
        position: relative;
        overflow: hidden;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    div[data-testid="stMetric"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--mt-blue), var(--mt-violet));
    }

    div[data-testid="stMetric"]:hover {
        box-shadow: 0 12px 28px rgba(15,23,42,0.08);
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.88rem;
        font-weight: 700;
        color: var(--mt-muted);
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: var(--mt-text);
    }

    /* CARD / CONTAINER */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 20px;
        border-color: rgba(255,255,255,0.82);
        background: rgba(255,255,255,0.62);
        box-shadow: 0 10px 26px rgba(15,23,42,0.05);
    }

    /* INPUT */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 13px !important;
        background: rgba(255,255,255,0.92) !important;
        border-color: rgba(15,23,42,0.08) !important;
        box-shadow: 0 4px 12px rgba(15,23,42,0.03);
    }

    /* BUTTON */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 13px;
        font-weight: 800;
        min-height: 42px;
        border: 1px solid rgba(15,23,42,0.08);
        background: linear-gradient(180deg, #ffffff 0%, #f7f9fc 100%);
        box-shadow: 0 7px 16px rgba(15,23,42,0.05);
        transition: all 0.18s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        box-shadow: 0 10px 20px rgba(15,23,42,0.08);
        border-color: rgba(37,99,235,0.18);
    }

    /* TABLES */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.82);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        background: rgba(255,255,255,0.72);
    }

    /* CHARTS */
    div[data-testid="stVegaLiteChart"],
    div[data-testid="stPlotlyChart"] {
        border: 1px solid rgba(255,255,255,0.82);
        border-radius: 18px;
        padding: 10px;
        background: rgba(255,255,255,0.66);
        box-shadow: 0 10px 24px rgba(15,23,42,0.04);
        backdrop-filter: blur(10px);
    }

    /* EXPANDER */
    details {
        border-radius: 16px !important;
        overflow: hidden;
    }

    hr {
        margin-top: 2rem !important;
        margin-bottom: 2rem !important;
        opacity: 0.12;
    }

    div[data-testid="stCaptionContainer"] {
        margin-bottom: 1.15rem;
        color: var(--mt-muted);
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .mt-hero {
            padding: 21px;
            border-radius: 22px;
        }

        .mt-hero-top {
            flex-direction: column;
        }

        .mt-hero-title {
            font-size: 1.55rem;
        }
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
    default=True,
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
            categorie,
            annunci,
            prezzi,
            trend,
        ]
    }
)

pg.run()