import re
from collections import defaultdict
from statistics import median

from database import get_connection
from sales_speed import calculate_hours, format_duration

def extract_storage(text):
    text = text.lower()

    match = re.search(
        r"\b(64|128|256|512)\s*(gb|g)?\b",
        text,
    )

    if match:
        return f"{match.group(1)} GB"

    if re.search(r"\b1\s*tb\b", text):
        return "1 TB"

    return None


def classify_iphone(text):
    label = None

    match = re.search(
        r"\biphone\s*(1[0-9]|[6-9])\s*"
        r"(pro\s*max|promax|pro|plus|mini|e)?\b",
        text,
    )

    if match:
        model = match.group(1)
        raw_variant = (match.group(2) or "").replace(" ", "")

        variants = {
            "promax": "Pro Max",
            "pro": "Pro",
            "plus": "Plus",
            "mini": "Mini",
            "e": "e",
        }

        variant = variants.get(raw_variant, "")
        label = f"iPhone {model}"

        if variant:
            label += f" {variant}"

    if label is None:
        special = re.search(
            r"\biphone\s*(xs\s*max|xs|xr|x|se)\b",
            text,
        )

        if special:
            special_models = {
                "xs max": "XS Max",
                "xs": "XS",
                "xr": "XR",
                "x": "X",
                "se": "SE",
            }

            label = "iPhone " + special_models[
                special.group(1).lower()
            ]

    if label is None:
        return "iPhone non specificato"

    if label.endswith(" e"):
        label = label[:-2] + "e"

    return label

def classify_ps5(text):
    is_slim = "slim" in text
    is_digital = any(word in text for word in (
        "digital", "digitale", "senza lettore", "no lettore"
    ))
    has_disc = (
        any(word in text for word in (
            "disco", "disc edition", "con lettore",
            "standard edition"
        ))
        or re.search(r"\bdisc\b", text) is not None
    )

    if re.search(r"\b(ps5|playstation\s*5)\s+pro\b", text):
        return "PlayStation 5 Pro"

    if is_slim and is_digital:
        return "PS5 Slim Digital"

    if is_slim and has_disc:
        return "PS5 Slim con disco"

    if is_slim:
        return "PS5 Slim non specificata"

    if is_digital:
        return "PS5 Digital"

    if has_disc:
        return "PS5 con disco"

    return "PS5 non specificata"


def classify_switch(text):
    if "switch 2" in text:
        return "Nintendo Switch 2"

    if "oled" in text:
        return "Nintendo Switch OLED"

    if "lite" in text:
        return "Nintendo Switch Lite"

    if re.search(r"\b(v1|prima versione|2017)\b", text):
        return "Nintendo Switch V1"

    if re.search(r"\b(v2|seconda versione|2019)\b", text):
        return "Nintendo Switch V2"

    return "Nintendo Switch non specificata"


def classify_xbox(text):
    if "series s" in text:
        return "Xbox Series S"

    if "series x" in text:
        return "Xbox Series X"

    if "one s" in text:
        return "Xbox One S"

    if "one x" in text:
        return "Xbox One X"

    if "xbox one" in text:
        return "Xbox One"

    if "360" in text:
        return "Xbox 360"

    return "Xbox non specificata"

def is_ps5_accessory(text):
    accessory_terms = (
        "portal", "ssd", "chiavett", "scuf",
        "fanatec", "vr2", "ps vr", "cover"
    )

    if any(term in text for term in accessory_terms):
        return True

    console_details = (
        "digital", "digitale", "disco", "disc",
        "standard edition", "slim", "825gb",
        "825 gb", "1tb", "1 tb", "fat", "con lettore"
    )

    has_console_details = any(
        detail in text for detail in console_details
    )

    if (
        any(word in text for word in ("controller", "dualsense", "volante"))
        and not has_console_details
    ):
        return True

    if (
        re.search(r"\bgiochi?\b", text)
        and not has_console_details
    ):
        return True

    return False    

def classify_ipad(text):
    if "air 4" in text or "air4" in text:
        return "iPad Air 4"

    if (
        "ipad 10" in text
        or "10th generation" in text
        or "10ª generazione" in text
    ):
        return "iPad 10"

    if (
        "ipad 9" in text
        or "nove generazione" in text
        or ("ipad" in text and "2021" in text)
    ):
        return "iPad 9"

    return "iPad non specificato"


def classify_samsung_watch(text):
    if "ultra" in text:
        return "Samsung Galaxy Watch Ultra"

    match = re.search(r"watch\s*(\d+)", text)

    if match:
        return f"Samsung Galaxy Watch {match.group(1)}"

    return "Samsung Galaxy Watch non specificato"


def classify_samsung(text):
    if "chromebook" in text:
        return "Samsung Chromebook"

    if "tv" in text or "monitor" in text:
        return "Samsung TV/Monitor"

    match = re.search(r"\bxcover\s*(\d+)", text)

    if match:
        return f"Samsung Galaxy XCover {match.group(1)}"

    match = re.search(r"\bz\s*fold\s*(\d+)", text)

    if match:
        return f"Samsung Galaxy Z Fold {match.group(1)}"

    match = re.search(r"\bz\s*flip\s*(\d+)", text)

    if match:
        return f"Samsung Galaxy Z Flip {match.group(1)}"

    match = re.search(
        r"\bnote\s*(\d+)\s*(ultra|plus)?",
        text,
    )

    if match:
        label = f"Samsung Galaxy Note {match.group(1)}"

        if match.group(2):
            label += f" {match.group(2).title()}"

        return label

    match = re.search(
        r"\bs\s*(\d+)\s*(ultra|plus|fe)?",
        text,
    )

    if match:
        label = f"Samsung Galaxy S{match.group(1)}"

        if match.group(2):
            label += f" {match.group(2).title()}"

        return label

    match = re.search(r"\ba\s*(\d+)", text)

    if match:
        return f"Samsung Galaxy A{match.group(1)}"

    return "Samsung non specificato"

def product_family(title):
    text = title.lower().strip()

    if re.search(r"\bpsp\s*5\b", text):
        return "PS5 Slim non specificata"

    if "playstation portal" in text:
        return "PlayStation Portal"

    if "vr2" in text or "playstation vr 2" in text:
        return "PlayStation VR2"

    if "aystation 5" in text:
        return classify_ps5(text)

    if "nintendo 2ds" in text:
        return "Nintendo 2DS XL"

    if "nintendo wii" in text:
        return "Nintendo Wii"

    if "insta360" in text:
        return "Insta360"

    if "folletto" in text:
        return "Folletto"

    if "ps5" in text or "playstation 5" in text:
        if is_ps5_accessory(text):
            return "Giochi e accessori"

        return classify_ps5(text)

    # Giochi e accessori
    if any(word in text for word in (
        "giochi ", "gioco ", "controller", "joy-con",
        "dualsense", "dualshock", "custodia", "cuffie",
        "dragon shield", "god of war"
    )):
        return "Giochi e accessori"

    # Orologi
    if (
        "galaxy watch" in text
        or "orologio samsung galaxy" in text
    ):
        return classify_samsung_watch(text)

    if "apple watch" in text or "smartwatch" in text:
        return "Smartwatch"

    # Smartphone e tablet
    if "iphone" in text:
        return classify_iphone(text)

    if "ipad" in text:
        return classify_ipad(text)

    if "galaxy tab" in text:
        return "Samsung Tablet"

    if "samsung" in text or "galaxy" in text:
        return classify_samsung(text)

    # Console

    if "ps4" in text or "playstation 4" in text:
        return "PlayStation 4"

    if (
        "nintendo switch" in text
        or "nontendo switch" in text
        or "switch oled" in text
        or "switch lite" in text
    ):
        return classify_switch(text)

    if "3ds" in text:
        return "Nintendo 3DS"

    if "xbox" in text:
        return classify_xbox(text)

    if "meta quest" in text or "oculus" in text:
        return "Meta Quest"

    # Fotografia e video
    if "gopro" in text or "hero 10" in text or "hero 11" in text:
        return "GoPro"

    if "dji" in text:
        return "DJI"

    if "canon" in text:
        return "Canon"

    if "nikon" in text:
        return "Nikon"

    if (
        "sony" in text
        and any(word in text for word in (
            "obiettivo", "fotocamera", "camera",
            "alpha", "sel-", "fe "
        ))
    ):
        return "Sony fotografia"

    if any(word in text for word in (
        "obiettivo", "sigma ", "tamron "
    )):
        return "Obiettivi fotografici"

    # Computer e componenti
    if "macbook" in text:
        return "MacBook"

    if "lenovo" in text:
        return "Lenovo"

    if any(word in text for word in (
        "rtx", "nvidia", "scheda video",
        "intel core", "ryzen"
    )):
        return "Componenti PC"

    # Altri prodotti ricorrenti
    if "dyson" in text:
        return "Dyson"

    if "lego" in text:
        return "LEGO"

    if "makita" in text:
        return "Makita"

    if "pokemon" in text or "pokémon" in text:
        return "Pokémon"

    return "Altro"


def main():
    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT
                title,
                price,
                posted_at,
                detected_sold_at
            FROM listings
            WHERE posted_at IS NOT NULL
              AND detected_sold_at IS NOT NULL
        """).fetchall()
    finally:
        conn.close()

    products = defaultdict(list)

    for row in rows:
        hours = calculate_hours(
            row["posted_at"],
            row["detected_sold_at"],
        )

        if hours < 0:
            continue

        family = product_family(row["title"])

        products[family].append({
            "hours": hours,
            "price": row["price"],
        })

    results = []

    for family, items in products.items():
        durations = [item["hours"] for item in items]
        prices = [
            item["price"]
            for item in items
            if item["price"] is not None
        ]

        total = len(items)
        within_24h = sum(
            item["hours"] <= 24
            for item in items
        )

        results.append({
            "family": family,
            "total": total,
            "median_hours": median(durations),
            "median_price": median(prices) if prices else None,
            "within_24h": within_24h / total * 100,
        })

    results.sort(
        key=lambda item: item["median_hours"]
    )

    print("\n📦 ANALISI PER PRODOTTO")
    print("=" * 78)
    print(
        f"{'PRODOTTO':<22}"
        f"{'VENDUTI':>8}"
        f"{'TEMPO MEDIANO':>18}"
        f"{'ENTRO 24H':>12}"
        f"{'PREZZO MEDIANO':>18}"
    )
    print("-" * 78)

    for result in results:
        price = (
            f"€{result['median_price']:.2f}"
            if result["median_price"] is not None
            else "-"
        )

        print(
            f"{result['family']:<22}"
            f"{result['total']:>8}"
            f"{format_duration(result['median_hours']):>18}"
            f"{result['within_24h']:>11.1f}%"
            f"{price:>18}"
        )


if __name__ == "__main__":
    main()
