import re
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
        .replace("insta 360", "insta360")
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

        # Pokémon / TCG: sottofamiglie utili al sourcing.
        pokemon_match = re.search(
            r"\bpokemon\b|\bpoke\b|\bcharizard\b|\bblastoise\b|"
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

            # 2. Sigillato: box, ETB, blister, booster, SPC e prodotti sealed.
            if re.search(
                r"\betb\b|\bbox\b|\bblister\b|\bbooster\b|"
                r"\bspc\b|\bsealed\b|\bsigillat|\bdisplay\b|"
                r"\bcollection\s+box\b|\bscatola\s+speciale\b",
                text,
            ):
                return "Pokémon • Sigillato"

            # 3. 30° anniversario come segmento dedicato.
            if re.search(
                r"\b30\s*(?:th|o|°)?\s*annivers|\b30\s*esimo\b|"
                r"\btrentesimo\b|\bprimi\s+compagni\b",
                text,
            ):
                return "Pokémon • 30° Anniversario"

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

    data["Famiglia"] = [
        detect_family(title, category)
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


