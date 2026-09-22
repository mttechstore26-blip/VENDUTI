import re
from html import escape

import pandas as pd
import streamlit as st

from database import get_connection


st.markdown(
    """
    <div class="mt-hero">
        <div class="mt-hero-top">
            <div>
                <div class="mt-hero-title">🎯 Radar categorie</div>
                <div class="mt-hero-subtitle">Scopri dove si concentra la domanda, cosa ruota più velocemente e come si stanno muovendo i prezzi</div>
            </div>
            <div class="mt-live"><span class="mt-live-dot"></span> Radar live</div>
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
            l.id,
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

    total_minutes = max(0, int(hours * 60))
    days = total_minutes // (24 * 60)
    remaining = total_minutes % (24 * 60)
    h = remaining // 60
    minutes = remaining % 60

    if days > 0:
        return f"{days}g {h}h"

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


def format_speed(hours):
    if pd.isna(hours) or hours < 0:
        return "-"

    return f"{speed_emoji(hours)} {format_duration(hours)}"


def format_delta(value):
    if pd.isna(value):
        return "-"

    if value > 999:
        return "> +999%"

    if value < -999:
        return "< -999%"

    return f"{value:+.1f}%"


def normalize_text(value):
    text = str(value or "").lower()
    text = (
        text.replace("pro-max", "pro max")
        .replace("promax", "pro max")
        .replace("pro/max", "pro max")
        .replace("series-s", "series s")
        .replace("series-x", "series x")
        .replace("x-box", "xbox")
        .replace("x box", "xbox")
        .replace("serie s", "series s")
        .replace("serie x", "series x")
        .replace("pa5", "ps5")
        .replace("p55", "ps5")
        .replace("ps 5", "ps5")
        .replace("play station", "playstation")
        .replace("play 5", "ps5")
        .replace("playstaion", "playstation")
        .replace("playstion", "playstation")
        .replace("playstaton", "playstation")
        .replace("playstartion", "playstation")
        .replace("potal", "portal")
        .replace("nitendo", "nintendo")
        .replace("swich", "switch")
        .replace("metà", "meta")
    )
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_family(title, category=None):
    text = normalize_text(title)
    category_text = normalize_text(category or "")

    for generation in ["17", "16", "15", "14", "13", "12", "11"]:
        if re.search(rf"\biphone\s*{generation}\s*pro\s*max\b", text):
            return f"iPhone {generation} Pro Max"
        if re.search(rf"\biphone\s*{generation}\s*pro\b", text):
            return f"iPhone {generation} Pro"
        if re.search(rf"\biphone\s*{generation}\s*plus\b", text):
            return f"iPhone {generation} Plus"
        if re.search(rf"\biphone\s*{generation}\s*mini\b", text):
            return f"iPhone {generation} mini"
        if re.search(rf"\biphone\s*{generation}\b", text):
            return f"iPhone {generation}"

    if re.search(r"\b(?:ps|playstation)\s*portal\b", text):
        return "PlayStation Portal"

    console_patterns = [
        (r"\bps5\b.*\bpro\b|\bplaystation\s*5\b.*\bpro\b", "PS5 Pro"),
        (r"\bps5\b.*\bdigital\b|\bplaystation\s*5\b.*\bdigital\b", "PS5 Digital"),
        (r"\bps5\b|\bplaystation\s*5\b", "PS5"),
        (r"\bps4\s*pro\b|\bplaystation\s*4\s*pro\b", "PS4 Pro"),
        (r"\bps4\b|\bplaystation\s*4\b", "PS4"),
        (r"\bxbox\s*series\s*x\b", "Xbox Series X"),
        (r"\bxbox\s*series\s*s\b", "Xbox Series S"),
        (r"\bswitch\s*2\b", "Nintendo Switch 2"),
        (r"\bswitch\s*oled\b", "Nintendo Switch OLED"),
        (r"\bswitch\s*lite\b", "Nintendo Switch Lite"),
        (r"\bnintendo\s*switch\b|\bswitch\b", "Nintendo Switch"),
    ]
    for pattern, label in console_patterns:
        if re.search(pattern, text):
            return label

    apple_patterns = [
        (r"\bmacbook\s*pro\b", "MacBook Pro"),
        (r"\bmacbook\s*air\b", "MacBook Air"),
        (r"\bimac\b", "iMac"),
        (r"\bipad\s*pro\b", "iPad Pro"),
        (r"\bipad\s*air\b", "iPad Air"),
        (r"\bipad\s*mini\b", "iPad mini"),
        (r"\bipad\b", "iPad"),
    ]
    for pattern, label in apple_patterns:
        if re.search(pattern, text):
            return label

    galaxy = re.search(r"\b(?:samsung\s*)?galaxy\s+(s|a|z)\s?(\d{1,3})(?:\s+(ultra|plus|fe))?\b", text)
    if galaxy:
        series, number, variant = galaxy.groups()
        label = f"Samsung Galaxy {series.upper()}{number}"
        if variant:
            label += f" {variant.upper() if variant == 'fe' else variant.title()}"
        return label

    insta360 = re.search(
        r"\binsta\s*360\s+(go\s*\d+[a-z]?|x\s*\d+|ace\s*pro\s*\d*|one\s*[a-z0-9]+)(?:\s+(\d{2,4}gb))?\b",
        text,
    )
    if insta360:
        model, storage = insta360.groups()
        model = re.sub(r"\s+", " ", model).strip()
        label = f"Insta360 {model.upper() if model.startswith('x') else model.title()}"
        if storage:
            label += f" {storage.upper()}"
        return label

    meta_quest = re.search(
        r"\b(?:meta\s+)?quest\s*(2|3\s*s|3|pro)\b",
        text,
    )
    if not meta_quest:
        meta_quest = re.search(
            r"\bmeta\s+(2|3\s*s|3|pro)\b",
            text,
        )

    if meta_quest:
        model = re.sub(r"\s+", "", meta_quest.group(1)).upper()
        if model == "PRO":
            return "Meta Quest Pro"
        return f"Meta Quest {model}"

    gopro = re.search(
        r"\bgopro(?:\s+hero)?\s*(\d{1,2})(?:\s+(black|silver|white))?\b",
        text,
    )
    if gopro:
        generation, edition = gopro.groups()
        label = f"GoPro Hero {generation}"
        if edition:
            label += f" {edition.title()}"
        return label

    # Fotografia: riconoscimento marca + modello reale.
    # Evita famiglie troppo generiche come solo "Canon", "Nikon" o "Sony".
    camera_patterns = [
        # Canon reflex / mirrorless
        (r"\bcanon(?:\s+eos)?\s+(\d{2,4}d)\b", "Canon"),
        (r"\bcanon(?:\s+eos)?\s+(5d|6d|7d)(?:\s+mark\s+(ii|iii|iv))?\b", "Canon"),
        (r"\bcanon(?:\s+eos)?\s+(r(?:p|\d{1,3})|m\d{1,3})\b", "Canon"),

        # Nikon reflex / mirrorless
        (r"\bnikon\s+(d\d{2,4})\b", "Nikon"),
        (r"\bnikon\s+(z\s*(?:fc|\d{1,2}))(?:\s+(ii|iii))?\b", "Nikon"),

        # Sony Alpha / ZV / RX
        (r"\bsony(?:\s+alpha)?\s+(a?\d{4})\b", "Sony"),
        (r"\bsony(?:\s+alpha)?\s+(a7[crs]?|a9|a1)(?:\s+(ii|iii|iv|v))?\b", "Sony"),
        (r"\bsony\s+(zv[\-\s]?(?:e10|1|e1|1f))\b", "Sony"),
        (r"\bsony\s+(rx\s*\d{1,3}[a-z0-9]*)\b", "Sony"),

        # Fujifilm
        (r"\b(?:fujifilm|fuji)\s+((?:x|gfx)[\-\s]?[a-z0-9]+(?:\s*[a-z0-9]+)?)\b", "Fujifilm"),
    ]

    for pattern, brand in camera_patterns:
        match = re.search(pattern, text)
        if match:
            groups = [g for g in match.groups() if g]
            model = " ".join(groups)
            model = re.sub(r"\s+", " ", model).strip().upper()
            model = model.replace("Α", "A")
            return f"{brand} {model}"

    # Compatte / bridge
    compact_patterns = [
        (r"\bnikon\s+coolpix\s+([a-z0-9\-]+)", "Nikon Coolpix"),
        (r"\bcanon\s+ixus\s+([a-z0-9\-]+)", "Canon IXUS"),
        (r"\bcanon\s+powershot\s+([a-z0-9\-]+(?:\s*[a-z0-9]+)?)", "Canon PowerShot"),
        (r"\bsony\s+cyber[\-\s]?shot\s+([a-z0-9\-]+)", "Sony Cyber-shot"),
    ]
    for pattern, brand in compact_patterns:
        match = re.search(pattern, text)
        if match:
            return f"{brand} {match.group(1).upper()}"

    pc_patterns = [
        (r"\blenovo\s+thinkpad\b", "Lenovo ThinkPad"),
        (r"\blenovo\s+ideapad\b", "Lenovo IdeaPad"),
        (r"\blenovo\s+legion\b", "Lenovo Legion"),
        (r"\basus\s+rog\b", "ASUS ROG"),
        (r"\basus\s+tuf\b", "ASUS TUF"),
        (r"\bdell\s+xps\b", "Dell XPS"),
        (r"\bdell\s+latitude\b", "Dell Latitude"),
        (r"\bhp\s+elitebook\b", "HP EliteBook"),
        (r"\bhp\s+probook\b", "HP ProBook"),
    ]
    for pattern, label in pc_patterns:
        if re.search(pattern, text):
            return label

    brands = [
        ("apple", "Apple"),
        ("samsung", "Samsung"),
        ("sony", "Sony"),
        ("canon", "Canon"),
        ("nikon", "Nikon"),
        ("fujifilm", "Fujifilm"),
        ("lenovo", "Lenovo"),
        ("asus", "ASUS"),
        ("acer", "Acer"),
        ("dell", "Dell"),
        ("hp", "HP"),
        ("nintendo", "Nintendo"),
        ("xbox", "Xbox"),
        ("playstation", "PlayStation"),
        ("logitech", "Logitech"),
        ("dyson", "Dyson"),
    ]
    for token, label in brands:
        if re.search(rf"\b{re.escape(token)}\b", text):
            if (
                "fotografia" in category_text
                and label in {"Canon", "Nikon", "Sony", "Fujifilm"}
            ):
                continue
            return label

    return "Altro / non riconosciuto"



GENERIC_FAMILIES = {
    "Altro / non riconosciuto",
    "Apple",
    "Samsung",
    "Sony",
    "Canon",
    "Nikon",
    "Fujifilm",
    "Lenovo",
    "ASUS",
    "Acer",
    "Dell",
    "HP",
    "Nintendo",
    "Xbox",
    "PlayStation",
    "Logitech",
    "Dyson",
}

STOPWORDS = {
    "vendo", "vendesi", "nuovo", "nuova", "nuovi", "nuove",
    "usato", "usata", "usati", "usate", "come", "con", "senza",
    "per", "del", "della", "dello", "dei", "degli", "delle",
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
    "originale", "originali", "ottimo", "ottima", "perfetto",
    "perfetta", "condizioni", "condizione", "lotto", "stock",
    "spedizione", "regalo", "offerta", "prezzo", "solo",
}


def significant_tokens(title):
    tokens = normalize_text(title).split()
    return [
        token for token in tokens
        if len(token) >= 2
        and token not in STOPWORDS
    ]


def recurring_similarity(tokens_a, tokens_b):
    a = set(tokens_a)
    b = set(tokens_b)

    if not a or not b:
        return 0.0

    common = a & b

    # Servono almeno due elementi significativi in comune.
    # Con tre o più parole condivise accettiamo anche titoli più descrittivi.
    if len(common) < 2:
        return 0.0

    union = a | b
    jaccard = len(common) / len(union)

    if len(common) >= 3:
        # Tre parole significative uguali identificano già bene
        # prodotti ricorrenti anche quando il resto del titolo varia
        # (es. "ETB 30 anniversario ...").
        return 1.0

    # Con sole due parole condivise usiamo una soglia più severa
    # per evitare famiglie troppo generiche.
    return jaccard if jaccard >= 0.67 else 0.0


def pretty_family_label(token_list):
    special = {
        "etb": "ETB",
        "ps5": "PS5",
        "ps4": "PS4",
        "xbox": "Xbox",
        "pokemon": "Pokemon",
        "oled": "OLED",
        "gb": "GB",
        "tb": "TB",
    }

    parts = []
    for token in token_list:
        if token in special:
            parts.append(special[token])
        elif token.isdigit():
            parts.append(token)
        else:
            parts.append(token.capitalize())

    return " ".join(parts)


def recurring_ngrams(tokens):
    phrases = []

    # Consideriamo sequenze da 2 a 4 parole significative.
    # Sono molto più efficaci del semplice confronto del titolo intero
    # per categorie eterogenee come giardino, fai da te e collezionismo.
    for size in (4, 3, 2):
        if len(tokens) < size:
            continue

        for start in range(len(tokens) - size + 1):
            phrase = tuple(tokens[start:start + size])

            # Evita etichette formate quasi solo da numeri.
            if sum(token.isdigit() for token in phrase) >= size - 1:
                continue

            phrases.append(phrase)

    return phrases


def apply_recurring_families(dataframe):
    result = dataframe.copy()

    for category, group in result.groupby("category"):
        candidate_idx = [
            idx for idx in group.index
            if result.at[idx, "Famiglia"] in GENERIC_FAMILIES
        ]

        if len(candidate_idx) < 2:
            continue

        token_map = {
            idx: significant_tokens(result.at[idx, "title"])
            for idx in candidate_idx
        }

        # -----------------------------------------------------
        # 1) RICONOSCIMENTO PER FRASI RICORRENTI
        # -----------------------------------------------------
        phrase_members = {}

        for idx in candidate_idx:
            seen = set()
            for phrase in recurring_ngrams(token_map[idx]):
                if phrase in seen:
                    continue
                seen.add(phrase)
                phrase_members.setdefault(phrase, []).append(idx)

        recurring = {
            phrase: members
            for phrase, members in phrase_members.items()
            if len(set(members)) >= 2
        }

        # Preferiamo prima le frasi più lunghe, poi quelle più frequenti.
        ordered_phrases = sorted(
            recurring.items(),
            key=lambda item: (
                len(item[0]),
                len(set(item[1])),
            ),
            reverse=True,
        )

        assigned = set()

        for phrase, members in ordered_phrases:
            available = [
                idx for idx in dict.fromkeys(members)
                if idx not in assigned
            ]

            if len(available) < 2:
                continue

            label = pretty_family_label(list(phrase))

            for idx in available:
                result.at[idx, "Famiglia"] = label
                assigned.add(idx)

        # -----------------------------------------------------
        # 2) FALLBACK: SIMILARITÀ FRA TITOLI
        # -----------------------------------------------------
        remaining = [
            idx for idx in candidate_idx
            if idx not in assigned
        ]

        if len(remaining) < 2:
            continue

        parent = {idx: idx for idx in remaining}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            root_a = find(a)
            root_b = find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        for pos, idx_a in enumerate(remaining):
            for idx_b in remaining[pos + 1:]:
                similarity = recurring_similarity(
                    token_map[idx_a],
                    token_map[idx_b],
                )

                if similarity >= 0.50:
                    union(idx_a, idx_b)

        clusters = {}
        for idx in remaining:
            clusters.setdefault(find(idx), []).append(idx)

        for members in clusters.values():
            if len(members) < 2:
                continue

            common_tokens = set(token_map[members[0]])
            for idx in members[1:]:
                common_tokens &= set(token_map[idx])

            if len(common_tokens) < 2:
                continue

            representative = min(
                members,
                key=lambda idx: len(token_map[idx]),
            )

            ordered_common = [
                token
                for token in token_map[representative]
                if token in common_tokens
            ][:5]

            if len(ordered_common) < 2:
                continue

            label = pretty_family_label(ordered_common)

            for idx in members:
                result.at[idx, "Famiglia"] = label

    return result



def apply_manual_family_overrides(dataframe):
    result = dataframe.copy()

    # Correzioni puntuali per annunci con titolo troppo generico
    # ma modello verificato manualmente.
    overrides = {
        "661292338": "Xbox Series S",
    }

    for needle, family in overrides.items():
        mask = result["url"].fillna("").astype(str).str.contains(
            needle,
            regex=False,
        )
        result.loc[mask, "Famiglia"] = family

    return result


def aggregate(group):
    return pd.Series(
        {
            "Venduti": int(group["id"].count()),
            "Prezzo_medio": group["price"].mean(),
            "Prezzo_mediano": group["price"].median(),
            "Tempo_mediano_ore": group["sale_time_hours"].median(),
        }
    )


df = load_data()

if df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()


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

df["category"] = df["category"].fillna("Senza categoria")
df["title"] = df["title"].fillna("Senza titolo")

df["sale_time_hours"] = (
    df["detected_sold_at"] - df["posted_at"]
).dt.total_seconds() / 3600

df.loc[df["sale_time_hours"] < 0, "sale_time_hours"] = pd.NA

# Esclude dalle analisi gli annunci che hanno impiegato più di 10 giorni a vendersi.
# Le righe restano nel database: il filtro vale solo per questa pagina.
df = df[
    df["sale_time_hours"].notna()
    & (df["sale_time_hours"] <= 24 * 10)
].copy()

df["Famiglia"] = df.apply(
    lambda row: detect_family(row["title"], row["category"]),
    axis=1,
)
df = apply_recurring_families(df)
df = apply_manual_family_overrides(df)

df = df[df["detected_sold_at"].notna()].copy()


now = pd.Timestamp.now(tz="UTC")
current_start = now - pd.Timedelta(days=30)
previous_start = now - pd.Timedelta(days=60)

current = df[df["detected_sold_at"] >= current_start].copy()
previous = df[
    (df["detected_sold_at"] >= previous_start)
    & (df["detected_sold_at"] < current_start)
].copy()

if current.empty:
    st.info("Non ci sono venduti negli ultimi 30 giorni.")
    st.stop()



# ---------------------------------------------------------
# PREPARAZIONE RADAR (serve anche all'esplorazione in primo piano)
# ---------------------------------------------------------

current_cat = (
    current
    .groupby("category", dropna=False)
    .apply(aggregate)
    .reset_index()
)

previous_cat = (
    previous
    .groupby("category", dropna=False)
    .apply(aggregate)
    .reset_index()
    if not previous.empty
    else pd.DataFrame(
        columns=[
            "category",
            "Venduti",
            "Prezzo_medio",
            "Prezzo_mediano",
            "Tempo_mediano_ore",
        ]
    )
)

previous_cat = previous_cat.rename(
    columns={
        "Venduti": "Venduti_prec",
        "Prezzo_medio": "Prezzo_medio_prec",
        "Prezzo_mediano": "Prezzo_mediano_prec",
        "Tempo_mediano_ore": "Tempo_mediano_ore_prec",
    }
)

radar = current_cat.merge(
    previous_cat,
    on="category",
    how="left",
)

radar["Venduti_prec"] = radar["Venduti_prec"].fillna(0)

radar["Trend_volume_%"] = radar.apply(
    lambda row: (
        ((row["Venduti"] - row["Venduti_prec"]) / row["Venduti_prec"]) * 100
        if row["Venduti_prec"] > 0
        else pd.NA
    ),
    axis=1,
)

radar["Trend_prezzo_%"] = radar.apply(
    lambda row: (
        ((row["Prezzo_mediano"] - row["Prezzo_mediano_prec"]) / row["Prezzo_mediano_prec"]) * 100
        if pd.notna(row["Prezzo_mediano_prec"])
        and row["Prezzo_mediano_prec"] != 0
        else pd.NA
    ),
    axis=1,
)

radar["Trend_velocita_%"] = radar.apply(
    lambda row: (
        ((row["Tempo_mediano_ore_prec"] - row["Tempo_mediano_ore"]) / row["Tempo_mediano_ore_prec"]) * 100
        if pd.notna(row["Tempo_mediano_ore_prec"])
        and row["Tempo_mediano_ore_prec"] != 0
        and pd.notna(row["Tempo_mediano_ore"])
        else pd.NA
    ),
    axis=1,
)

st.divider()
st.subheader("🔎 Esplora una categoria")

categories = (
    radar
    .sort_values("Venduti", ascending=False)["category"]
    .tolist()
)

selected_category = st.selectbox(
    "Categoria",
    categories,
)

detail = current[current["category"] == selected_category].copy()
detail_prev = previous[previous["category"] == selected_category].copy()

if detail.empty:
    st.info("Nessun dato disponibile per questa categoria.")
    st.stop()

detail_row = radar[radar["category"] == selected_category].iloc[0]

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "📦 Venduti",
        int(detail_row["Venduti"]),
        format_delta(detail_row["Trend_volume_%"]),
    )

with c2:
    st.metric(
        "💰 Prezzo mediano",
        format_price(detail_row["Prezzo_mediano"]),
        format_delta(detail_row["Trend_prezzo_%"]),
    )

with c3:
    st.metric(
        "⚡ Tempo mediano",
        format_speed(detail_row["Tempo_mediano_ore"]),
        format_delta(detail_row["Trend_velocita_%"]) + " velocità"
        if pd.notna(detail_row["Trend_velocita_%"])
        else "-",
    )

with c4:
    st.metric(
        "🧩 Famiglie rilevate",
        detail["Famiglia"].nunique(),
    )


st.markdown("### 🧩 Brand / famiglie / modelli")

family_current = (
    detail
    .groupby("Famiglia")
    .agg(
        Venduti=("id", "count"),
        Prezzo_mediano=("price", "median"),
        Tempo_mediano_ore=("sale_time_hours", "median"),
    )
    .reset_index()
)

family_previous = (
    detail_prev
    .groupby("Famiglia")
    .agg(
        Venduti_prec=("id", "count"),
        Prezzo_mediano_prec=("price", "median"),
    )
    .reset_index()
    if not detail_prev.empty
    else pd.DataFrame(
        columns=[
            "Famiglia",
            "Venduti_prec",
            "Prezzo_mediano_prec",
        ]
    )
)

family_stats = family_current.merge(
    family_previous,
    on="Famiglia",
    how="left",
)

family_stats["Venduti_prec"] = family_stats["Venduti_prec"].fillna(0)

family_stats["Trend_volume_%"] = family_stats.apply(
    lambda row: (
        ((row["Venduti"] - row["Venduti_prec"]) / row["Venduti_prec"]) * 100
        if row["Venduti_prec"] > 0
        else pd.NA
    ),
    axis=1,
)

family_stats["Prezzo"] = family_stats["Prezzo_mediano"].apply(format_price)
family_stats["Tempo vendita"] = family_stats["Tempo_mediano_ore"].apply(format_speed)
family_stats["Trend 30 gg"] = family_stats["Trend_volume_%"].apply(format_delta)

family_stats = family_stats.sort_values(
    ["Venduti", "Tempo_mediano_ore"],
    ascending=[False, True],
)

family_table = family_stats[
    [
        "Famiglia",
        "Venduti",
        "Trend 30 gg",
        "Prezzo",
        "Tempo vendita",
    ]
].reset_index(drop=True)

family_event = st.dataframe(
    family_table,
    width="stretch",
    hide_index=True,
    height=420,
    on_select="rerun",
    selection_mode="single-row",
)

selected_rows = []
if family_event is not None:
    try:
        selected_rows = family_event.selection.rows
    except Exception:
        selected_rows = []

if selected_rows:
    selected_family = family_table.iloc[selected_rows[0]]["Famiglia"]

    st.caption(f"📌 Selezionato: **{selected_family}**")

    selected_family_data = detail[
        detail["Famiglia"] == selected_family
    ].copy()

    famiglia_venduti = len(selected_family_data)
    famiglia_prezzo_medio = selected_family_data["price"].mean()
    famiglia_prezzo_mediano = selected_family_data["price"].median()
    famiglia_tempo_mediano = selected_family_data["sale_time_hours"].median()

    fk1, fk2, fk3, fk4 = st.columns(4)

    with fk1:
        st.metric(
            "📦 Venduti",
            famiglia_venduti,
        )

    with fk2:
        st.metric(
            "💰 Prezzo medio",
            format_price(famiglia_prezzo_medio),
        )

    with fk3:
        st.metric(
            "🎯 Prezzo mediano",
            format_price(famiglia_prezzo_mediano),
        )

    with fk4:
        st.metric(
            "⚡ Tempo mediano",
            format_speed(famiglia_tempo_mediano),
        )

    st.markdown("#### 📈 Andamento prezzo")

    periodo_prezzo = st.segmented_control(
        "Periodo",
        options=[30, 60, 90],
        default=30,
        format_func=lambda days: f"{days} giorni",
        key=f"price_period_{selected_family}",
    )

    if periodo_prezzo is None:
        periodo_prezzo = 30

    price_cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=periodo_prezzo)

    # Il grafico deve usare tutto lo storico disponibile della famiglia,
    # non il dataset "detail" già limitato agli ultimi 30 giorni.
    historical_family_data = df[
        (df["category"] == selected_category)
        & (df["Famiglia"] == selected_family)
    ].copy()

    price_history = historical_family_data[
        historical_family_data["detected_sold_at"] >= price_cutoff
    ].copy()

    if not price_history.empty:
        price_history["Giorno"] = (
            price_history["detected_sold_at"]
            .dt.tz_convert("Europe/Rome")
            .dt.date
        )

        daily_price = (
            price_history.groupby("Giorno", as_index=False)
            .agg(
                Prezzo_mediano=("price", "median"),
                Prezzo_medio=("price", "mean"),
                Venduti=("price", "count"),
            )
            .sort_values("Giorno")
        )

        st.line_chart(
            daily_price.set_index("Giorno")[["Prezzo_mediano"]],
            x_label="Giorno",
            y_label="Prezzo mediano (€)",
            height=320,
        )

        p1, p2, p3 = st.columns(3)

        with p1:
            st.metric(
                f"🎯 Mediana {periodo_prezzo}g",
                format_price(price_history["price"].median()),
            )

        with p2:
            st.metric(
                f"💰 Media {periodo_prezzo}g",
                format_price(price_history["price"].mean()),
            )

        with p3:
            st.metric(
                f"📦 Venduti {periodo_prezzo}g",
                len(price_history),
            )

        st.caption(
            "Il grafico usa il prezzo mediano giornaliero, "
            "più resistente agli annunci fuori mercato rispetto alla media."
        )
    else:
        st.info(
            f"Nessun venduto per {selected_family} "
            f"negli ultimi {periodo_prezzo} giorni."
        )

    family_listings = (
        selected_family_data
        .sort_values(
            "detected_sold_at",
            ascending=False,
        )
        .copy()
    )

    if selected_family != "Altro / non riconosciuto":
        family_listings = family_listings.head(50).copy()

    family_listings["Prezzo"] = family_listings["price"].apply(format_price)
    family_listings["Venduto in"] = family_listings["sale_time_hours"].apply(format_speed)
    family_listings["Rilevato venduto"] = (
        family_listings["detected_sold_at"]
        .dt.tz_convert("Europe/Rome")
        .dt.strftime("%d/%m/%Y %H:%M")
        .fillna("-")
    )

    family_listings = family_listings.rename(
        columns={
            "title": "Titolo",
            "url": "Link",
        }
    )

    rows = []
    for _, row in family_listings.iterrows():
        titolo = escape(str(row["Titolo"]))
        prezzo = escape(str(row["Prezzo"]))
        venduto_in = escape(str(row["Venduto in"]))
        rilevato = escape(str(row["Rilevato venduto"]))
        link = str(row["Link"]).strip() if pd.notna(row["Link"]) else ""

        if link.startswith("http://") or link.startswith("https://"):
            titolo_html = (
                f'<a href="{escape(link, quote=True)}" target="_blank" '
                f'style="font-weight:700;text-decoration:none">{titolo}</a>'
            )
        else:
            titolo_html = titolo

        rows.append(
            "<tr>"
            f"<td>{titolo_html}</td>"
            f"<td>{prezzo}</td>"
            f"<td>{venduto_in}</td>"
            f"<td>{rilevato}</td>"
            "</tr>"
        )

    st.markdown(
        """
        <div style="overflow-x:auto;max-height:520px;overflow-y:auto">
        <table style="width:100%;border-collapse:collapse">
            <thead>
                <tr>
                    <th style="text-align:left;padding:10px">Titolo</th>
                    <th style="text-align:left;padding:10px">Prezzo</th>
                    <th style="text-align:left;padding:10px">Venduto in</th>
                    <th style="text-align:left;padding:10px">Rilevato venduto</th>
                </tr>
            </thead>
            <tbody>
        """
        + "".join(rows)
        + """
            </tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.divider()
st.subheader(f"📈 Trend giornaliero — {selected_category}")

daily = detail.copy()
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

if not daily_sales.empty:
    st.line_chart(
        daily_sales,
        x="Giorno",
        y="Venduti",
        width="stretch",
    )
else:
    st.info("Dati insufficienti per il grafico.")


st.subheader("📡 Mercato negli ultimi 30 giorni")

prev_count = len(previous)
current_count = len(current)

volume_delta = (
    ((current_count - prev_count) / prev_count) * 100
    if prev_count > 0
    else pd.NA
)

current_median_price = current["price"].median()
previous_median_price = previous["price"].median()

price_delta = (
    ((current_median_price - previous_median_price) / previous_median_price) * 100
    if pd.notna(previous_median_price) and previous_median_price != 0
    else pd.NA
)

current_speed = current["sale_time_hours"].median()
previous_speed = previous["sale_time_hours"].median()

speed_delta = (
    ((current_speed - previous_speed) / previous_speed) * 100
    if pd.notna(previous_speed) and previous_speed != 0
    else pd.NA
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Venduti 30 gg",
        f"{current_count:,}".replace(",", "."),
        format_delta(volume_delta),
    )

with col2:
    st.metric(
        "💰 Prezzo mediano",
        format_price(current_median_price),
        format_delta(price_delta),
    )

with col3:
    delta_speed_label = (
        f"{speed_delta:+.1f}% tempo"
        if pd.notna(speed_delta)
        else "-"
    )
    st.metric(
        "⚡ Tempo mediano",
        format_speed(current_speed),
        delta_speed_label,
        delta_color="inverse",
    )

with col4:
    st.metric(
        "🏷️ Categorie attive",
        current["category"].nunique(),
    )

st.caption(
    "Le variazioni confrontano gli ultimi 30 giorni con i 30 giorni precedenti. "
    "Per il tempo di vendita, una variazione negativa indica una rotazione più veloce."
)


st.divider()
st.subheader("🏷️ Radar categorie")

def market_signal(row):
    signals = 0

    if pd.notna(row["Trend_volume_%"]) and row["Trend_volume_%"] >= 10:
        signals += 1

    if pd.notna(row["Trend_velocita_%"]) and row["Trend_velocita_%"] >= 10:
        signals += 1

    if row["Venduti"] >= max(5, current_cat["Venduti"].median()):
        signals += 1

    if signals >= 3:
        return "🟢 Forte"

    if signals == 2:
        return "🟡 Interessante"

    return "⚪ Da osservare"


radar["Segnale"] = radar.apply(market_signal, axis=1)

radar_display = radar.copy()
radar_display["Prezzo mediano"] = radar_display["Prezzo_mediano"].apply(format_price)
radar_display["Tempo mediano"] = radar_display["Tempo_mediano_ore"].apply(format_speed)
radar_display["Trend venduti"] = radar_display["Trend_volume_%"].apply(format_delta)
radar_display["Trend prezzo"] = radar_display["Trend_prezzo_%"].apply(format_delta)
radar_display["Velocità vs prec."] = radar_display["Trend_velocita_%"].apply(format_delta)

radar_display = radar_display.rename(
    columns={
        "category": "Categoria",
    }
)

st.dataframe(
    radar_display[
        [
            "Categoria",
            "Venduti",
            "Trend venduti",
            "Prezzo mediano",
            "Trend prezzo",
            "Tempo mediano",
            "Velocità vs prec.",
            "Segnale",
        ]
    ].sort_values("Venduti", ascending=False),
    width="stretch",
    hide_index=True,
    height=500,
)

st.caption(
    "Il segnale sintetico non stima il profitto: evidenzia categorie con combinazione di volume, crescita e velocità di vendita."
)


st.divider()
st.subheader("🔥 Cosa sta girando di più")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Più venduti negli ultimi 30 giorni**")

    top_volume = (
        radar_display[
            [
                "Categoria",
                "Venduti",
                "Trend venduti",
                "Prezzo mediano",
            ]
        ]
        .sort_values("Venduti", ascending=False)
        .head(10)
    )

    st.dataframe(
        top_volume,
        width="stretch",
        hide_index=True,
    )

with col2:
    st.markdown("**Rotazione più veloce**")

    top_speed = (
        radar[
            radar["Tempo_mediano_ore"].notna()
        ][
            [
                "category",
                "Venduti",
                "Tempo_mediano_ore",
                "Trend_velocita_%",
            ]
        ]
        .sort_values(
            ["Tempo_mediano_ore", "Venduti"],
            ascending=[True, False],
        )
        .head(10)
        .copy()
    )

    top_speed["Tempo mediano"] = top_speed["Tempo_mediano_ore"].apply(format_speed)
    top_speed["Velocità vs prec."] = top_speed["Trend_velocita_%"].apply(format_delta)
    top_speed = top_speed.rename(columns={"category": "Categoria"})

    st.dataframe(
        top_speed[
            [
                "Categoria",
                "Venduti",
                "Tempo mediano",
                "Velocità vs prec.",
            ]
        ],
        width="stretch",
        hide_index=True,
    )


