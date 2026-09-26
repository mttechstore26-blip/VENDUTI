import re
from functools import lru_cache
from html import escape

import pandas as pd
import streamlit as st

from data_cache import load_market_data


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


@lru_cache(maxsize=20000)
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
        .replace("poket", "pocket")
        .replace("petnax", "pentax")
        .replace("zhyun", "zhiyun")
        .replace("mimi mavic", "mini mavic")
        .replace("go pro", "gopro")
        .replace("mac book", "macbook")
        .replace("compiuter", "computer")
        .replace("insta 360", "insta360")
        .replace("metà", "meta")
        .replace("iohone", "iphone")
        .replace("i phone", "iphone")
        .replace("readmi", "redmi")
        .replace("hawei", "huawei")
        .replace("asuz", "asus")
    )
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Corregge typo iPhone solo come parole intere.
    # Importante: non usare str.replace("iphon", "iphone"),
    # perché trasformerebbe anche "iphone" corretto in "iphonee".
    text = re.sub(r"\biphonee\b", "iphone", text)
    text = re.sub(r"\biphon\b", "iphone", text)

    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=50000)
def detect_family(title, category=None):
    text = normalize_text(title)
    category_text = normalize_text(category or "")

    # iPhone: parser robusto che ignora memoria, colore e formattazioni del titolo.
    # Gestisce anche forme come iphone13, iphone 11pro, iphone 14promax, 16e, X/XS e SE.
    if re.search(r"\biphone", text):
        # Modelli speciali.
        if re.search(r"\biphone\s*se\s*(?:3|3a|3rd)?\b", text):
            return "iPhone SE 3"
        if re.search(r"\biphone\s*xs\b", text):
            return "iPhone XS"
        if re.search(r"\biphone\s*x\b", text):
            return "iPhone X"
        if re.search(r"\biphone\s*2g\b", text):
            return "iPhone 2G"
        if re.search(r"\biphone\s*16e\b", text):
            return "iPhone 16e"

        # Generazioni moderne, anche senza spazio: iphone13, iphone12pro, 14promax...
        iphone_modern = re.search(
            r"\biphone\s*(11|12|13|14|15|16|17)"
            r"\s*(pro\s*max|promax|pro|max|plus)?\b",
            text,
        )
        if iphone_modern:
            generation, variant = iphone_modern.groups()
            if variant:
                variant = variant.replace("promax", "pro max")
                if variant == "max":
                    variant = "Pro Max"
                elif variant == "pro max":
                    variant = "Pro Max"
                else:
                    variant = variant.title()
                return f"iPhone {generation} {variant}"
            return f"iPhone {generation}"

        # Modelli precedenti.
        legacy = re.search(r"\biphone\s*(8|7|6)\b", text)
        if legacy:
            return f"iPhone {legacy.group(1)}"

        # Titolo iPhone senza modello identificabile.
        return "iPhone • Modello non identificato"

    if re.search(r"\b(?:ps|playstation)\s*portal\b", text):
        return "PlayStation Portal"

    console_patterns = [
        # PlayStation 5: per il sourcing raggruppiamo per generazione hardware.
        # Digital / disco della PS5 base confluiscono in PS5.
        # Digital / disco della Slim confluiscono in PS5 Slim.
        (r"\b(?:ps5|playstation\s*5)\b.*\bpro\b", "PS5 Pro"),
        (r"\b(?:ps5|playstation\s*5)\b.*\bslim\b", "PS5 Slim"),
        (r"\bps5\b|\bplaystation\s*5\b", "PS5"),
        (r"\b(?:ps4|playstation\s*4)\b.*\bpro\b", "PS4 Pro"),
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

    # iPad: separa generazioni/modelli e non confonde gli accessori.
    if re.search(r"\bipad\b", text):
        if re.search(r"\bmagic\s+keyboard\b", text):
            return "iPad • Accessori"

        if re.search(r"\bipad\s+pro\b", text):
            return "iPad Pro"
        if re.search(r"\bipad\s+air\b", text):
            return "iPad Air"
        if re.search(r"\bipad\s+mini\b", text):
            return "iPad mini"

        # iPad A16 (modello base 2025)
        if re.search(r"\bipad\s+a16\b", text):
            return "iPad A16"

        # Varianti testuali: 10 gen, 10th, 10ª generazione, ecc.
        generation_patterns = [
            (10, r"\bipad\b.*\b(?:10|10th|10a|10o)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b10\s*(?:gen|generazione|generation)\b"),
            (9, r"\bipad\b.*\b(?:9|9th|9a|9o|nove)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b9\s*(?:gen|generazione|generation)\b"),
            (8, r"\bipad\b.*\b(?:8|8th|8a|8o)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b8\s*(?:gen|generazione|generation)\b"),
            (7, r"\bipad\b.*\b(?:7|7th|7a|7o)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b7\s*(?:gen|generazione|generation)\b"),
            (6, r"\bipad\b.*\b(?:6|6th|6a|6o)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b6\s*(?:gen|generazione|generation)\b"),
            (5, r"\bipad\b.*\b(?:5|5th|5a|5o)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b5\s*(?:gen|generazione|generation)\b"),
            (4, r"\bipad\b.*\b(?:4|4th|4a|4o)\b(?:\s*(?:gen|generazione|generation))?|\bipad\b.*\b4\s*(?:gen|generazione|generation)\b"),
        ]
        for generation, pattern in generation_patterns:
            if re.search(pattern, text):
                return f"iPad {generation}ª gen"

        return "iPad • Modello non identificato"

    # MacBook Air: separa per chip quando possibile, altrimenti per anno.
    if re.search(r"\bmacbook\s*air\b", text):
        for chip in ["m4", "m3", "m2", "m1"]:
            if re.search(rf"\b{chip}\b", text):
                return f"MacBook Air {chip.upper()}"

        year_match = re.search(
            r"\bmacbook\s*air\b.*\b(2015|2016|2017|2018|2019|2020|2021|2022|2023|2024|2025|2026)\b",
            text,
        )
        if year_match:
            return f"MacBook Air {year_match.group(1)}"

        # Alcuni titoli mettono l'anno prima o lontano dal nome prodotto.
        any_year = re.search(
            r"\b(2015|2016|2017|2018|2019|2020|2021|2022|2023|2024|2025|2026)\b",
            text,
        )
        if any_year:
            return f"MacBook Air {any_year.group(1)}"

        return "MacBook Air • Modello non identificato"

    apple_patterns = [
        (r"\bmacbook\s*pro\b", "MacBook Pro"),
        (r"\bimac\b", "iMac"),
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

    # Telefonia: modelli e famiglie utili al sourcing.
    if "telefonia" in category_text:
        phone_patterns = [
            # Google Pixel
            (r"\b(?:google\s+)?pixel\s*(10|9|8|7|6)(?:\s*(pro|pro\s+xl|xl|a))?\b", "Google Pixel"),

            # Xiaomi / Redmi / Poco
            (r"\bxiaomi\s*(15|14|13|12|11)(?:\s*(ultra|pro|lite|t|t\s+pro))?\b", "Xiaomi"),
            (r"\bredmi\s+note\s*(\d{1,2})(?:\s*(pro\+?|pro|s|5g))?\b", "Xiaomi Redmi Note"),
            (r"\bredmi\s*(\d{1,2})(?:\s*(c|a|note|pro|5g))?\b", "Xiaomi Redmi"),
            (r"\bpoco\s*(x|f|m|c)\s*(\d{1,2})(?:\s*(pro|ultra|gt))?\b", "POCO"),

            # OnePlus / Nothing
            (r"\boneplus\s*(\d{1,2})(?:\s*(pro|r|t))?\b", "OnePlus"),
            (r"\bnothing\s+phone\s*\(?\s*(\d[a-z]?)\s*\)?\b", "Nothing Phone"),
            (r"\bcmf\s+phone\s*(\d+)\b", "CMF Phone"),

            # Motorola
            (r"\bmotorola\s+edge\s*(\d{1,2})(?:\s*(pro|neo|fusion|ultra))?\b", "Motorola Edge"),
            (r"\bmoto\s+g\s*(\d{1,3})(?:\s*(power|stylus|5g))?\b", "Motorola Moto G"),
            (r"\bmotorola\s+razr\s*(\d{2})?(?:\s*(ultra|plus))?\b", "Motorola Razr"),

            # Honor / Huawei
            (r"\bhonor\s*(magic\s*\d+|\d{2,3})(?:\s*(pro|lite))?\b", "Honor"),
            (r"\bhuawei\s+(p|mate)\s*(\d{2,3})(?:\s*(pro|lite))?\b", "Huawei"),

            # OPPO / Realme
            (r"\boppo\s+(find\s+[a-z]\d+|reno\s*\d+|a\d{2,3})(?:\s*(pro|lite|neo))?\b", "OPPO"),
            (r"\brealme\s*(gt\s*\d+|\d{1,2})(?:\s*(pro|plus|neo))?\b", "Realme"),

            # Sony Xperia / Nokia / Asus
            (r"\bsony\s+xperia\s*(1|5|10)(?:\s*(ii|iii|iv|v|vi))?\b", "Sony Xperia"),
            (r"\bnokia\s+([a-z]?\d{1,3})(?:\s*(plus|5g))?\b", "Nokia"),
            (r"\basus\s+zenfone\s*(\d{1,2})\b", "ASUS Zenfone"),
            (r"\basus\s+rog\s+phone\s*(\d{1,2})\b", "ASUS ROG Phone"),
        ]

        for pattern, brand in phone_patterns:
            match = re.search(pattern, text)
            if match:
                groups = [g for g in match.groups() if g]
                model = " ".join(groups)
                model = re.sub(r"\s+", " ", model).strip()
                return f"{brand} {model}".strip()

        # Samsung Fold / Flip possono non seguire il parser Galaxy numerico.
        samsung_fold = re.search(
            r"\b(?:samsung\s+)?galaxy\s+z\s*(fold|flip)\s*(\d{1,2})\b",
            text,
        )
        if samsung_fold:
            kind, generation = samsung_fold.groups()
            return f"Samsung Galaxy Z {kind.title()} {generation}"

        # Wearable e telefoni semplici che ricorrono spesso in Telefonia.
        if re.search(r"\bapple\s+watch\s+(ultra\s*\d*|series\s*\d+|se)\b", text):
            watch = re.search(
                r"\bapple\s+watch\s+(ultra\s*\d*|series\s*\d+|se)\b",
                text,
            )
            return f"Apple Watch {watch.group(1).title()}"

        if re.search(r"\bgalaxy\s+watch\s*(\d+|ultra|classic)\b", text):
            watch = re.search(r"\bgalaxy\s+watch\s*(\d+|ultra|classic)\b", text)
            return f"Samsung Galaxy Watch {watch.group(1).title()}"

        if re.search(r"\bsmartwatch\b", text):
            return "Smartwatch"

        if re.search(r"\btelefono\s+fisso\b|\bcordless\b", text):
            return "Telefoni fissi / Cordless"

        if re.search(r"\bcover\b|\bcustodia\b|\bpellicola\b|\bcaricatore\b|\bcharger\b", text):
            return "Accessori telefonia"

    if "telefonia" in category_text:
        # Samsung scritti senza Galaxy.
        samsung_short = re.search(
            r"\b(?:samsung\s+)?s\s*(2[0-9])(?:\s*(ultra|plus|fe))?\b",
            text,
        )
        if samsung_short:
            model, variant = samsung_short.groups()
            label = f"Samsung Galaxy S{model}"
            if variant:
                label += f" {variant.title() if variant != 'fe' else 'FE'}"
            return label

        if re.search(r"\bz\s*flip\s*4\b", text):
            return "Samsung Galaxy Z Flip 4"
        if re.search(r"\bgalaxy\s+xcover\s*7\b", text):
            return "Samsung Galaxy XCover 7"

        # Brand/modelli meno comuni presenti nei dati reali.
        uncommon_phone_patterns = [
            (r"\binfinix\s+note\s*50\s*pro\b", "Infinix Note 50 Pro"),
            (r"\btcl\s+p80\s+pro\b", "TCL P80 Pro"),
            (r"\btcl\s+70\s+pro\s+next\s*paper\b", "TCL 70 Pro NXTPAPER"),
            (r"\bhotwav\s+t8\b", "Hotwav T8"),
            (r"\bred\s+magic\s*6\s*pro\b", "RedMagic 6 Pro"),
            (r"\bdoogee\s+v\s*max\s+plus\b", "Doogee V Max Plus"),
            (r"\bsharp\s+aquos\s+r8\s+pro\b", "Sharp Aquos R8 Pro"),
            (r"\bunihertz\s+jelly\s+star\b", "Unihertz Jelly Star"),
            (r"\bblackview\s+xplore\s*1\b", "Blackview Xplore 1"),
            (r"\bnubia\s+z60s\s+pro\b", "Nubia Z60S Pro"),
            (r"\bnubia\s+air\b", "Nubia Air"),
        ]
        for pattern, label in uncommon_phone_patterns:
            if re.search(pattern, text):
                return label

        # Redmi typo già normalizzato.
        redmi_note = re.search(
            r"\bredmi\s+note\s*(\d{1,2})(?:\s*(pro\+?|pro|s|5g))?\b",
            text,
        )
        if redmi_note:
            model, variant = redmi_note.groups()
            label = f"Xiaomi Redmi Note {model}"
            if variant:
                label += f" {variant.upper() if variant == '5g' else variant.title()}"
            return label

        # Wearable / audio / smart glasses.
        if re.search(r"\bairpods\s+pro\s*3\b", text):
            return "AirPods Pro 3"
        if re.search(r"\bamazfit\s+t[\s-]*rex\s*3\b|\bt[\s-]*rex\s*3\s+amazfit\b", text):
            return "Amazfit T-Rex 3"
        if re.search(r"\bhuawei\s+gt6\s+pro\b", text):
            return "Huawei Watch GT 6 Pro"
        if re.search(r"\bultra\s*3\b", text):
            return "Apple Watch Ultra 3"
        if re.search(r"\brayneo\s+air\s*4\s+pro\b", text):
            return "RayNeo Air 4 Pro"
        if re.search(r"\bvyda\b", text):
            return "VYDA"

        # Router / modem 5G che finiscono nella categoria Telefonia.
        if re.search(r"\bnokia\s+fastmile\s*5g\b", text):
            return "Nokia FastMile 5G"
        if re.search(r"\bzte\s+mc889\b", text):
            return "ZTE MC889 5G"

        # Domotica / touchscreen presenti impropriamente in Telefonia.
        if re.search(r"\bbticino\s+3488\b", text):
            return "BTicino 3488"

        # OnePlus scritto staccato senza modello.
        if re.search(r"\bone\s+plus\b", text):
            return "OnePlus • Modello non identificato"

        # iPhone generici o lotti restano volutamente separati dal modello specifico.
        if re.search(r"\bdue\s+iphone\b|\btelefoni\s+iphone\b", text):
            return "iPhone • Lotto / Accessori"
        if re.fullmatch(r"iphone", text):
            return "iPhone • Modello non identificato"

    insta360 = re.search(
        r"\binsta\s*360\s+(go\s*\d+[a-z]?|x\s*\d+|ace\s*pro\s*\d*|one\s*[a-z0-9]+)(?:\s+\d{2,4}gb)?\b",
        text,
    )
    if insta360:
        model = insta360.group(1)
        model = re.sub(r"\s+", " ", model).strip()
        return f"Insta360 {model.upper() if model.startswith('x') else model.title()}"

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

    if re.search(r"\bgopro\s+(?:hero\s+)?max\b", text):
        return "GoPro MAX"

    gopro = re.search(
        r"\bgopro(?:\s+hero)?\s*(\d{1,2})(?:\s+(?:black|silver|white))?\b",
        text,
    )
    if gopro:
        generation = gopro.group(1)
        return f"GoPro Hero {generation}"

    # Fotografia: riconoscimento marca + modello reale.
    # Canon EOS 2000D può comparire anche senza la parola "Canon" nel titolo.
    # Il codice modello 2000D identifica la Canon EOS 2000D.
    if re.search(r"\b2000d\b", text):
        return "Canon 2000D"

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

    # Altri sistemi fotografici / video comuni
    photo_product_patterns = [
        # DJI: action cam, pocket, droni e gimbal
        (r"\bdji\s+osmo\s+pocket\s*(\d+)?\b", "DJI Osmo Pocket"),
        (r"\bdji\s+osmo\s+action\s*(\d+)?\b", "DJI Osmo Action"),
        (r"\bdji\s+(?:drone\s+)?mini\s*(\d+\s*pro|\d+|se)?\b", "DJI Mini"),
        (r"\bdji\s+(?:drone\s+)?mavic\s+([a-z0-9\s]+?)(?=\s+(?:combo|fly|con|piu|\+)|$)", "DJI Mavic"),
        (r"\bdji\s+(?:drone\s+)?avata\s*(\d+)?\b", "DJI Avata"),
        (r"\bdji\s+neo\s*2\b", "DJI Neo 2"),
        (r"\bdji\s+neo\b", "DJI Neo"),
        (r"\bdji\s+rs\s*(\d+)\s*(mini|pro)?\b", "DJI RS"),

        # Panasonic / Olympus / Pentax / Leica
        (r"\b(?:panasonic\s+)?lumix\s+([a-z]{1,3}\d+[a-z0-9\-]*)\b", "Panasonic Lumix"),
        (r"\bpanasonic\s+([a-z]{1,3}\d+[a-z0-9\-]*)\b", "Panasonic"),
        (r"\bolympus\s+(?:om[\-\s]?d\s+)?([a-z]{1,3}[\-\s]?\d+[a-z0-9]*)\b", "Olympus"),
        (r"\bom\s*system\s+([a-z0-9\-]+)\b", "OM System"),
        (r"\bpentax\s+([a-z]{1,3}[\-\s]?\d+[a-z0-9]*)\b", "Pentax"),
        (r"\bleica\s+([qmstdcl][a-z0-9\-]*)\b", "Leica"),
    ]

    for pattern, brand in photo_product_patterns:
        match = re.search(pattern, text)
        if match:
            groups = [g for g in match.groups() if g]
            suffix = " ".join(groups)
            suffix = re.sub(r"\s+", " ", suffix).strip().upper()
            return f"{brand}{(' ' + suffix) if suffix else ''}"

    # Obiettivi: raggruppa per marca + focale/zoom, molto più utile della sola marca.
    # Esempi: "Canon EF 50mm", "Sigma 18-35mm", "Tamron 70-300mm".
    lens_brand_match = re.search(
        r"\b(canon|nikon|nikkor|sony|sigma|tamron|samyang|tokina|viltrox)\b",
        text,
    )
    lens_focal_match = re.search(
        r"\b(\d{1,3}(?:[\-\s]?\d{1,3})?)\s*mm\b",
        text,
    )

    if lens_brand_match and lens_focal_match:
        raw_brand = lens_brand_match.group(1)
        brand_map = {
            "canon": "Canon",
            "nikon": "Nikon",
            "nikkor": "Nikon",
            "sony": "Sony",
            "sigma": "Sigma",
            "tamron": "Tamron",
            "samyang": "Samyang",
            "tokina": "Tokina",
            "viltrox": "Viltrox",
        }
        brand = brand_map[raw_brand]
        focal = re.sub(r"\s+", "-", lens_focal_match.group(1))
        focal = focal.replace("--", "-")
        return f"{brand} {focal}mm"

    # Fotografia: famiglie/modelli aggiuntivi ricavati dai titoli reali
    extra_photo_patterns = [
        (r"\bpolaroid\s+sx[\-\s]?70\b", "Polaroid SX-70"),
        (r"\bmamiya\s+universal\b", "Mamiya Universal"),
        (r"\bhorizon\s+202\b", "Horizon 202"),
        (r"\bseestar\s+s30\b", "Seestar S30"),
        (r"\bminox\s+35\s*ml\b", "Minox 35 ML"),
        (r"\batomos\s+shinobi\s*(ii|2)?\b", "Atomos Shinobi"),
        (r"\btour\s*box\s+neo\b", "TourBox Neo"),
        (r"\bzhiyun\s+crane\s*3s\b", "Zhiyun Crane 3S"),
        (r"\bricoh\s+wg[\-\s]?6\b", "Ricoh WG-6"),
        (r"\bricoh\s+theta\s+v\b", "Ricoh Theta V"),
        (r"\bricoh\s+gr\s*(ii|2)\b", "Ricoh GR II"),
        (r"\bricoh\s+gr1\b", "Ricoh GR1"),
        (r"\bcontax\s+t2\b", "Contax T2"),
        (r"\brolleicord\b", "Rolleicord"),
        (r"\brollei\s+35\s*se\b", "Rollei 35 SE"),
        (r"\bkodak\s+pixpro\s+fz55\b", "Kodak Pixpro FZ55"),
        (r"\bautel\s+evo\s+nano\s+plus\b", "Autel Evo Nano+"),
        (r"\bfimi\s+x8\s+se\b", "FIMI X8 SE"),
        (r"\bgarmin\s+virb\s+ultra\s*30\b", "Garmin Virb Ultra 30"),
        (r"\bflir\s+one\s+pro\b", "FLIR One Pro"),
        (r"\bzwo\s+asiair\s+plus\b", "ZWO ASIAIR Plus"),
        (r"\bsinar\s+p\s+4x5\b", "Sinar P 4x5"),
        (r"\barax\s+60|\bkiev\s+60\b", "Arax/Kiev 60"),
        (r"\bcanonet\s+ql17\s+giii\b", "Canonet QL17 GIII"),
        (r"\btopcon\s+re2\b", "Topcon RE2"),
        (r"\bgodox\s+tl60\b", "Godox TL60"),
        (r"\bgodox\s+dp600iii[\-\s]?v\b", "Godox DP600III-V"),
        (r"\baputure\s+mc\s+pro\b", "Aputure MC Pro"),
        (r"\bneewer\s+nl660\b", "Neewer NL660"),
        (r"\bmetabones\s+iv\b", "Metabones IV"),
        (r"\bsmallrig\s+vb99\b", "SmallRig VB99"),
        (r"\btilta\s+nucleus\s+nano\b", "Tilta Nucleus Nano"),
        (r"\bsky[\-\s]?watcher\s+star\s+adventurer\b", "Sky-Watcher Star Adventurer"),
        (r"\bgossen\s+sinar\s+six\b", "Gossen Sinar Six"),
        (r"\bdurst\s+601\b", "Durst 601"),
        (r"\blab[\-\s]?box\b", "LAB-BOX"),
        (r"\bnisi\s+swift\b", "NiSi Swift"),
        (r"\bdivevolk\s+sea\s+touch\s+4\s+max\b", "Divevolk Sea Touch 4 Max"),
        (r"\bdavinci\s+studio\b", "DaVinci Resolve Studio"),
        (r"\bosmo\s+pocket\s*3\b", "DJI Osmo Pocket 3"),
        (r"\bosmo\s+action\s*4\b", "DJI Osmo Action 4"),
        (r"\bosmo\s+mobile\s+8p\b", "DJI Osmo Mobile 8P"),
        (r"\bosmo\s+nano\b", "DJI Osmo Nano"),
        (r"\bdji\s+spark\b", "DJI Spark"),
        (r"\bdji\s+ronin[\-\s]?s\b", "DJI Ronin-S"),
        (r"\bdji\s+fpv\s+remote\s+controller\s*3\b", "DJI FPV Remote Controller 3"),
        (r"\bdji\s+rc\b", "DJI RC"),
        (r"\binsta(?:360)?\s+flow\s+2\s+pro\b", "Insta360 Flow 2 Pro"),
        (r"\binsta(?:360)?\s+ace\s+pro\s*2\b", "Insta360 Ace Pro 2"),
        (r"\binsta(?:360)?\s+go\s+3\s*(?:e|/)?\s*3s\b", "Insta360 GO 3 / 3S"),
        (r"\bgopro\s+max\s*2\b|\bgopro\s+max2\b", "GoPro MAX 2"),
    ]

    for pattern, label in extra_photo_patterns:
        if re.search(pattern, text):
            return label

    # Nikon storiche / serie 1 / compatte nominate senza pattern moderni
    nikon_extra = [
        (r"\bnikon\s+1\s*j1\b", "Nikon 1 J1"),
        (r"\bnikon\s+v1\b", "Nikon 1 V1"),
        (r"\bnikon\s+fe[\-\s]?2\b", "Nikon FE-2"),
        (r"\bnikon\s+f\s*501\b", "Nikon F501"),
        (r"\bnikon\s+f2\b", "Nikon F2"),
        (r"\bnikon\s+f\b", "Nikon F"),
        (r"\bnikon\s+p7800\b", "Nikon P7800"),
        (r"\bnikon\s+d[t]?7100\b", "Nikon D7100"),
    ]
    for pattern, label in nikon_extra:
        if re.search(pattern, text):
            return label

    # Canon compatte / bridge nominate senza PowerShot/IXUS
    canon_extra = [
        (r"\bcanon\s+s120\b", "Canon S120"),
        (r"\bcanon\s+sx60\b", "Canon SX60"),
    ]
    for pattern, label in canon_extra:
        if re.search(pattern, text):
            return label

    # Sony modelli scritti in forme più colloquiali
    sony_extra = [
        (r"\bsony\s+serie\s+a\s*5000\b", "Sony A5000"),
        (r"\bsony\s+fx3\b", "Sony FX3"),
        (r"\bsony\s+fx30\b", "Sony FX30"),
    ]
    for pattern, label in sony_extra:
        if re.search(pattern, text):
            return label

    # Obiettivi senza 'mm' ma con focale chiaramente espressa
    lens_loose = [
        (r"\b(nikkor|nikon)\s+(24[\-\s]120)\b", "Nikon"),
        (r"\b(tokina).*?(11[\-\s]16)\b", "Tokina"),
        (r"\b(sigma)\s+(105)\s+2[.,]8\b", "Sigma"),
        (r"\b(samyang)\s+(14)\s+f?\s*2[.,]8\b", "Samyang"),
        (r"\b(sigma).*?\b(20)\s+1[.,]8\b", "Sigma"),
        (r"\b(sigma)\s*30\s*mm\b", "Sigma"),
        (r"\b(lumix)\s+(14[\-\s]140)\b", "Panasonic Lumix"),
        (r"\b(komura)\s+(47)\s*mm\b", "Komura"),
        (r"\b(rodenstock).*?\b(80)\s*mm\b", "Rodenstock"),
        (r"\b(takumar).*?\b(90)\s*mm\b", "Takumar"),
        (r"\b(leitz|summicron).*?\b(50)r?\b", "Leica Summicron"),
    ]
    for pattern, brand in lens_loose:
        match = re.search(pattern, text)
        if match:
            nums = [g for g in match.groups() if g and re.search(r"\d", g)]
            focal = nums[-1] if nums else ""
            focal = re.sub(r"\s+", "-", focal)
            return f"{brand} {focal}mm".strip()

    # Ultimo pass Fotografia: prodotti specifici rimasti in Altro
    final_photo_patterns = [
        (r"\blobotim\b", "Lobotim Timer"),
        (r"\bfototrappola\s+zeiss\b", "Zeiss Fototrappola"),
        (r"\bzaino\s+manfrotto\b", "Manfrotto Zaino"),
        (r"\bsony\s+upc\s*21\s*l\b", "Sony UPC-21L"),
        (r"\bdji\s+batteria.*\blito\b", "DJI Lito Batteria"),
        (r"\bnikon\s+z\s*40\s*mm\b", "Nikon Z 40mm"),
        (r"\bpentax\s+k[\-\s]?s2\b", "Pentax K-S2"),
        (r"\bnikon\s+md[\-\s]?4\b", "Nikon MD-4"),
        (r"\bcanon\s+charger\s+nc[\-\s]?e2\b", "Canon NC-E2"),
        (r"\bborsa\s+fotografica\s+ona\b", "ONA Borsa fotografica"),
        (r"\bteleprompter\s+x12.*\bneewer\b", "Neewer X12"),
        (r"\bhasselblad\s+filtro\s+uv\s+86\s*mm\b", "Hasselblad Filtro UV 86mm"),
        (r"\bnikon\s+mb\s*d18\b", "Nikon MB-D18"),
        (r"\bcanon\s+fd\s+300\s+f4\s+l\b", "Canon FD 300mm F4 L"),
        (r"\bzeiss\s+distagon\b", "Zeiss Distagon"),
        (r"\bmagicfiz\s+smallrig\b", "SmallRig MagicFIZ"),
        (r"\bsoligor.*\bspotmeter\b", "Soligor Spotmeter"),
        (r"\bsony\s+ecm[\-\s]?m1\b", "Sony ECM-M1"),
        (r"\bzwo\s+pe200\b|\bpe200\s+zwo\b", "ZWO PE200"),
        (r"\bprofoto\s+connect\s+pro\b", "Profoto Connect Pro"),
        (r"\bcanon\s+pixma\s+g550\b", "Canon PIXMA G550"),
        (r"\bmeade\b.*\boculari\b|\boculari\s+meade\b", "Meade Oculari"),
        (r"\batomos\s+accessory\s+kit\b", "Atomos Accessory Kit"),
        (r"\bvevor\b.*\bmicroscopio\b|\bmicroscopio\s+vevor\b", "VEVOR Microscopio"),
        (r"\bminolta\s+7s\b", "Minolta 7S"),
        (r"\bzeiss\s+ikon\s+super\s+ikonta\b", "Zeiss Ikon Super Ikonta"),
        (r"\bvideomic\s+pro\b", "Rode VideoMic Pro"),
        (r"\bdji\s+lito\s*1\s+rc[\-\s]?n3\b", "DJI Lito 1 RC-N3"),
        (r"\bmovmax\s+blade\s+arm\b", "MOVMAX Blade Arm"),
        (r"\bgopro\s+piu\s+accessori\b", "GoPro"),
        (r"\bnikon\s+reflex\s+d5500\b", "Nikon D5500"),
        (r"\bsony\s+55\s+1\s*8\b", "Sony 55mm F1.8"),
        (r"\bsigma.*\b20\s+1\s*8\b", "Sigma 20mm F1.8"),
        (r"\bcalumet\s+8x10\b", "Calumet 8x10"),
        (r"\bteleobiettivo\s+zeiss\s+2\s*35x\b", "Zeiss 2.35x"),
    ]
    for pattern, label in final_photo_patterns:
        if re.search(pattern, text):
            return label

    # Gruppi accessori utili quando il prodotto è chiaro ma manca un modello specifico.
    if re.search(r"\bobbiettiv[oi]\s+per\s+canon\b|\bobiettiv[oi]\s+per\s+canon\b", text):
        return "Canon Obiettivi"

    if re.search(r"\bdue\s+obiettivi\s+nikon\b|\bobbiettivi\s+nikon\b|\bobiettivi\s+nikon\b", text):
        return "Nikon Obiettivi"

    if re.search(r"\bstabilizzatore\s+gimbal\b|\bstabilizatore\s+gimbal\b", text):
        return "Gimbal / Stabilizzatore"

    # Collezionismo: famiglie utili per il sourcing.
    # Vini/champagne restano volutamente in "Altro / non riconosciuto".
    if "collezionismo" in category_text:
        # LEGO: sottofamiglie utili al sourcing.
        if re.search(r"\blego\b", text):
            lego_set = re.search(r"\blego\b.*?\b(\d{4,6})\b", text)

            if re.search(r"\btechnic\b", text):
                return "LEGO • Technic"
            if re.search(r"\bone\s*piece\b|\bonepiece\b", text):
                return "LEGO • One Piece"
            if re.search(r"\bharry\s+potter\b|\bhogwarts\b|\bgringotts\b", text):
                return "LEGO • Harry Potter"
            if re.search(r"\bmarvel\b|\bavengers\b|\bsanctum\s+sanctorum\b", text):
                return "LEGO • Marvel"
            if re.search(r"\bstar\s+wars\b|\byoda\b|\blightsaber\b", text):
                return "LEGO • Star Wars"
            if re.search(r"\bcastle\b|\bcastello\b|\bpirati\b|\bbarracuda\b|\bgaleone\b", text):
                return "LEGO • Castle / Pirati"
            if re.search(r"\bf1\b|\bferrari\b|\bmercedes\b|\baston\s+martin\b|\bauto\b", text):
                return "LEGO • Auto / F1"
            if re.search(r"\bminifig", text):
                return "LEGO • Minifigures"
            if re.search(r"\bvintage\b|\bspazio\b", text):
                return "LEGO • Vintage"

            if lego_set:
                return f"LEGO • Set {lego_set.group(1)}"

            return "LEGO • Altro"

        # Pokémon 30° anniversario: alcuni annunci non scrivono "Pokemon"
        # oppure usano "Pokémon" con accento. ETB + 30° / Primi Compagni
        # sono comunque riconoscibili in modo affidabile nella categoria Collezionismo.
        if (
            re.search(
                r"\b30\s*(?:th|o|°)?\s*annivers|\b30\s*esimo\b|"
                r"\btrentesimo\b|\bprimi\s+compagni\b",
                text,
            )
            and re.search(
                r"\betb\b|\bpokemon\b|\bpokémon\b|\bprimi\s+compagni\b|"
                r"\bpikachu\b|\bmew\b|\blugia\b|\bcharizard\b",
                text,
            )
        ):
            return "Pokémon • 30° Anniversario"

        # Pokémon / TCG: sottofamiglie utili al sourcing.
        pokemon_match = re.search(
            r"\bpokemon\b|\bpokémon\b|\bpoke\b|\bcharizard\b|\bblastoise\b|"
            r"\bmew\b|\bmewtwo\b|\blugia\b|\braichu\b|\bcelebi\b|"
            r"\bvictini\b|\bmoltres\b|\bespeon\b|\bbulbasaur\b|"
            r"\bsquirt|\bdragonite\b|\bdarkrai\b|\bzoroark\b",
            text,
        )

        if pokemon_match:
            # 1. Graded ha precedenza: PSA/BGS/GRAAD/AI grading ecc.
            if re.search(
                r"\bpsa\s*\d+(?:\.\d+)?\b|\bbgs\s*\d+(?:\.\d+)?\b|"
                r"\bgraad\s*\d+(?:\.\d+)?\b|\baigrading\s*\d+(?:\.\d+)?\b|"
                r"\bgradat[oa]\b|\bgrading\b",
                text,
            ):
                return "Pokémon • Graded"

            # 2. 30° anniversario come segmento dedicato.
            # Ha priorità sul sigillato: un ETB del 30° deve restare nel segmento anniversario.
            if re.search(
                r"\b30\s*(?:th|o|°)?\s*annivers|\b30\s*esimo\b|"
                r"\btrentesimo\b|\bprimi\s+compagni\b",
                text,
            ):
                return "Pokémon • 30° Anniversario"

            # 3. Sigillato: box, ETB, blister, booster, SPC e prodotti sealed.
            if re.search(
                r"\betb\b|\bbox\b|\bblister\b|\bbooster\b|"
                r"\bspc\b|\bsealed\b|\bsigillat|\bdisplay\b|"
                r"\bcollection\s+box\b|\bscatola\s+speciale\b",
                text,
            ):
                return "Pokémon • Sigillato"

            # 4. Vintage / set storici.
            if re.search(
                r"\bvintage\b|\b1st\s+edition\b|\bprima\s+edizione\b|"
                r"\bjungle\b|\bfossil\b|\bteam\s+rocket\b|"
                r"\bbase\s+set\b|\bphantom\s+forces\b",
                text,
            ):
                return "Pokémon • Vintage"

            # 5. Lotti / collezioni / set misti.
            if re.search(
                r"\blotto\b|\blotti\b|\bcollezion|\bset\s+carte\b|"
                r"\bcarte\s+assortite\b|\bcoppia\s+carte\b|"
                r"\bbinder\b|\braccoglitore\b",
                text,
            ):
                return "Pokémon • Lotti / Collezioni"

            # 6. Tutto il resto: singole carte.
            return "Pokémon • Carte singole"

        # Magic: The Gathering.
        if re.search(
            r"\bmtg\b|\bmagic\s+the\s+gathering\b|\bmystery\s+booster\b",
            text,
        ):
            return "Magic: The Gathering"

        if re.search(r"\bsubbuteo\b", text):
            return "Subbuteo"
        if re.search(r"\bskylanders\b", text):
            return "Skylanders"
        if re.search(r"\bbeyblade\b", text):
            return "Beyblade"
        if re.search(r"\bdungeon\s+(?:and|&)\s+dragons\b|\bd&d\b|\bdnd\b", text):
            return "Dungeons & Dragons"
        if re.search(r"\bwarhammer\b", text):
            return "Warhammer"
        if re.search(r"\bfunko\b", text):
            return "Funko"
        if re.search(r"\bhot\s+toys\b", text):
            return "Hot Toys"

        # Manga / fumetti / figurine.
        if re.search(r"\bmanga\b|\bhunter\s+x\s+hunter\b|\bdarwins?\s+game\b", text):
            return "Manga"
        if re.search(r"\bfumett", text):
            return "Fumetti"
        if re.search(r"\bpanini\b|\bfigurine\b|\balbum\s+calciatori\b", text):
            return "Panini / Figurine"

        # Modellini auto / die-cast.
        if re.search(
            r"\bmodellini?\b|\bhotwheels?\b|\bbburago\b|\bmebetoys\b|"
            r"\btecnomodel\b|\blaudoracing\b|\bpocher\b",
            text,
        ):
            return "Modellini auto"

        # Auto/mezzi RC: prima brand/modello, poi tipologia.
        if re.search(
            r"\bradiocomand|\bauto\s+rc\b|\bbuggy\b|\bcrawler\b|"
            r"\bkyosho\b|\bhpi\b|\bxray\b|\baxial\b|\btamiya\b|"
            r"\btamya\b|\bteam\s+associated\b|\bnovarossi\b|\bpicco\b|"
            r"\bradiomaster\b|\bmaverick\b|\bmjx\b|\bmini\s*z\b|\bminiz\b",
            text,
        ):
            # Brand + modello quando chiaramente riconoscibile.
            if re.search(r"\baxial\b.*\bscx\s*10\b", text):
                return "RC • Axial SCX10"
            if re.search(r"\baxial\b.*\bscx\s*30\b", text):
                return "RC • Axial SCX30"
            if re.search(r"\bhpi\b.*\bsavage\s+xs\s+flux\b", text):
                return "RC • HPI Savage XS Flux"
            if re.search(r"\bhpi\b.*\bventure\b", text):
                return "RC • HPI Venture"
            if re.search(r"\bxray\b.*\bx4\b", text):
                return "RC • XRAY X4"
            if re.search(r"\bxray\b.*\bx1\b", text):
                return "RC • XRAY X1"
            if re.search(r"\bteam\s+associated\b.*\brc10b7\b", text):
                return "RC • Team Associated RC10B7"
            if re.search(r"\bkyosho\b.*\bmad\s+force\b", text):
                return "RC • Kyosho Mad Force"
            if re.search(r"\bkyosho\b.*\bmini\s*z\b|\bkyosho\b.*\bminiz\b", text):
                return "RC • Kyosho Mini-Z"
            if re.search(r"\bmaverick\b.*\bquantum\s+mt\s+flux\b", text):
                return "RC • Maverick Quantum MT Flux"
            if re.search(r"\btamiya\b.*\btrf\s*422\b|\btamya\b.*\btrf\s*422\b", text):
                return "RC • Tamiya TRF 422"
            if re.search(r"\bradiomaster\b.*\btx16s\b", text):
                return "RC • Radiomaster TX16S"
            if re.search(r"\bnovarossi\b.*\btplus\b", text):
                return "RC • Novarossi Tplus"
            if re.search(r"\bnovarossi\b.*\brally\b", text):
                return "RC • Novarossi Rally"
            if re.search(r"\bpicco\b.*\bp3tt\b", text):
                return "RC • Picco P3TT"

            # Tipologia quando manca un modello preciso.
            if re.search(r"\bcrawler\b|\bscaler\b", text):
                return "RC • Crawler / Scaler"
            if re.search(r"\bbuggy\b", text):
                return "RC • Buggy"
            if re.search(r"\bmonster\s+truck\b|\bmt\b", text):
                return "RC • Monster Truck"
            if re.search(r"\bmini\s*4wd\b|\b1\s*[:/]\s*76\b", text):
                return "RC • Mini"
            if re.search(r"\bbrushless\b", text):
                return "RC • Brushless"
            if re.search(r"\bscoppio\b|\bnitro\b", text):
                return "RC • Nitro / Scoppio"
            if re.search(r"\bradiomaster\b|\btrasmettitor|\bradio\s+comando\b|\bradiocomando\b", text):
                return "RC • Radio / Trasmettitori"

            return "RC • Altro"

        # Modellismo ferroviario.
        if re.search(
            r"\bfleischmann\b|\bacme\b.*\bcarrozza\b|\bh0\b|"
            r"\bmodellismo\s+ferroviario\b|\btrenino\b|\btreni\b",
            text,
        ):
            return "Modellismo ferroviario"

        # Modellismo navale.
        if re.search(
            r"\bmodellismo\s+navale\b|\bveliero\b|\bhms\b|\bsantisima\s+trinidad\b|"
            r"\bmamoli\b|\boccre\b",
            text,
        ):
            return "Modellismo navale"

        # Trading/sports cards non Pokémon/MTG.
        if re.search(
            r"\btopps\b|\btrading\s+cards?\b|\bsports?\s+cards?\b|"
            r"\bcard\s+dazn\b|\bufc\s+topps\b",
            text,
        ):
            return "Trading cards"

        # Altri TCG riconoscibili.
        if re.search(r"\byugioh\b|\byu\s*gi\s*oh\b|\bgalaxy\s+eyes\b", text):
            return "Yu-Gi-Oh!"
        if re.search(r"\bone\s+piece\b.*\b(?:tcg|card|box|op\d+)\b|\bop\d+\s+box\b", text):
            return "One Piece TCG"

        # Giochi da tavolo / boardgame.
        if re.search(
            r"\bgioco\s+tavolo\b|\bboardgame\b|\bdescent\b|"
            r"\bwestern\s+legends\b|\bsword\s+&?\s*sorcery\b",
            text,
        ):
            return "Giochi da tavolo"

        # Arte, stampe e grafica da collezione.
        if re.search(
            r"\bukiyo\b|\bkakemono\b|\bpergamena\s+giapponese\b|"
            r"\bposter\b|\bstampa\b|\bbassorilievi?\b|\bpiero\s+manzoni\b|"
            r"\bfornasetti\b",
            text,
        ):
            return "Arte / Stampe"

        # Macchine da scrivere e oggetti Olivetti.
        if re.search(r"\bolivetti\b|\bmacchina\s+da\s+scrivere\b", text):
            return "Olivetti / Macchine da scrivere"

        # Radio, ricevitori e CB vintage.
        if re.search(
            r"\bricevitore\b|\bradio\b|\bantenna\s+cb\b|\bcb\b.*\bantenna\b",
            text,
        ):
            return "Radio / CB vintage"

        # Multi-tool / Victorinox / Leatherman.
        if re.search(r"\bvictorinox\b|\bleatherman\b", text):
            return "Multi-tool / Coltellini"

        # Modellini Ferrari/F1 espliciti, se non già catturati da modellini auto.
        if re.search(
            r"\bferrari\b.*\b1\s*[:/]\s*(?:18|43|8|7)\b|"
            r"\bf1\b.*\bmodell|\bdeagostini\b.*\bferrari\b",
            text,
        ):
            return "Modellini Ferrari / F1"

        # Design vintage riconoscibile.
        if re.search(r"\bartemide\b|\beclisse\b|\bsgabello\s+industriale\b", text):
            return "Design vintage"


        # Militaria e memorabilia storica.
        if re.search(
            r"\bww2\b|\bmilitaria\b|\bpnf\b|\bmimetica\b|"
            r"\bspange\b|\bteschio\b|\bscudetto\s+pnf\b",
            text,
        ):
            return "Militaria"

        # Transformers e robot da collezione.
        if re.search(r"\btransformers?\b|\bjetfire\b", text):
            return "Transformers"

        # Bambole / giocattoli vintage.
        if re.search(
            r"\bbarbie\b|\bbambol|\bsailor\s+moon\b|"
            r"\bgiocattolo\s+robot\b|\bbiker\s+mice\b|\bmicro\s+machines\b",
            text,
        ):
            return "Giocattoli vintage"

        # Ceramiche / porcellane / piatti da collezione.
        if re.search(
            r"\bceramica\b|\bporcellan|\bpiatti?\b|\bvietri\b|"
            r"\bcantagalli\b|\bformella\b",
            text,
        ):
            return "Ceramiche / Porcellane"

        # Orologi e accessori da collezione.
        if re.search(
            r"\borologi?\b|\bomega\b|\beberhard\b|\bspeed\s*master\b",
            text,
        ):
            return "Orologi / Accessori"

        # Penne e accendini da collezione.
        if re.search(r"\bpenne?\b|\baccendini?\b|\bcartier\b", text):
            return "Penne / Accendini"

        # Reliquie e oggetti religiosi.
        if re.search(r"\breliqui|\bnativit|\bre\s+magio\b|\bpresepe\b", text):
            return "Religioso / Reliquie"

        # Aeromodellismo / elicotteri RC.
        if re.search(
            r"\baeromodell|\baliante\s+rc\b|\baereo\s+rc\b|"
            r"\belicottero\s+rc\b|\bhobbyking\b|\bseb-art\b|\bsebarts?\b",
            text,
        ):
            return "Aeromodellismo RC"

        # Metal detector.
        if re.search(r"\bmetal\s*detector\b|\bmetaldetector\b", text):
            return "Metal detector"

        # Action figure / statue / robot da collezione.
        if re.search(
            r"\bbandai\b|\bmetalbuild\b|\bmazinger\b|\bstatuett|"
            r"\baction\s+figure\b|\bpersonaggi\b",
            text,
        ):
            return "Action figure / Statue"

    # Informatica: famiglie tecniche e modelli utili al sourcing.
    if "informatica" in category_text:
        # GPU NVIDIA RTX / GTX
        gpu_nvidia = re.search(
            r"\b(?:nvidia\s+|geforce\s+)?(rtx|gtx)\s*(\d{3,4})(?:\s*(ti|super))?\b",
            text,
        )
        if gpu_nvidia:
            series, model, variant = gpu_nvidia.groups()
            label = f"NVIDIA {series.upper()} {model}"
            if variant:
                label += f" {variant.upper()}"
            return label

        nvidia_bare = re.search(
            r"\bnvidia\s+(\d{4})(?:\s*(ti|super))?\b",
            text,
        )
        if nvidia_bare:
            model, variant = nvidia_bare.groups()
            label = f"NVIDIA RTX {model}"
            if variant:
                label += f" {variant.upper()}"
            return label

        # GPU AMD Radeon RX
        gpu_amd = re.search(
            r"\b(?:amd\s+|radeon\s+)?rx\s*(\d{3,4})(?:\s*(xt|gre|xtx))?\b",
            text,
        )
        if gpu_amd:
            model, variant = gpu_amd.groups()
            label = f"AMD Radeon RX {model}"
            if variant:
                label += f" {variant.upper()}"
            return label

        # CPU AMD Ryzen
        ryzen = re.search(
            r"\bryzen\s*([3579])\s*(\d{4})(?:\s*(x3d|x|g|u|h|hs|hx))?\b",
            text,
        )
        if ryzen:
            tier, model, suffix = ryzen.groups()
            label = f"AMD Ryzen {tier} {model}"
            if suffix:
                label += f" {suffix.upper()}"
            return label

        amd_bare_cpu = re.search(
            r"\bamd\s+(\d{4})(x3d|x|g)?\b",
            text,
        )
        if amd_bare_cpu:
            model, suffix = amd_bare_cpu.groups()
            tier = model[0]
            if tier in {"3", "5", "7", "9"}:
                label = f"AMD Ryzen {tier} {model}"
                if suffix:
                    label += f" {suffix.upper()}"
                return label

        # CPU Intel Core / Core Ultra
        core_ultra = re.search(
            r"\bcore\s+ultra\s*([579])\s*(\d{3}[a-z]?)\b",
            text,
        )
        if core_ultra:
            tier, model = core_ultra.groups()
            return f"Intel Core Ultra {tier} {model.upper()}"

        intel = re.search(
            r"\b(?:intel\s+)?(?:core\s+)?i?([3579])[-\s]?(\d{4,5})([a-z]{0,2})\b",
            text,
        )
        if intel:
            tier, model, suffix = intel.groups()
            label = f"Intel Core i{tier}-{model}"
            if suffix:
                label += suffix.upper()
            return label

        # Handheld PC / gaming PC portatili
        handheld_patterns = [
            (r"\bsteam\s+deck\s+oled\b", "Steam Deck OLED"),
            (r"\bsteam\s+deck\b", "Steam Deck"),
            (r"\brog\s+ally\s+x\b", "ASUS ROG Ally X"),
            (r"\brog\s+ally\b", "ASUS ROG Ally"),
            (r"\blegion\s+go\s+s\b", "Lenovo Legion Go S"),
            (r"\blegion\s+go\b", "Lenovo Legion Go"),
            (r"\bmsi\s+claw\b", "MSI Claw"),
        ]
        for pattern, label in handheld_patterns:
            if re.search(pattern, text):
                return label

        # NAS
        synology = re.search(r"\bsynology\s+(ds\d{3,4}\+?)\b", text)
        if synology:
            return f"Synology {synology.group(1).upper()}"

        qnap = re.search(r"\bqnap\s+([a-z]{2,4}[-\s]?\d{3,4}[a-z0-9\-]*)\b", text)
        if qnap:
            return f"QNAP {qnap.group(1).upper().replace(' ', '-')}"

        if re.search(r"\bnas\b", text):
            return "NAS"

        # E-reader / e-paper
        ereader_patterns = [
            (r"\bremarkable\s*2\b", "reMarkable 2"),
            (r"\bkobo\s+clara\b", "Kobo Clara"),
            (r"\bkobo\s+forma\b", "Kobo Forma"),
            (r"\bkobo\b", "Kobo"),
            (r"\bpocketbook\s+inkpad\s*4\b", "PocketBook InkPad 4"),
            (r"\bpocketbook\s+era\b", "PocketBook Era"),
            (r"\bbigme\s+b7\b", "Bigme B7"),
            (r"\bviwoods\b", "Viwoods AI Paper"),
        ]
        for pattern, label in ereader_patterns:
            if re.search(pattern, text):
                return label

        # Tablet / 2-in-1
        tablet_patterns = [
            (r"\bxiaomi\s+pad\s*7\b|\bxiami\s+pad\s*7\b", "Xiaomi Pad 7"),
            (r"\bteclast\s+artpad\s+pro\b", "Teclast ArtPad Pro"),
            (r"\bsurface\s+duo\b", "Microsoft Surface Duo"),
        ]
        for pattern, label in tablet_patterns:
            if re.search(pattern, text):
                return label
        if re.search(r"\btablet\b", text):
            return "Tablet"

        # Raspberry / SBC
        if re.search(r"\braspberry\s*pi\s*5\b", text):
            return "Raspberry Pi 5"
        if re.search(r"\braspberry\s*pi\b", text):
            return "Raspberry Pi"

        # VR / smart glasses
        if re.search(r"\bpico\s*4\b", text):
            return "Pico 4"
        if re.search(r"\bdji\s+goggles\s+integra\b", text):
            return "DJI Goggles Integra"

        # Tastiere / controller / creator peripherals
        if re.search(r"\bwooting\b", text):
            return "Wooting"
        if re.search(r"\bhotas\s+warthog\b|\bthrustmaster\b.*\bwarthog\b", text):
            return "Thrustmaster HOTAS Warthog"
        if re.search(r"\belgato\s+stream\s+deck\b", text):
            return "Elgato Stream Deck"
        if re.search(r"\btourbox\s+elite\b", text):
            return "TourBox Elite"
        if re.search(r"\bxppen\b|\bxp\s*pen\b", text):
            return "XP-Pen"
        if re.search(r"\bmouse\b", text):
            return "Mouse"

        # Smart home / sicurezza / videocitofonia
        security_patterns = [
            (r"\bhikvision\b.*\bnvr\b|\bnvr\b.*\bhikvision\b", "Hikvision NVR"),
            (r"\bhikvision\b", "Hikvision"),
            (r"\bezviz\s+cp4\b", "EZVIZ CP4"),
            (r"\bnetatmo\s+presence\b", "Netatmo Presence"),
            (r"\bajax\s+hub\s*2\s+plus\b", "Ajax Hub 2 Plus"),
            (r"\btado\b", "Tado"),
            (r"\bbticino\b.*\b300x\b", "BTicino Classe 300X"),
        ]
        for pattern, label in security_patterns:
            if re.search(pattern, text):
                return label

        # Power station / UPS / inverter
        power_patterns = [
            (r"\bbluetti\s+elite\s*30\s*v2\b", "Bluetti Elite 30 V2"),
            (r"\bpower\s+station\b", "Power Station"),
            (r"\bapc\s+smart[\-\s]?ups\b", "APC Smart-UPS"),
            (r"\beats?on\s+9130\b", "Eaton 9130"),
            (r"\bups\b", "UPS"),
            (r"\bsolaredge\b.*\bse2200h\b", "SolarEdge SE2200H"),
            (r"\binverter\b", "Inverter"),
        ]
        for pattern, label in power_patterns:
            if re.search(pattern, text):
                return label

        # Networking enterprise / Starlink / Cisco / Fortinet
        enterprise_network_patterns = [
            (r"\bcisco\s+c1113[\-\s]?8pltew\b", "Cisco C1113-8PLTEW"),
            (r"\bfortiap\s+431f\b", "FortiAP 431F"),
            (r"\btp\s*link\s+ne211\b|\btplink\s+ne211\b", "TP-Link NE211"),
            (r"\bstarlink\b", "Starlink"),
        ]
        for pattern, label in enterprise_network_patterns:
            if re.search(pattern, text):
                return label

        # GPS / wearable Garmin / Oura
        wearable_patterns = [
            (r"\boura\s+ring\s*5\b", "Oura Ring 5"),
            (r"\bgarmin\s+inreach\s+messenger\b", "Garmin inReach Messenger"),
            (r"\bgarmin\s+gpsmap\s+66s\b", "Garmin GPSMAP 66s"),
            (r"\bgarmin\s+vivoactive\s*6\b", "Garmin Vivoactive 6"),
        ]
        for pattern, label in wearable_patterns:
            if re.search(pattern, text):
                return label

        # Storage HDD / enterprise
        if re.search(r"\bseagate\s+exos\b", text):
            return "Seagate Exos"

        # Cooling / custom loop
        if re.search(r"\bnzxt\s+kraken\s+elite\s*360\b", text):
            return "NZXT Kraken Elite 360"
        if re.search(r"\bek\b.*\bradiator|\bradiatori\s+ek\b", text):
            return "EK Water Cooling"
        if re.search(r"\bdissipatore\b|\bwatercooling\b|\bwater\s+cooling\b", text):
            return "Cooling PC"

        # PSU specifici
        if re.search(r"\bcorsair\s+hx1500i\b", text):
            return "Corsair HX1500i"

        # Stampanti 3D / CNC / maker
        maker_patterns = [
            (r"\bcricut\s+explore\s*4\b", "Cricut Explore 4"),
            (r"\bcricut\s+maker\s*4\b", "Cricut Maker 4"),
            (r"\bcreality\s+k1c\b|\bk1c\b", "Creality K1C"),
            (r"\bbambu\b.*\bpla\b|\bpla\s+bambu\b", "Bambu Lab Filamento"),
            (r"\bcnc\s+3018\b", "CNC 3018"),
            (r"\bxtool\b", "xTool"),
            (r"\bduet\s+3d\b", "Duet 3D"),
        ]
        for pattern, label in maker_patterns:
            if re.search(pattern, text):
                return label

        # Retro computing
        retro_patterns = [
            (r"\bcommodore\s+amiga\s*600\b", "Commodore Amiga 600"),
            (r"\bolivetti\s+envision\s*400\b", "Olivetti Envision 400"),
            (r"\bwindows\s*95\b", "PC Vintage Windows 95"),
            (r"\bmsx\b", "MSX"),
        ]
        for pattern, label in retro_patterns:
            if re.search(pattern, text):
                return label

        # Industriale / automazione
        industrial_patterns = [
            (r"\bsiemens\s+et200\b|\bet200\s+siemens\b", "Siemens ET200"),
            (r"\bsiemens\s+6es7155", "Siemens ET200"),
            (r"\bdigitax\s+st\s+dst\s*1405\b", "Digitax ST DST 1405"),
            (r"\bsiglent\s+sdg1032x\b", "Siglent SDG1032X"),
            (r"\bpinza\s+amperometrica\b", "Strumenti di misura"),
        ]
        for pattern, label in industrial_patterns:
            if re.search(pattern, text):
                return label

        # Utility tech specifiche
        if re.search(r"\bflipper\s+zero\b", text):
            return "Flipper Zero"
        if re.search(r"\bplaud\s+note\s+pro\b", text):
            return "Plaud Note Pro"
        if re.search(r"\bcorsair\s+xeneon\s+edge\b", text):
            return "Corsair Xeneon Edge"

        # SSD / NVMe
        if re.search(r"\bnvme\b|\bssd\b", text):
            if re.search(r"\bsamsung\s+990\s+pro\b", text):
                return "SSD Samsung 990 Pro"
            if re.search(r"\bsamsung\s+980\s+pro\b", text):
                return "SSD Samsung 980 Pro"
            if re.search(r"\bwd\s+black\s+sn850x\b", text):
                return "SSD WD Black SN850X"
            if re.search(r"\bcrucial\s+t700\b", text):
                return "SSD Crucial T700"
            if re.search(r"\bcrucial\s+p5\s+plus\b", text):
                return "SSD Crucial P5 Plus"
            if re.search(r"\bm\s*2\b|\bnvme\b", text):
                return "SSD NVMe / M.2"
            return "SSD"

        # RAM
        if re.search(r"\b(?:ddr[345]|ram)\b", text):
            if re.search(r"\bddr5\b", text):
                return "RAM DDR5"
            if re.search(r"\bddr4\b", text):
                return "RAM DDR4"
            if re.search(r"\bddr3\b", text):
                return "RAM DDR3"
            return "RAM"

        # Schede madri
        if re.search(
            r"\bscheda\s+madre\b|\bmotherboard\b|"
            r"\b(?:b[45678]\d0|x[45678]\d0|z[45678]\d0|a[45678]\d0)\b",
            text,
        ):
            chipset = re.search(
                r"\b(b[45678]\d0|x[45678]\d0|z[45678]\d0|a[45678]\d0)\b",
                text,
            )
            if chipset:
                return f"Scheda madre {chipset.group(1).upper()}"
            return "Schede madri"

        # Mini PC
        mini_pc_patterns = [
            (r"\bmac\s+mini\b", "Mac mini"),
            (r"\bintel\s+nuc\b|\bnuc\s+\d", "Intel NUC"),
            (r"\bbeelink\b", "Beelink Mini PC"),
            (r"\bminisforum\b", "Minisforum Mini PC"),
            (r"\bgeekom\b", "GEEKOM Mini PC"),
        ]
        for pattern, label in mini_pc_patterns:
            if re.search(pattern, text):
                return label
        if re.search(r"\bmini\s*pc\b", text):
            return "Mini PC"

        # Notebook / workstation: altre linee ricorrenti
        laptop_patterns = [
            (r"\bmsi\s+(?:katana|raider|vector|stealth|prestige|modern)\b", "MSI Notebook"),
            (r"\bacer\s+nitro\b", "Acer Nitro"),
            (r"\bacer\s+predator\b", "Acer Predator"),
            (r"\bacer\s+aspire\b", "Acer Aspire"),
            (r"\basus\s+vivobook\b", "ASUS VivoBook"),
            (r"\basus\s+zenbook\b", "ASUS ZenBook"),
            (r"\bhp\s+omen\b", "HP Omen"),
            (r"\bhp\s+victus\b", "HP Victus"),
            (r"\bdell\s+precision\b", "Dell Precision"),
            (r"\blenovo\s+loq\b", "Lenovo LOQ"),
            (r"\blenovo\s+yoga\b", "Lenovo Yoga"),
            (r"\bmicrosoft\s+surface\s+pro\b", "Microsoft Surface Pro"),
            (r"\bmicrosoft\s+surface\s+laptop\b", "Microsoft Surface Laptop"),
        ]
        for pattern, label in laptop_patterns:
            if re.search(pattern, text):
                return label

        # Monitor: modello specifico prima della marca generica.
        if re.search(r"\bmonitor\b|\bdisplay\b", text):
            monitor_patterns = [
                (r"\bphilips\s+cm8833(?:[/\s-]*00g)?\b", "Monitor • Philips CM8833"),

                (r"\bmsi\b.*\bmag\s*274qf[\s-]*x24\b", "Monitor • MSI MAG 274QF-X24"),
                (r"\bmsi\b.*\boptix\s+g27c7\b", "Monitor • MSI Optix G27C7"),
                (r"\bmsi\b.*\bmag301cr2\b", "Monitor • MSI MAG301CR2"),
                (r"\bmsi\b.*\b345cqr\b", "Monitor • MSI 345CQR"),

                (r"\bktc\b.*\bh32s17\b", "Monitor • KTC H32S17"),
                (r"\bktc\b.*\bh27t7p[\s-]*2\b", "Monitor • KTC H27T7P-2"),
                (r"\bktc\b.*\bh27e6\b", "Monitor • KTC H27E6"),
                (r"\bktc\b.*\bm27t20\b", "Monitor • KTC M27T20"),

                (r"\bsamsung\b.*\b(?:odyssey|odissey)\b.*\bg5\b.*\b34\b", "Monitor • Samsung Odyssey G5 34"),
                (r"\bsamsung\b.*\b(?:odyssey|odissey)\b.*\bg5\b.*\b27\b", "Monitor • Samsung Odyssey G5 27"),
                (r"\bsamsung\b.*\bsmart\s+monitor\s+m7\b", "Monitor • Samsung Smart Monitor M7"),

                (r"\blg\b.*\b27ul500[\s-]*w\b", "Monitor • LG 27UL500-W"),
                (r"\blg\b.*\b27gr93u\b", "Monitor • LG UltraGear 27GR93U"),

                (r"\bbenq\b.*\bew3270u\b", "Monitor • BenQ EW3270U"),
            ]
            for pattern, label in monitor_patterns:
                if re.search(pattern, text):
                    return label

            # Famiglie utili quando il modello esatto non è presente.
            if re.search(r"\bmsi\b", text):
                return "Monitor • MSI"
            if re.search(r"\bktc\b", text):
                return "Monitor • KTC"
            if re.search(r"\bsamsung\b.*\b(?:odyssey|odissey)\b", text):
                return "Monitor • Samsung Odyssey"
            if re.search(r"\bsamsung\b", text):
                return "Monitor • Samsung"
            if re.search(r"\blg\b.*\bultragear\b", text):
                return "Monitor • LG UltraGear"
            if re.search(r"\blg\b", text):
                return "Monitor • LG"
            if re.search(r"\bphilips\b", text):
                return "Monitor • Philips"
            if re.search(r"\baoc\b", text):
                return "Monitor • AOC"
            if re.search(r"\blenovo\b", text):
                return "Monitor • Lenovo"
            if re.search(r"\bbenq\b", text):
                return "Monitor • BenQ"
            if re.search(r"\bproart\b|\basus\b", text):
                return "Monitor • ASUS"

            # Specifiche tecniche, solo quando manca marca/modello.
            if re.search(r"\bmini[\s-]*led\b", text):
                return "Monitor • Mini-LED"
            if re.search(r"\bultrawide\b|\b21\s*[:/]\s*9\b", text):
                return "Monitor • Ultrawide"
            if re.search(r"\b300\s*hz\b", text):
                return "Monitor • 300Hz"
            if re.search(r"\bgaming\b", text):
                return "Monitor • Gaming generico"

            return "Monitor • Altro"

        # Router / Mesh / networking
        networking_patterns = [
            (r"\bfritz!?box\b", "AVM FRITZ!Box"),
            (r"\bdeco\b.*\btp\s*link\b|\btp\s*link\b.*\bdeco\b", "TP-Link Deco"),
            (r"\bunifi\b|\bubiquiti\b", "Ubiquiti UniFi"),
            (r"\beero\b", "Amazon eero"),
            (r"\borbi\b", "Netgear Orbi"),
        ]
        for pattern, label in networking_patterns:
            if re.search(pattern, text):
                return label
        if re.search(r"\brouter\b|\bmesh\b|\bswitch\s+ethernet\b|\baccess\s+point\b", text):
            return "Networking"

        # Stampanti / scanner
        if re.search(r"\bstampante\b|\bprinter\b", text):
            if re.search(r"\blaser\b", text):
                return "Stampanti laser"
            return "Stampanti"
        if re.search(r"\bscanner\b", text):
            return "Scanner"

        # Server / workstation desktop
        if re.search(r"\bserver\b|\bpoweredge\b", text):
            return "Server"
        if re.search(r"\bworkstation\b|\bthinkstation\b|\bz\s*workstation\b", text):
            return "Workstation"

        # PC desktop / gaming assemblati
        if re.search(
            r"\bpc\s+gaming\b|\bgaming\s+pc\b|\bpc\s+fisso\b|"
            r"\bdesktop\b|\bcomputer\s+fisso\b",
            text,
        ):
            return "PC Desktop / Gaming"

        # Alimentatori e case
        if re.search(r"\balimentatore\b|\bpower\s+supply\b|\bpsu\b", text):
            return "Alimentatori PC"
        if re.search(r"\bcase\s+pc\b|\bcabinet\s+pc\b", text):
            return "Case PC"

    # CONSOLE 400€+: classificazione dedicata ai prodotti ad alto ticket.
    if "console 400" in category_text:
        premium_console_patterns = [
            # Handheld / console portatili
            (r"\bmsi\s+claw\s*8\b", "Handheld • MSI Claw 8"),
            (r"\bsteam\s+deck\s+oled\b", "Handheld • Steam Deck OLED"),
            (r"\bgame\s*boy\s+advance\s+sp\b", "Nintendo • Game Boy Advance SP"),
            (r"\bredmagic\s+astra\b", "Handheld • RedMagic Astra"),
            (r"\bayn\s+odin\s*3\s+pro\b", "Handheld • AYN Odin 3 Pro"),
            (r"\bayn\s+thor\s+pro\b", "Handheld • AYN Thor Pro"),
            (r"\bodin\s*2\s+portal\s+max\b", "Handheld • AYN Odin 2 Portal Max"),

            # VR
            (r"\bpico\s*4\s+ultra\b", "VR • Pico 4 Ultra"),
            (r"\boculus\s*3\b", "VR • Meta Quest 3"),
            (r"\bpimax\s+crystal\s+light\b", "VR • Pimax Crystal Light"),

            # Sim racing
            (r"\bfanatec\s+csl\s+dd\s+pro\b", "Sim Racing • Fanatec CSL DD Pro"),
            (r"\bfanatec\s+f1\b", "Sim Racing • Fanatec F1"),
            (r"\bsimucube\s*2\s+pro\b", "Sim Racing • Simucube 2 Pro"),
            (r"\bsimnet\s+sp\s+pro\b", "Sim Racing • SimNet SP Pro"),
            (r"\bmoza\s+r5\b", "Sim Racing • Moza R5"),
            (r"\bconspit\s+cpp\s+lite\b", "Sim Racing • Conspit CPP Lite"),
            (r"\bsimagic\s+alpha\s+evo\s+sport\b", "Sim Racing • Simagic Alpha Evo Sport"),
            (r"\bpedaliera\s+vrs\b|\bvrs\b.*\bpedaliera\b", "Sim Racing • VRS Pedals"),
            (r"\bthrustmaster\s+t[\s-]*lcm\b", "Sim Racing • Thrustmaster T-LCM"),

            # PlayStation / retro / lotti
            (r"\baystation\s*5\b", "PlayStation 5"),
            (r"\blotto\s+ps3\b.*\bpsp\b", "PlayStation • Lotto PS3 / PSP"),
            (r"\bsega\s+master\s+system\b", "SEGA Master System"),
            (r"\b3\s+console\b.*\bgiochi\b", "Console • Lotto"),
            (r"\bconsole\s+nuova\b", "Console • Modello non identificato"),

            # Periferiche / controller espliciti
            (r"\bwolfmix\s+w1\b", "Controller • Wolfmix W1"),
        ]

        for pattern, label in premium_console_patterns:
            if re.search(pattern, text):
                return label

        if re.search(r"\bfanatec\b|\bsimucube\b|\bsimagic\b|\bmoza\b|\bpedaliera\b", text):
            return "Sim Racing • Altro"
        if re.search(r"\bvr\b|\boculus\b|\bpimax\b|\bpico\b", text):
            return "VR • Altro"
        if re.search(r"\bsteam\s+deck\b|\bayn\b|\bodin\b|\bhandheld\b", text):
            return "Handheld • Altro"

    # Tutto per i bambini: famiglie basate sui titoli reali.
    if "tutto per i bambini" in category_text or "bambini" in category_text:
        kids_patterns = [
            # LEGO e costruzioni
            (r"\blego\b.*\btechnic\b|\blego\b.*\b421\d+\b", "LEGO • Technic"),
            (r"\blego\b.*\bharry\s+potter\b|\blego\b.*\b71043\b", "LEGO • Harry Potter"),
            (r"\blego\b.*\bstar\s+wars\b|\blego\b.*\bx[\s-]*wing\b|\blego\b.*\btie\s+fighter\b", "LEGO • Star Wars"),
            (r"\blego\b.*\bcastle\b|\blego\b.*\bbarracuda\b", "LEGO • Castle / Pirati"),
            (r"\blego\b.*\b(?:spiderman|marvel|daily\s+bugle)\b", "LEGO • Marvel"),
            (r"\blego\b.*\bduplo\b", "LEGO • Duplo"),
            (r"\blego\b.*\bbionicle\b", "LEGO • Bionicle"),
            (r"\blego\b.*\bminifig", "LEGO • Minifigures"),
            (r"\blego\b.*\b(?:sfusi|mattoncini|varie|combo)\b", "LEGO • Sfusi / Lotti"),
            (r"\blego\b.*\b(\d{4,6})\b", "LEGO • Set"),
            (r"\blego\b|\blegoo\b", "LEGO • Altro"),

            # Passeggini / trio / telai
            (r"\bcybex\b.*\bgazelle\b", "Passeggini • Cybex Gazelle"),
            (r"\bcybex\b", "Passeggini / Seggiolini • Cybex"),
            (r"\binglesina\b.*\b(?:twin\s+sketch|quid2|electa)\b", "Passeggini • Inglesina"),
            (r"\bfoppapedretti\b.*\b(?:trio|passeggino)\b", "Passeggini • Foppapedretti"),
            (r"\bjoolz\b.*\b(?:aer|aer2)\b", "Passeggini • Joolz Aer"),
            (r"\bbugaboo\b.*\bbutterfly\b|\bbugaboo\b.*\bbuterfly\b", "Passeggini • Bugaboo Butterfly"),
            (r"\bvalco\s*baby\b.*\bsnap\s*4\b|\bvalcobany\b.*\bsnap\s*4\b", "Passeggini • Valco Baby Snap 4"),
            (r"\bgb\s+pockit\b", "Passeggini • GB Pockit"),
            (r"\bmast\b.*\bpasseggino\b|\bpasseggino\b.*\bmast\b", "Passeggini • MAST"),
            (r"\bpasseggino\b|\btrio\b|\bnavicella\b|\btelaio\b", "Passeggini / Trio"),

            # Seggiolini / basi auto
            (r"\bcybex\s+pallas\b", "Seggiolini auto • Cybex Pallas"),
            (r"\bbritax\b.*\bromer\b", "Seggiolini auto • Britax Römer"),
            (r"\bdoona\b", "Seggiolini auto • Doona"),
            (r"\bnuna\b.*\b(?:base\s+next|arra\s+next)\b", "Seggiolini auto • Nuna"),
            (r"\bisofix\b", "Seggiolini auto • Base ISOFIX"),
            (r"\bseggiolino\b|\bovetto\b", "Seggiolini auto"),

            # Culle / lettini / next2me
            (r"\bnext2me\b", "Culle • Chicco Next2Me"),
            (r"\bstokke\b.*\bculla\b", "Culle • Stokke"),
            (r"\bculla\b.*\bfoppapedretti\b", "Culle • Foppapedretti"),
            (r"\bculla\b", "Culle"),
            (r"\blettino\b", "Lettini"),
            (r"\bfasciatoio\b", "Fasciatoi"),

            # Seggioloni / sedie evolutive
            (r"\bstokke\b.*\b(?:tripp?\s*trapp|seggiolone|sedia)\b|\btripp?\s*trapp\b", "Seggioloni • Stokke Tripp Trapp"),
            (r"\bhauck\b.*\bsedia\b", "Seggioloni • Hauck"),
            (r"\bseggiolone\b", "Seggioloni"),

            # Sdraiette
            (r"\bmamaroo\b|\b4moms\b", "Sdraiette • 4moms mamaRoo"),
            (r"\bsdraietta\b", "Sdraiette"),

            # Marsupi / zaini porta-bimbo
            (r"\bminimeis\b", "Marsupi / Porta-bimbo • MiniMeis"),
            (r"\bbaby\s+monkey\b.*\bmarsupio\b", "Marsupi / Porta-bimbo • Baby Monkey"),
            (r"\bmarsupio\b|\bzaino\s+porta\s+bimbo\b", "Marsupi / Porta-bimbo"),

            # Carrelli bici / mobilità bambini
            (r"\bqueridoo\b|\bcarrellino\b.*\bbici\b|\bcarrello\s+porta\s+bimbi\b", "Carrelli bici bambini"),
            (r"\bmonopattino\b.*\b(?:bambin|highwaykick)\b", "Mobilità bambini • Monopattino"),
            (r"\b(?:moto|vespa|quad)\b.*\bbambin", "Veicoli elettrici bambini"),
            (r"\btriciclo\b", "Tricicli"),

            # Giochi / brand
            (r"\bfaba\b", "FABA"),
            (r"\bsylvanian\s+families\b", "Sylvanian Families"),
            (r"\bbarbie\b.*\b(?:dreamhouse|casa\s+dei\s+sogni)\b", "Barbie • Dreamhouse"),
            (r"\bbarbie\b", "Barbie"),
            (r"\bbeyblade\b", "Beyblade"),
            (r"\bbruder\b", "Bruder"),
            (r"\bhot\s*wheels\b|\bmatchbox\b", "Hot Wheels / Matchbox"),
            (r"\bgormiti\b", "Gormiti"),
            (r"\bemiglio\b", "Emiglio"),
            (r"\bwinx\b", "Winx"),
            (r"\bpinypon\b", "Pinypon"),
            (r"\bmontessori\b|\blovevery\b", "Giochi educativi / Montessori"),
            (r"\bpeluche\b|\bsquishy\b", "Peluche / Squishy"),
            (r"\bgiocattoli?\s+vintage\b|\bgiochi\s+misti\b", "Giocattoli vintage / Lotti"),

            # Pokémon / collezionabili
            (r"\bpokemon\b", "Pokémon"),
            (r"\baction\s+figure\b|\bfigure\b|\bcavalieri\s+dello\s+zodiaco\b", "Action figure"),

            # Prima infanzia / accessori
            (r"\btiralatte\b", "Prima infanzia • Tiralatte"),
            (r"\bpannolini\b", "Prima infanzia • Pannolini"),
            (r"\bpiscina\s+gonfiabile\b", "Giochi da esterno • Piscine"),
            (r"\bcasetta\b.*\bbambin", "Giochi da esterno • Casette"),
            (r"\bcucina\s+giocattolo\b", "Giochi di ruolo • Cucine"),
        ]

        for pattern, label in kids_patterns:
            if re.search(pattern, text):
                return label

    # Giardino e fai da te: classificazione dedicata ai titoli reali rimasti in Altro.
    # Manteniamo famiglie utili per il sourcing: marca/modello quando riconoscibile,
    # altrimenti tipologia di prodotto. Le regole valgono solo dentro questa categoria.
    if "giardino" in category_text or "fai da te" in category_text:
        garden_patterns = [
            # Robot tagliaerba / automazione prato
            (r"\bworx\s+landroid\b", "Robot tagliaerba • Worx Landroid"),
            (r"\bbosch\s+indego\b|\bindego\b", "Robot tagliaerba • Bosch Indego"),
            (r"\bhusqvarna\s+automower\b|\bautomower\b", "Robot tagliaerba • Husqvarna Automower"),
            (r"\brobot\b.*\btagliaerba\b|\btagliaerba\b.*\brobot\b", "Robot tagliaerba • Altro"),

            # Piscina / robot pulizia
            (r"\bdolphin\b.*\be10\b|\be10\b.*\bdolphin\b", "Piscina • Dolphin E10"),
            (r"\bdolphin\b", "Piscina • Dolphin"),
            (r"\bzodiac\b", "Piscina • Zodiac"),
            (r"\brobot\b.*\bpiscina\b|\bpiscina\b.*\brobot\b", "Piscina • Robot pulizia"),
            (r"\bpompa\b.*\bpiscina\b|\bfiltro\b.*\bpiscina\b", "Piscina • Pompe e filtri"),

            # Automazione cancelli
            (r"\bducati\b.*\b(?:cancello|apricancello)\b|\b(?:cancello|apricancello)\b.*\bducati\b", "Automazione cancelli • Ducati"),
            (r"\bfaac\b", "Automazione cancelli • FAAC"),
            (r"\bcame\b", "Automazione cancelli • CAME"),
            (r"\bbft\b", "Automazione cancelli • BFT"),
            (r"\b(?:motore|kit)\b.*\b(?:cancello|apricancello)\b|\bapricancello\b", "Automazione cancelli • Altro"),

            # Batterie/caricabatterie per utensili: prima delle regole di marca.
            (r"\bbatteri[ae]\b.*\b(?:milwaukee|bosch|dewalt|makita|parkside)\b|\b(?:milwaukee|bosch|dewalt|makita|parkside)\b.*\bbatteri[ae]\b", "Utensili • Batterie"),
            (r"\bcaricabatteri[ae]\b.*\b(?:milwaukee|bosch|dewalt|makita|parkside)\b|\b(?:milwaukee|bosch|dewalt|makita|parkside)\b.*\bcaricabatteri[ae]\b", "Utensili • Caricabatterie"),

            # Milwaukee / Bosch / DeWalt / Makita / Parkside: prima i tipi più utili.
            (r"\bmilwaukee\b.*\b(?:tassellatore|martello|demolitore)\b|\b(?:tassellatore|martello|demolitore)\b.*\bmilwaukee\b", "Utensili • Milwaukee Tassellatori"),
            (r"\bmilwaukee\b.*\bm18\b|\bm18\b.*\bmilwaukee\b", "Utensili • Milwaukee M18"),
            (r"\bmilwaukee\b", "Utensili • Milwaukee"),
            (r"\bbosch\b.*\b(?:tassellatore|martello|demolitore)\b|\b(?:tassellatore|martello|demolitore)\b.*\bbosch\b", "Utensili • Bosch Tassellatori"),
            (r"\bbosch\b.*\b(?:professional|gbh|gsb|gws|gdr|gdx)\b", "Utensili • Bosch Professional"),
            (r"\bdewalt\b", "Utensili • DeWalt"),
            (r"\bmakita\b", "Utensili • Makita"),
            (r"\bparkside\b", "Utensili • Parkside"),
            (r"\bhilti\b", "Utensili • Hilti"),
            (r"\bmetabo\b", "Utensili • Metabo"),
            (r"\beinhell\b", "Utensili • Einhell"),

            # Utensili per tipologia, anche senza marca.
            (r"\btassellator\w*\b|\bmartello\s+demolitore\b", "Utensili • Tassellatori / Demolitori"),
            (r"\btrapano\b.*\bavvitatore\b|\bavvitatore\b.*\btrapano\b", "Utensili • Trapani / Avvitatori"),
            (r"\bavvitatore\b", "Utensili • Avvitatori"),
            (r"\btrapano\b", "Utensili • Trapani"),
            (r"\bsmerigliatrice\b|\bflex\b", "Utensili • Smerigliatrici"),
            (r"\bseghetto\b|\bsega\s+circolare\b|\bsega\s+alternativa\b", "Utensili • Seghe elettriche"),
            (r"\bfresatrice\b", "Utensili • Fresatrici"),
            (r"\blevigatrice\b", "Utensili • Levigatrici"),

            # Saldatura / officina
            (r"\btelwin\b", "Saldatura • Telwin"),
            (r"\bsaldatrice\b|\bsaldatura\b", "Saldatura • Altro"),
            (r"\bcompressore\b", "Officina • Compressori"),

            # Attrezzatura da giardino a motore / batteria
            (r"\bshindaiwa\b.*\bt[\s-]*27\b|\bt[\s-]*27\b.*\bshindaiwa\b", "Giardino • Shindaiwa T-27"),
            (r"\bshindaiwa\b", "Giardino • Shindaiwa"),
            (r"\bstihl\b.*\bbg\s*56\b|\bbg\s*56\b.*\bstihl\b", "Giardino • Stihl BG56"),
            (r"\bstihl\b", "Giardino • Stihl"),
            (r"\bhusqvarna\b.*\b129\s*lk\b|\b129\s*lk\b.*\bhusqvarna\b", "Giardino • Husqvarna 129LK"),
            (r"\bhusqvarna\b", "Giardino • Husqvarna"),
            (r"\bdecespugliator\w*\b", "Giardino • Decespugliatori"),
            (r"\bsoffiator\w*\b", "Giardino • Soffiatori"),
            (r"\bmotosega\b", "Giardino • Motoseghe"),
            (r"\btagliasiepi\b", "Giardino • Tagliasiepi"),
            (r"\btagliaerba\b|\brasaerba\b", "Giardino • Tagliaerba"),

            # Pulizia esterni / pompe / energia
            (r"\bkarcher\b|\bkärcher\b", "Pulizia esterni • Kärcher"),
            (r"\bidropulitrice\b", "Pulizia esterni • Idropulitrici"),
            (r"\bgeneratore\b|\bgruppo\s+elettrogeno\b", "Energia • Generatori"),
            (r"\binverter\b", "Energia • Inverter"),
            (r"\bpompa\s+sommersa\b|\belettropompa\b|\bautoclave\b", "Pompe / Autoclavi"),

            # Fotovoltaico
            (r"\bfotovoltaic\w*\b|\bpannell[io]\s+solari?\b", "Fotovoltaico"),

            # Barbecue / cottura esterna
            (r"\bweber\b.*\bbarbecue\b|\bbarbecue\b.*\bweber\b", "Barbecue • Weber"),
            (r"\bbarbecue\b|\bbbq\b", "Barbecue • Altro"),

            # Quadri elettrici / climatizzazione tecnica
            (r"\brittal\b.*\bsk\s*3302\s*100\b|\bsk\s*3302\s*100\b", "Quadri elettrici • Rittal SK3302100"),
            (r"\brittal\b", "Quadri elettrici • Rittal"),

        ]

        for pattern, label in garden_patterns:
            if re.search(pattern, text):
                return label

    # Elettrodomestici: secondo pass basato sui titoli reali rimasti in Altro.
    if "elettrodomestici" in category_text or "eletrodomestici" in category_text:
        appliance_patterns = [
            # Vorwerk / Bimby / Folletto
            (r"\bbimby\s*(?:tm|t)?\s*31\b|\bbimby\s+t31\b", "Bimby TM31"),
            (r"\bbimby\s*tm21\b", "Bimby TM21"),
            (r"\bbimby\s*tm6\b|\bboccale\s+tm6\b", "Bimby TM6"),
            (r"\bbimby\s*tm7\b|\bboccale\s+tm7\b", "Bimby TM7"),
            (r"\bbimby\b", "Bimby • Modello non identificato"),
            (r"\bfolletto\s+vr7s\b", "Folletto VR7S"),
            (r"\bfolletto\s+vr300\b", "Folletto VR300"),
            (r"\bfolletto\s+(?:vk|wk)\s*135\b", "Folletto VK135"),
            (r"\bfolletto\s+(?:vk|wk)\s*140\b", "Folletto VK140"),
            (r"\bfolletto\s+vk\s*150\b", "Folletto VK150"),
            (r"\bfolletto\s+vk\s*200\b", "Folletto VK200"),
            (r"\bfolletto\s+vk\s*220s\b", "Folletto VK220S"),
            (r"\b(?:folletto|vorwerk)\b.*\bvk7s\b|\bvk7s\b", "Folletto VK7S"),
            (r"\bfolletto\b|\bvorwerk\b", "Folletto / Vorwerk • Altro"),

            # Robot / aspirazione / lavapavimenti
            (r"\becovacs\s+deebot\s+t50\s+pro\s+omni\b", "Robot • Ecovacs Deebot T50 Pro Omni"),
            (r"\becovacs\s+winbot\b|\bconga\s+windroid\b", "Robot lavavetri"),
            (r"\bmova\s+p50\s+ultra\b", "Robot • Mova P50 Ultra"),
            (r"\broomba\s+plus\s*505\b", "Robot • Roomba Plus 505"),
            (r"\bxiaomi\s+x20\+?\b", "Robot • Xiaomi X20+"),
            (r"\blefant\s+m3\b", "Robot • Lefant M3"),
            (r"\baspirapolvere\s+robot\b|\brobot\s+aspirapolvere\b", "Robot aspirapolvere"),
            (r"\btineco\s+s7\b", "Lavapavimenti • Tineco S7"),
            (r"\btineco\s+s9\b", "Lavapavimenti • Tineco S9"),
            (r"\btineco\b", "Lavapavimenti • Tineco"),
            (r"\bbissell\s+spotclean\b", "Lavapavimenti • Bissell SpotClean"),
            (r"\bbissell\s+crosswave\b", "Lavapavimenti • Bissell CrossWave"),
            (r"\browenta\s+x[\s-]*clean\s*10\b", "Lavapavimenti • Rowenta X-Clean 10"),
            (r"\brotowash\b", "Lavapavimenti • Rotowash"),
            (r"\blavapavimenti\b", "Lavapavimenti"),
            (r"\baspirapolvere\b|\baspiratore\b", "Aspirapolvere / Aspiratori"),

            # Frigo / congelatori / cantinette
            (r"\bfrigo(?:rifero)?\b.*\bsmeg\b|\bsmeg\b.*\bfrigo", "Frigoriferi • Smeg"),
            (r"\bfrigo(?:rifero)?\b.*\bindesit\b", "Frigoriferi • Indesit"),
            (r"\bred\s*bull\b.*\bmini\s*frigo\b|\bredbull\b.*\bmini\s*frigo\b", "Minifrigo • Red Bull"),
            (r"\bfrigo\s+vetrina\b", "Frigoriferi • Vetrina"),
            (r"\bmini\s*frigo\b|\bfrigo\s+da\s+campeggio\b", "Minifrigo"),
            (r"\bcantina\s+frigo\b|\bcantinetta\s+per\s+vino\b", "Cantinette vino"),
            (r"\bcongelatore\b", "Congelatori"),
            (r"\bfrigo\b|\bfrigorifero\b", "Frigoriferi"),

            # Climatizzazione / riscaldamento
            (r"\bcondizionatore\b|\bclimatizzatore\b|\baria\s+condizionata\b|\bclima\s+portatile\b", "Climatizzazione"),
            (r"\bpinguino\b", "Climatizzazione • Portatile"),
            (r"\bdeumidificatore\b|\btrotec\s+ttk\b", "Deumidificatori"),
            (r"\btermoconvettor\b|\bradiatore\s+elettrico\b|\bstufa\s+a\s+pellet\b", "Riscaldamento"),
            (r"\btermostato\b|\bcronotermostat", "Termostati"),
            (r"\btado\b", "Domotica • Tado"),

            # Caffè / cucina
            (r"\bnespresso\s+creatista\s+pro\b", "Caffè • Nespresso Creatista Pro"),
            (r"\bnespresso\s+(?:gran\s+)?lattissima\b", "Caffè • Nespresso Lattissima"),
            (r"\bnespresso\b", "Caffè • Nespresso"),
            (r"\bdelonghi\s+magnifica\s+evo\b", "Caffè • DeLonghi Magnifica Evo"),
            (r"\bgaggia\s+classic\b", "Caffè • Gaggia Classic"),
            (r"\bla\s+pavoni\b", "Caffè • La Pavoni"),
            (r"\blavazza\b", "Caffè • Lavazza"),
            (r"\beureka\b.*\bmacin", "Caffè • Macinacaffè Eureka"),
            (r"\bmacin(?:a|ino)caff", "Caffè • Macinacaffè"),
            (r"\bmacchina\s+da\s+caffe\b|\bmacchia\s+da\s+caffe\b", "Caffè • Macchine"),
            (r"\bkitchen\s*aid\b|\bkitcheaid\b", "Planetarie • KitchenAid"),
            (r"\bkenwood\s+(?:chef\s+xl|kvl4100s|kmix)\b", "Planetarie • Kenwood"),
            (r"\bplanetaria\b|\bimpastatrice\b", "Planetarie / Impastatrici"),
            (r"\bmonsieur\s+cuisine\b|\bmousiere\s+cousine\b", "Robot cucina • Monsieur Cuisine"),
            (r"\bsilver\s*crest\b.*\brobot\s+cucina\b", "Robot cucina • SilverCrest"),
            (r"\bfriggitrice\s+aria\b", "Friggitrici ad aria"),
            (r"\bmacchina\s+gelato\b|\bgelateria\s+professionale\b", "Gelatiere"),
            (r"\bgranitore\b", "Granitori"),
            (r"\bmacchina\s+sottovuoto\b", "Macchine sottovuoto"),
            (r"\bessiccatore\b|\bessicatore\b", "Essiccatori"),
            (r"\btritacarne\b|\bpassata\s+di\s+pomodoro\b|\bspremipomodoro\b", "Preparazione alimenti"),
            (r"\bspillatore\b|\bspillatrice\b|\bperfectdraft\b", "Spillatori birra"),
            (r"\bnutella\b.*\b(?:dosatore|dispenser|erogatore)\b|\b(?:dosatore|dispenser|erogatore)\b.*\bnutella\b", "Dispenser Nutella"),
            (r"\bforno\b", "Forni"),

            # Beauty / cura persona
            (r"\bbraun\b.*\bserie\s*9\b|\brasoi?o\b.*\bbraun\b", "Rasoi • Braun"),
            (r"\bphilips\s+shaver\b|\brasoi?o\b.*\bphilips\b", "Rasoi • Philips"),
            (r"\brasoi?o\b.*\bpanasonic\b", "Rasoi • Panasonic"),
            (r"\bphilips\s+lumea\b", "Beauty • Philips Lumea"),
            (r"\bbraun\s+silk\s+expert\b", "Beauty • Braun Silk-expert"),
            (r"\bghd\b", "Beauty • GHD"),
            (r"\bphon\b|\bsupersoni[c]?\b", "Beauty • Asciugacapelli"),
            (r"\bpressoterapia\b", "Beauty / Benessere • Pressoterapia"),

            # Energia / domotica / impianti
            (r"\bbluetti\b", "Energia • Bluetti"),
            (r"\bpower\s+station\b", "Energia • Power station"),
            (r"\becoflow\b.*\binverter\b", "Energia • EcoFlow"),
            (r"\binverter\b", "Energia • Inverter"),
            (r"\bshelly\b", "Domotica • Shelly"),
            (r"\bvimar\b", "Domotica / Elettrico • Vimar"),
            (r"\bvelux\b", "Automazione • Velux"),
            (r"\bgrundfos\b|\bdanfoss\b|\belettropomp", "Impianti • Pompe"),
            (r"\bdepuratore\b|\bosmosi\b", "Depurazione acqua"),

            # Altri elettrodomestici / professionali
            (r"\bbambu\s*lab\s+a1\b|\bbambulab\s+a1\b", "Stampa 3D • Bambu Lab A1"),
            (r"\bcricut\s+maker\s*3\b", "Craft • Cricut Maker 3"),
            (r"\bmacchina\s+taglio\s+laser\b|\bmecpow\b", "Macchine laser"),
            (r"\bidropulitrice\b", "Idropulitrici"),
            (r"\babbattitore\s+di\s+temperatura\b", "Professionale cucina • Abbattitori"),
            (r"\bfontana\s+di\s+cioccolato\b", "Professionale cucina • Cioccolato"),
            (r"\bzucchero\s+filato\b", "Professionale cucina • Zucchero filato"),
            (r"\btagliamozzarella\b", "Professionale cucina • Tagliamozzarella"),
            (r"\bmacchina\s+di\s+rimaglio\b|\btagliacuci\b", "Cucito / Tessile"),
        ]

        for pattern, label in appliance_patterns:
            if re.search(pattern, text):
                return label

    # Sport: famiglie utili per il sourcing.
    if "sport" in category_text:
        sport_patterns = [
            # Ciclismo / e-bike
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\btrek\b|\btrek\b.*\b(?:bike|mtb|bici)\b", "Bici • Trek"),
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\bspecialized\b|\bspecialized\b.*\b(?:bike|mtb|bici)\b", "Bici • Specialized"),
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\bcannondale\b|\bcannondale\b.*\b(?:bike|mtb|bici)\b", "Bici • Cannondale"),
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\bscott\b|\bscott\b.*\b(?:bike|mtb|bici)\b", "Bici • Scott"),
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\bcube\b|\bcube\b.*\b(?:bike|mtb|bici)\b", "Bici • Cube"),
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\bbianchi\b|\bbianchi\b.*\b(?:bike|mtb|bici)\b", "Bici • Bianchi"),
            (r"\b(?:bici|bicicletta|bike|mtb)\b.*\borbea\b|\borbea\b.*\b(?:bike|mtb|bici)\b", "Bici • Orbea"),
            (r"\b(?:ebike|e bike|e-bike|bici elettrica|bicicletta elettrica)\b", "E-bike"),
            (r"\bmountain\s*bike\b|\bmtb\b", "Bici • MTB"),
            (r"\bbici\s+da\s+corsa\b|\broad\s+bike\b", "Bici • Corsa"),
            (r"\bgravel\b", "Bici • Gravel"),
            (r"\bbmx\b", "Bici • BMX"),

            # Componenti bici
            (r"\bshimano\b.*\b(?:ultegra|dura\s*ace|105|deore|xt|xtr)\b", "Componenti bici • Shimano"),
            (r"\bsram\b.*\b(?:red|force|rival|gx|xx1|axs)\b", "Componenti bici • SRAM"),
            (r"\bcampagnolo\b", "Componenti bici • Campagnolo"),
            (r"\bruote?\b.*\b(?:carbonio|carbon)\b", "Componenti bici • Ruote carbonio"),
            (r"\bgruppo\b.*\b(?:shimano|sram|campagnolo)\b", "Componenti bici • Gruppo"),

            # Padel / tennis
            (r"\bpadel\b.*\bbabolat\b|\bbabolat\b.*\bpadel\b", "Padel • Babolat"),
            (r"\bpadel\b.*\bhead\b|\bhead\b.*\bpadel\b", "Padel • Head"),
            (r"\bpadel\b.*\bwilson\b|\bwilson\b.*\bpadel\b", "Padel • Wilson"),
            (r"\bpadel\b.*\badidas\b|\badidas\b.*\bpadel\b", "Padel • Adidas"),
            (r"\bpadel\b.*\bnox\b|\bnox\b.*\bpadel\b", "Padel • Nox"),
            (r"\bpadel\b.*\bbullpadel\b|\bbullpadel\b", "Padel • Bullpadel"),
            (r"\bracchetta\b.*\bpadel\b|\bpala\s+padel\b", "Padel • Racchette"),
            (r"\bracchetta\b.*\btennis\b|\btennis\b.*\bracchetta\b", "Tennis • Racchette"),

            # Golf
            (r"\btaylormade\b", "Golf • TaylorMade"),
            (r"\bcallaway\b", "Golf • Callaway"),
            (r"\btitleist\b", "Golf • Titleist"),
            (r"\bping\b.*\b(?:driver|golf|iron|putter)\b", "Golf • Ping"),
            (r"\bgolf\b.*\bmazze\b|\bset\s+golf\b|\bdriver\s+golf\b", "Golf"),

            # Sci / snowboard
            (r"\bsci\b.*\bsalomon\b|\bsalomon\b.*\bsci\b", "Sci • Salomon"),
            (r"\bsci\b.*\brossignol\b|\brossignol\b.*\bsci\b", "Sci • Rossignol"),
            (r"\bsci\b.*\batomic\b|\batomic\b.*\bsci\b", "Sci • Atomic"),
            (r"\bsci\b.*\bhead\b|\bhead\b.*\bsci\b", "Sci • Head"),
            (r"\bsnowboard\b.*\bburton\b|\bburton\b.*\bsnowboard\b", "Snowboard • Burton"),
            (r"\bsnowboard\b", "Snowboard"),
            (r"\bsci\b", "Sci"),

            # Fitness / palestra
            (r"\btapis\s*roulant\b|\btreadmill\b", "Fitness • Tapis roulant"),
            (r"\bcyclette\b|\bspin\s*bike\b|\bspinning\b", "Fitness • Cyclette / Spin bike"),
            (r"\bellittica\b", "Fitness • Ellittica"),
            (r"\bpanca\b.*\bpalestra\b|\bpanca\s+multifunzione\b", "Fitness • Panche"),
            (r"\bmanubri\b|\bbilanciere\b|\bdischi\s+pesi\b", "Fitness • Pesi"),
            (r"\btechnogym\b", "Fitness • Technogym"),

            # Running / outdoor GPS
            (r"\bgarmin\s+forerunner\s*\d+\b", "Running • Garmin Forerunner"),
            (r"\bgarmin\s+fenix\s*\d+\b", "Outdoor • Garmin Fenix"),
            (r"\bgarmin\s+edge\s*\d+\b", "Ciclismo • Garmin Edge"),
            (r"\bsuunto\b", "Outdoor • Suunto"),
            (r"\bpolar\b.*\b(?:vantage|pacer|grit)\b", "Running • Polar"),

            # Calcio
            (r"\bscarpe\s+calcio\b|\bscarpini\b", "Calcio • Scarpe"),
            (r"\bmaglia\s+calcio\b|\bmaglietta\s+calcio\b", "Calcio • Maglie"),
            (r"\bpallone\s+calcio\b", "Calcio • Palloni"),

            # Pesca
            (r"\bcanna\s+da\s+pesca\b|\bmulinello\b|\bpesca\b.*\bshimano\b", "Pesca"),
            (r"\bgarmin\b.*\b(?:fishfinder|striker)\b|\blowrance\b", "Pesca • Ecoscandagli"),

            # Sub / diving
            (r"\berogatore\b|\bcomputer\s+sub\b|\bmuta\s+sub\b|\bsubacquea\b", "Subacquea"),
            (r"\bsuunto\b.*\b(?:d5|d4|eon)\b", "Subacquea • Suunto"),
        ]

        for pattern, label in sport_patterns:
            if re.search(pattern, text):
                return label

        # Secondo pass Sport basato sui titoli reali rimasti in "Altro".

        # Padel / tennis: molti titoli indicano solo marca/modello, senza la parola padel.
        racket_patterns = [
            (r"\bnox\b", "Padel • Nox"),
            (r"\bvarlion\b", "Padel • Varlion"),
            (r"\boxdog\b", "Padel • Oxdog"),
            (r"\bhirostar\b", "Padel • Hirostar"),
            (r"\bdrop\s+shot\b", "Padel • Drop Shot"),
            (r"\bjoma\b.*\b(?:blast|padel)\b", "Padel • Joma"),
            (r"\btecnifibre\b", "Tennis / Padel • Tecnifibre"),
            (r"\bprokennex\b", "Tennis • ProKennex"),
            (r"\bbabolat\b.*\b(?:pure|drive|aero)\b", "Tennis • Babolat"),
            (r"\bblade\b.*\b(?:racchetta|raqueta|bors|tennis)\b", "Tennis • Wilson Blade"),
            (r"\bracchett[ae]\b|\braqueta\b", "Tennis / Padel • Racchette"),
        ]
        for pattern, label in racket_patterns:
            if re.search(pattern, text):
                return label

        # Wingfoil / foil / SUP / surf / windsurf.
        water_board_patterns = [
            (r"\bsabfoil\b", "Wing/Foil • Sabfoil"),
            (r"\bduotone\b.*\b(?:foil|wing|slick|whizz|bar)\b", "Wing/Foil • Duotone"),
            (r"\bgong\b.*\b(?:foil|wing|tavola)\b|\b(?:foil|wing)\b.*\bgong\b", "Wing/Foil • Gong"),
            (r"\bcabrinh[ai]\b", "Wing/Foil • Cabrinha"),
            (r"\brrd\b.*\b(?:foil|wing|tavola|fusoliera|twintip)\b", "Wing/Foil • RRD"),
            (r"\bnaish\b", "Wing/Foil • Naish"),
            (r"\btakuma\b.*\bwingfoil\b", "Wing/Foil • Takuma"),
            (r"\bf[\s-]?one\b.*\bwing\b", "Wing/Foil • F-One"),
            (r"\barmstrong\b.*\bfoil\b", "Wing/Foil • Armstrong"),
            (r"\bwing\s*foil\b|\bwingfoil\b|\bfoil\b", "Wing/Foil"),
            (r"\bsup\b|\bstand\s+up\s+paddle\b|\bwindsup\b", "SUP"),
            (r"\bwindsurf\b", "Windsurf"),
            (r"\bsurfskate\b", "Surfskate"),
            (r"\btavola\s+surf\b|\bsurf\b", "Surf"),
            (r"\bwakeboard\b", "Wakeboard"),
        ]
        for pattern, label in water_board_patterns:
            if re.search(pattern, text):
                return label

        # Subacquea / apnea.
        diving_patterns = [
            (r"\bmares\b.*\b(?:apnea|gav|xr|smart|sub)\b", "Sub • Mares"),
            (r"\bcressi\b", "Sub • Cressi"),
            (r"\bapeks\b|\bapex\s+atx\b", "Sub • Apeks"),
            (r"\bcetma\b.*\bpinne\b|\bpinne\b.*\bcetma\b", "Sub • CETMA"),
            (r"\balemanni\b.*\bpinne\b", "Sub • Alemanni"),
            (r"\bgav\b|\bbcd\b", "Sub • GAV / BCD"),
            (r"\bcomputer\b.*\b(?:sub|immersion|apnea)\b|\borologio\s+per\s+apnea\b", "Sub • Computer"),
            (r"\barbalete\b", "Sub • Arbalete"),
            (r"\bpinne\b", "Sub • Pinne"),
            (r"\bbombola\s+sub\b|\bscooter\s+subacqueo\b|\bsubacque", "Subacquea"),
        ]
        for pattern, label in diving_patterns:
            if re.search(pattern, text):
                return label

        # Pesca.
        fishing_patterns = [
            (r"\bdaiwa\b", "Pesca • Daiwa"),
            (r"\bpenn\b.*\b(?:525|mulinello|mag)\b", "Pesca • Penn"),
            (r"\babu\b.*\b(?:6500|cardinal)\b", "Pesca • Abu Garcia"),
            (r"\bbelly\s*boat\b|\bbellyboat\b", "Pesca • Belly boat"),
            (r"\bcarpfishing\b", "Pesca • Carpfishing"),
            (r"\bcanne?\b.*\b(?:mosca|pesca)\b|\bmulinello\b|\bjig\b", "Pesca"),
            (r"\bhook\s+reveal\b|\blowrance\b", "Pesca • Ecoscandaglio"),
        ]
        for pattern, label in fishing_patterns:
            if re.search(pattern, text):
                return label

        # Arrampicata / alpinismo / ferrata.
        climbing_patterns = [
            (r"\bpetzl\b.*\b(?:quark|nomic|spirit|gri\s*gri)\b", "Arrampicata • Petzl"),
            (r"\bpiccozz[ae]\b", "Alpinismo • Piccozze"),
            (r"\bkit\s+ferrata\b|\bvie\s+ferrate\b", "Arrampicata • Ferrata"),
            (r"\bcrashpad\b|\bboulder\b", "Arrampicata • Boulder"),
            (r"\bfriend\b.*\barrampicata\b|\barrampicata\b.*\bfriend\b", "Arrampicata • Friends"),
            (r"\brinvii\b|\bimbrago\b.*\barrampicata\b|\bcord[ae]\b.*\barrampicata\b", "Arrampicata • Attrezzatura"),
            (r"\bscarpette\s+arrampicata\b|\battrezzatur[ae]\s+per\s+arrampicata\b", "Arrampicata"),
            (r"\bortovox\b.*\bartva\b|\bartva\b", "Alpinismo • ARTVA"),
            (r"\bbastoncini\s+leki\b", "Trekking • Bastoncini"),
        ]
        for pattern, label in climbing_patterns:
            if re.search(pattern, text):
                return label

        # Fitness / riabilitazione / home gym.
        fitness_real_patterns = [
            (r"\bcompex\b", "Fitness • Compex"),
            (r"\bmagnetoterapia\b|\bmag\s*2000\b", "Fitness • Magnetoterapia"),
            (r"\belettrostimolatore\b|\btesmed\b", "Fitness • Elettrostimolatori"),
            (r"\bvogatore\b", "Fitness • Vogatore"),
            (r"\bhalf\s+rack\b|\brack\b.*\bpalestra\b", "Fitness • Rack"),
            (r"\bpanca\b", "Fitness • Panche"),
            (r"\bdischi\b.*\b(?:gym|pesi)\b", "Fitness • Pesi"),
            (r"\bbellicon\b", "Fitness • Trampolino"),
            (r"\bpoledance\b|\bpole\b.*\baerea\b", "Fitness • Pole / Aerea"),
            (r"\bcrossfit\b", "Fitness • CrossFit"),
            (r"\bwithings\s+bodyscan\b", "Fitness • Withings Body Scan"),
        ]
        for pattern, label in fitness_real_patterns:
            if re.search(pattern, text):
                return label

        # Smartwatch / wearable sportivi.
        wearable_sport_patterns = [
            (r"\bamazfit\s+(?:active|activ|action)\s+max\b", "Sportwatch • Amazfit Active Max"),
            (r"\bamazfit\s+t[\s-]*rex\s*3\b", "Sportwatch • Amazfit T-Rex 3"),
            (r"\bhuawei\s+gt5\s+pro\b", "Sportwatch • Huawei GT5 Pro"),
            (r"\bfitbit\b", "Sportwatch • Fitbit"),
            (r"\bpolar\s+loop\b", "Sportwatch • Polar Loop"),
            (r"\bwatch\s+ultra\b", "Sportwatch • Apple Watch Ultra"),
            (r"\bshokz\s+open\s*run\b", "Running • Shokz OpenRun"),
        ]
        for pattern, label in wearable_sport_patterns:
            if re.search(pattern, text):
                return label

        # Calcio / volley.
        if re.search(r"\bmagli?[ae]\b.*\b(?:calcio|inter|juventus|lazio|parma|francia|mondiali)\b", text):
            return "Calcio • Maglie"
        if re.search(r"\bpallone\b.*\b(?:calcio|maradona|fifa|world\s+cup)\b", text):
            return "Calcio • Palloni"
        if re.search(r"\badidas\s+predator\b", text):
            return "Calcio • Adidas Predator"
        if re.search(r"\bset\s+calcio\b", text):
            return "Calcio • Set"
        if re.search(r"\bmikasa\b.*\bvolley\b|\bpallone\b.*\bvolley\b", text):
            return "Volley"

        # Camping / trekking.
        camping_patterns = [
            (r"\bquechua\b.*\b(?:air|tenda)\b", "Camping • Quechua"),
            (r"\btenda\b.*\bdecathlon\b|\barpenaz\b", "Camping • Decathlon"),
            (r"\btenda\b.*\bferrino\b", "Camping • Ferrino"),
            (r"\btenda\b.*\bskandika\b", "Camping • Skandika"),
            (r"\btenda\b.*\bvango\b", "Camping • Vango"),
            (r"\btenda\b.*\bsimond\b", "Camping • Simond"),
            (r"\bmaterassini?\b.*\bsea\s+to\s+summit\b", "Camping • Sea to Summit"),
            (r"\bsacco\s+a\s+pelo\b", "Camping • Sacchi a pelo"),
            (r"\btenda\b|\bcampeggio\b", "Camping • Tende"),
        ]
        for pattern, label in camping_patterns:
            if re.search(pattern, text):
                return label

        # Metal detector.
        metal_patterns = [
            (r"\bnokta\b", "Metal detector • Nokta"),
            (r"\bminelab\b|\bequinox\b", "Metal detector • Minelab"),
            (r"\bxp\s+mi[\s-]*6\b|\bpin[t]?\s+pointer\b", "Metal detector • Pinpointer"),
        ]
        for pattern, label in metal_patterns:
            if re.search(pattern, text):
                return label

        # Snowboard / pattinaggio / skate.
        board_patterns = [
            (r"\bnidecker\b", "Snowboard • Nidecker"),
            (r"\bbataleon\b", "Snowboard • Bataleon"),
            (r"\bburton\b", "Snowboard • Burton"),
            (r"\bride\s+twin\s+pig\b", "Snowboard • Ride Twin Pig"),
            (r"\bedea\b|\broll\s+line\b|\bpattinaggio\b", "Pattinaggio"),
            (r"\bskateboard\b|\bskate\b", "Skateboard"),
        ]
        for pattern, label in board_patterns:
            if re.search(pattern, text):
                return label

        # Parapendio.
        if re.search(r"\bparapendio\b|\bparawing\b", text):
            return "Parapendio"

        # Kart / moto sport.
        if re.search(r"\bkart\b|\bcrg\b.*\b100cc\b", text):
            return "Kart"
        if re.search(r"\balpinestars\b|\btuta\s+moto\b|\bberik\b", text):
            return "Moto • Protezioni / Abbigliamento"

        # Mobilità personale.
        if re.search(r"\bsegway\b|\bninebot\b|\bmonopattino\b|\bmonoruota\b", text):
            return "Mobilità personale"

        # Tiro con arco (non include prodotti da ricarica/armi).
        if re.search(r"\btiro\s+con\s+l\s+arco\b|\briser\b|\bflettenti\b|\barco\s+ricurvo\b", text):
            return "Tiro con arco"

        # Altre nicchie sportive riconoscibili.
        if re.search(r"\bsella\b.*\b(?:zaldi|equitazione)\b|\bstaffe\s+safe\s+riding\b", text):
            return "Equitazione"
        if re.search(r"\bbocce\b", text):
            return "Bocce"
        if re.search(r"\bst[e]?cca\b.*\b(?:biliardo|effebi|gomez)\b", text):
            return "Biliardo"

        # Macro-famiglie residuali ma ancora utili.
        if re.search(r"\bbici\b|\bbicicletta\b|\bbike\b", text):
            return "Bici • Altro"
        if re.search(r"\bpadel\b", text):
            return "Padel • Altro"
        if re.search(r"\btennis\b", text):
            return "Tennis • Altro"
        if re.search(r"\bgolf\b", text):
            return "Golf • Altro"
        if re.search(r"\bpalestra\b|\bfitness\b", text):
            return "Fitness • Altro"
        if re.search(r"\bpesca\b", text):
            return "Pesca • Altro"

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
        ("playstation", "PlayStation • Modello non identificato"),
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


@st.cache_data(ttl=60, show_spinner=False)
def prepare_data():
    """Carica e prepara i dati una sola volta per ciclo cache.

    Questa è la parte più costosa della pagina: parsing date, calcolo tempi,
    riconoscimento famiglie e clustering. Tenerla in cache rende i rerun
    causati da selectbox/dataframe praticamente immediati.
    """
    data = load_market_data().copy()

    if data.empty:
        return data

    # La pagina usa al massimo 90 giorni di storico.
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=90)
    data = data[
        data["detected_sold_at"].notna()
        & (data["detected_sold_at"] >= cutoff)
    ].copy()

    data["sale_time_hours"] = (
        data["detected_sold_at"] - data["posted_at"]
    ).dt.total_seconds() / 3600

    data.loc[data["sale_time_hours"] < 0, "sale_time_hours"] = pd.NA

    # Esclude dalle analisi gli annunci che hanno impiegato più di 10 giorni.
    data = data[
        data["sale_time_hours"].notna()
        & (data["sale_time_hours"] <= 24 * 10)
        & data["detected_sold_at"].notna()
    ].copy()

    # Usa stringhe stabili così la cache della classificazione viene riutilizzata
    # tra i rerun della pagina e tra titoli/categorie ripetuti.
    data["Famiglia"] = [
        detect_family(str(title or ""), str(category or ""))
        for title, category in zip(data["title"], data["category"])
    ]
    data = apply_recurring_families(data)
    data = apply_manual_family_overrides(data)

    return data


df = prepare_data()

if df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()


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
    .agg(
        Venduti=("id", "count"),
        Prezzo_medio=("price", "mean"),
        Prezzo_mediano=("price", "median"),
        Tempo_mediano_ore=("sale_time_hours", "median"),
    )
    .reset_index()
)

previous_cat = (
    previous
    .groupby("category", dropna=False)
    .agg(
        Venduti=("id", "count"),
        Prezzo_medio=("price", "mean"),
        Prezzo_mediano=("price", "median"),
        Tempo_mediano_ore=("sale_time_hours", "median"),
    )
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

# ---------------------------------------------------------
# CASH COW / PRODOTTI DA RICOMPRARE
# ---------------------------------------------------------
# Non abbiamo il costo reale di acquisto: quindi il "margine" non viene inventato.
# Usiamo stabilità del prezzo di rivendita come proxy di prevedibilità e mostriamo
# una soglia d'acquisto indicativa all'80% della mediana (spread lordo teorico 20%,
# prima di spedizioni, commissioni, resi e altri costi).
family_quality = (
    detail
    .groupby("Famiglia")
    .agg(
        Prezzo_q25=("price", lambda s: s.quantile(0.25)),
        Prezzo_q75=("price", lambda s: s.quantile(0.75)),
        Entro_24h_pct=("sale_time_hours", lambda s: (s <= 24).mean() * 100),
    )
    .reset_index()
)

family_stats = family_stats.merge(
    family_quality,
    on="Famiglia",
    how="left",
)

# PS5: nelle Cash Cow serve anche una vista aggregata della piattaforma.
# Le varianti restano comunque separate nella tabella famiglie e per il prezzo d'acquisto.
ps5_current = detail[
    detail["Famiglia"].astype(str).str.match(
        r"^PS5(?:$|\s)",
        na=False,
    )
].copy()

ps5_previous = detail_prev[
    detail_prev["Famiglia"].astype(str).str.match(
        r"^PS5(?:$|\s)",
        na=False,
    )
].copy()

if not ps5_current.empty:
    ps5_prices = ps5_current["price"].dropna()
    ps5_hours = ps5_current["sale_time_hours"].dropna()
    ps5_venduti = len(ps5_current)
    ps5_venduti_prec = len(ps5_previous)

    ps5_aggregate = pd.DataFrame([{
        "Famiglia": "PS5 — tutte le versioni",
        "Venduti": ps5_venduti,
        "Prezzo_mediano": ps5_prices.median() if not ps5_prices.empty else pd.NA,
        "Tempo_mediano_ore": ps5_hours.median() if not ps5_hours.empty else pd.NA,
        "Venduti_prec": ps5_venduti_prec,
        "Prezzo_mediano_prec": (
            ps5_previous["price"].median()
            if not ps5_previous.empty
            else pd.NA
        ),
        "Trend_volume_%": (
            ((ps5_venduti - ps5_venduti_prec) / ps5_venduti_prec) * 100
            if ps5_venduti_prec > 0
            else pd.NA
        ),
        "Prezzo_q25": ps5_prices.quantile(0.25) if not ps5_prices.empty else pd.NA,
        "Prezzo_q75": ps5_prices.quantile(0.75) if not ps5_prices.empty else pd.NA,
        "Entro_24h_pct": (
            (ps5_hours <= 24).mean() * 100
            if not ps5_hours.empty
            else pd.NA
        ),
    }])

    family_stats = pd.concat(
        [ps5_aggregate, family_stats],
        ignore_index=True,
    )

family_stats["Dispersione_prezzo_%"] = family_stats.apply(
    lambda row: (
        ((row["Prezzo_q75"] - row["Prezzo_q25"]) / row["Prezzo_mediano"]) * 100
        if pd.notna(row["Prezzo_mediano"]) and row["Prezzo_mediano"] > 0
        and pd.notna(row["Prezzo_q25"]) and pd.notna(row["Prezzo_q75"])
        else pd.NA
    ),
    axis=1,
)

# Score 0-100 orientato al sourcing:
# 50 volume, 25 velocità, 15 stabilità prezzo, 10 continuità.
# Il volume usa una scala relativa al leader della categoria, così i prodotti
# realmente liquidi vengono premiati molto più dei campioni piccoli.
max_family_volume = max(float(family_stats["Venduti"].max()), 1.0)

family_stats["Score_volume"] = family_stats["Venduti"].apply(
    lambda sold: 50.0 * (float(sold) / max_family_volume) ** 0.5
)

family_stats["Score_velocita"] = family_stats["Tempo_mediano_ore"].apply(
    lambda hours: (
        max(0.0, 25 * (1 - min(float(hours), 168.0) / 168.0))
        if pd.notna(hours)
        else 0.0
    )
)

family_stats["Score_stabilita"] = family_stats["Dispersione_prezzo_%"].apply(
    lambda dispersion: (
        max(0.0, 15 * (1 - min(float(dispersion), 50.0) / 50.0))
        if pd.notna(dispersion)
        else 0.0
    )
)

family_stats["Score_continuita"] = family_stats.apply(
    lambda row: (
        10.0
        if row["Venduti_prec"] >= max(2, row["Venduti"] * 0.35)
        else (5.0 if row["Venduti_prec"] > 0 else 0.0)
    ),
    axis=1,
)

family_stats["CashCow_score"] = (
    family_stats["Score_volume"]
    + family_stats["Score_velocita"]
    + family_stats["Score_stabilita"]
    + family_stats["Score_continuita"]
).round(0).clip(0, 100)

family_stats["Prezzo_max_acquisto"] = family_stats["Prezzo_mediano"] * 0.80

def cash_cow_signal(row):
    if row["Famiglia"] == "PS5 — tutte le versioni":
        reasons = ["domanda PS5 aggregata"]

        if pd.notna(row["Tempo_mediano_ore"]) and row["Tempo_mediano_ore"] <= 48:
            reasons.append("vendita rapida")
        if row["Venduti_prec"] > 0:
            reasons.append("domanda continua")

        reasons.append("prezzo: vedi variante")
        return " · ".join(reasons[:3])

    reasons = []

    if row["Venduti"] >= max(5, family_stats["Venduti"].median()):
        reasons.append("alto volume")
    if pd.notna(row["Tempo_mediano_ore"]) and row["Tempo_mediano_ore"] <= 48:
        reasons.append("vendita rapida")
    if pd.notna(row["Dispersione_prezzo_%"]) and row["Dispersione_prezzo_%"] <= 20:
        reasons.append("prezzo stabile")
    if row["Venduti_prec"] > 0:
        reasons.append("domanda continua")

    if not reasons:
        reasons.append("campione da monitorare")

    return " · ".join(reasons[:3])

generic_cash_cow_families = {
    "PlayStation",
    "Xbox",
    "Nintendo",
    "Canon",
    "Nikon",
    "Sony",
    "Samsung",
    "Apple",
    "Fotocamere",
    "Console",
    "Smartphone",
    "Tablet",
    "Computer",
}

cash_cow = family_stats[
    (family_stats["Venduti"] >= 5)
    & (family_stats["Prezzo_mediano"].notna())
    & (family_stats["Prezzo_mediano"] > 0)
    & (~family_stats["Famiglia"].astype(str).str.contains(
        "Altro|non identificato|non specificat",
        case=False,
        regex=True,
        na=False,
    ))
    & (~family_stats["Famiglia"].astype(str).isin(generic_cash_cow_families))
].copy()

cash_cow["Insight"] = cash_cow.apply(cash_cow_signal, axis=1)
cash_cow["Score"] = cash_cow["CashCow_score"].apply(lambda x: f"{int(x)}/100")
cash_cow["Prezzo rivendita"] = cash_cow["Prezzo_mediano"].apply(format_price)
cash_cow["Compra max*"] = cash_cow["Prezzo_max_acquisto"].apply(format_price)

ps5_aggregate_mask = cash_cow["Famiglia"] == "PS5 — tutte le versioni"
cash_cow.loc[ps5_aggregate_mask, "Prezzo rivendita"] = "vedi varianti"
cash_cow.loc[ps5_aggregate_mask, "Compra max*"] = "vedi varianti"

cash_cow["Rotazione"] = cash_cow["Tempo_mediano_ore"].apply(format_speed)
cash_cow["Stabilità prezzo"] = cash_cow["Dispersione_prezzo_%"].apply(
    lambda x: f"IQR {x:.0f}%" if pd.notna(x) else "-"
)

cash_cow = cash_cow.sort_values(
    ["CashCow_score", "Venduti", "Tempo_mediano_ore"],
    ascending=[False, False, True],
)

# Se esiste domanda PS5 aggregata, la rendiamo sempre visibile senza falsarne lo score.
if (cash_cow["Famiglia"] == "PS5 — tutte le versioni").any():
    ps5_row = cash_cow[
        cash_cow["Famiglia"] == "PS5 — tutte le versioni"
    ]
    other_rows = cash_cow[
        cash_cow["Famiglia"] != "PS5 — tutte le versioni"
    ].head(4)
    cash_cow = pd.concat([ps5_row, other_rows], ignore_index=True)
else:
    cash_cow = cash_cow.head(5)

st.markdown("### 🐄 Cash Cow — cosa ricomprare con continuità")

if not cash_cow.empty:
    st.dataframe(
        cash_cow[
            [
                "Famiglia",
                "Score",
                "Venduti",
                "Rotazione",
                "Prezzo rivendita",
                "Compra max*",
                "Stabilità prezzo",
                "Insight",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

    best_cash_cow = cash_cow.iloc[0]
    st.success(
        f"🐄 Miglior candidato: {best_cash_cow['Famiglia']} — "
        f"{int(best_cash_cow['CashCow_score'])}/100, "
        f"{int(best_cash_cow['Venduti'])} venduti in 30 giorni, "
        f"tempo mediano {format_duration(best_cash_cow['Tempo_mediano_ore'])}."
    )

    st.caption(
        "* Compra max = 80% del prezzo mediano osservato: lascia uno spread lordo teorico "
        "del 20% prima di spedizione, commissioni, resi e altri costi. "
        "Il punteggio combina volume (50%), velocità (25%), stabilità del prezzo (15%) "
        "e continuità della domanda (10%). Servono almeno 5 vendite negli ultimi 30 giorni. "
        "Non è un margine reale finché non inseriamo "
        "anche il tuo costo d'acquisto effettivo."
    )
else:
    st.info(
        "Dati ancora insufficienti per individuare Cash Cow affidabili in questa categoria."
    )

st.markdown("### 🧩 Brand / famiglie / modelli")

family_stats["Prezzo"] = family_stats["Prezzo_mediano"].apply(format_price)
family_stats["Tempo vendita"] = family_stats["Tempo_mediano_ore"].apply(format_speed)
family_stats["Trend 30 gg"] = family_stats["Trend_volume_%"].apply(format_delta)

# Viste aggregate oltre alle sottofamiglie.
if selected_category and "collezionismo" in normalize_text(selected_category):

    def add_aggregate_family(base_name, prefix):
        nonlocal_family_stats = None
        subset_current = detail[
            detail["Famiglia"].astype(str).str.startswith(prefix)
        ].copy()
        subset_previous = detail_prev[
            detail_prev["Famiglia"].astype(str).str.startswith(prefix)
        ].copy()

        if subset_current.empty:
            return None

        venduti = len(subset_current)
        venduti_prec = len(subset_previous)
        trend = (
            ((venduti - venduti_prec) / venduti_prec) * 100
            if venduti_prec > 0
            else pd.NA
        )

        return pd.DataFrame(
            [{
                "Famiglia": base_name,
                "Venduti": venduti,
                "Prezzo_mediano": subset_current["price"].median(),
                "Tempo_mediano_ore": subset_current["sale_time_hours"].median(),
                "Venduti_prec": venduti_prec,
                "Prezzo_mediano_prec": (
                    subset_previous["price"].median()
                    if not subset_previous.empty
                    else pd.NA
                ),
                "Trend_volume_%": trend,
                "Prezzo": format_price(subset_current["price"].median()),
                "Tempo vendita": format_speed(subset_current["sale_time_hours"].median()),
                "Trend 30 gg": format_delta(trend),
            }]
        )

    aggregate_rows = []
    for base_name, prefix in [
        ("Pokémon TCG", "Pokémon • "),
        ("LEGO", "LEGO • "),
        ("RC / Radiocomandati", "RC • "),
    ]:
        aggregate_row = add_aggregate_family(base_name, prefix)
        if aggregate_row is not None:
            aggregate_rows.append(aggregate_row)

    if aggregate_rows:
        family_stats = pd.concat(
            aggregate_rows + [family_stats],
            ignore_index=True,
        )

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

    aggregate_prefixes = {
        "Pokémon TCG": "Pokémon • ",
        "LEGO": "LEGO • ",
        "RC / Radiocomandati": "RC • ",
    }

    if selected_family in aggregate_prefixes:
        selected_family_data = detail[
            detail["Famiglia"].astype(str).str.startswith(
                aggregate_prefixes[selected_family]
            )
        ].copy()
    else:
        selected_family_data = detail[
            detail["Famiglia"] == selected_family
        ].copy()

    # KPI famiglia: restano sugli ultimi 30 giorni.
    famiglia_venduti = len(selected_family_data)
    famiglia_prezzo_medio = selected_family_data["price"].mean()
    famiglia_prezzo_mediano = selected_family_data["price"].median()
    famiglia_tempo_mediano = selected_family_data["sale_time_hours"].median()

    # Lista annunci: usa tutto lo storico disponibile (max 90 giorni),
    # così la consultazione non si ferma al limite dei KPI a 30 giorni.
    if selected_family in aggregate_prefixes:
        selected_family_listings_data = df[
            (df["category"] == selected_category)
            & df["Famiglia"].astype(str).str.startswith(
                aggregate_prefixes[selected_family]
            )
        ].copy()
    else:
        selected_family_listings_data = df[
            (df["category"] == selected_category)
            & (df["Famiglia"] == selected_family)
        ].copy()

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

    family_listings = (
        selected_family_listings_data
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
    if selected_family in aggregate_prefixes:
        historical_family_data = df[
            (df["category"] == selected_category)
            & df["Famiglia"].astype(str).str.startswith(
                aggregate_prefixes[selected_family]
            )
        ].copy()
    else:
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

