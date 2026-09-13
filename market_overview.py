from collections import defaultdict
from statistics import median

from database import get_connection
from product_analysis import product_family
from sales_speed import calculate_hours, format_duration


def broad_family(detailed_family):
    if detailed_family.startswith("iPhone"):
        return "iPhone"

    if (
        detailed_family.startswith("PS5")
        or detailed_family.startswith("PlayStation 5")
    ):
        return "PlayStation 5"

    if detailed_family.startswith("Nintendo Switch"):
        return "Nintendo Switch"

    if detailed_family.startswith("Xbox"):
        return "Xbox"

    if detailed_family.startswith("iPad"):
        return "iPad"

    if detailed_family.startswith("Samsung Galaxy Watch"):
        return "Smartwatch"

    if detailed_family.startswith("Samsung Galaxy"):
        return "Samsung Smartphone"

    if detailed_family in (
        "Canon",
        "Nikon",
        "Sony fotografia",
        "Obiettivi fotografici",
        "Insta360",
    ):
        return "Fotografia"

    if detailed_family in (
        "Dyson",
        "Folletto",
    ):
        return "Elettrodomestici"
    return detailed_family


def reliability(total):
    if total >= 10:
        return "Più significativo"

    if total >= 5:
        return "Preliminare"

    if total >= 2:
        return "Debole"

    return "Insufficiente"


def main():
    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT title, price, posted_at, detected_sold_at
            FROM listings
            WHERE posted_at IS NOT NULL
              AND detected_sold_at IS NOT NULL
        """).fetchall()
    finally:
        conn.close()

    groups = defaultdict(list)

    for row in rows:
        hours = calculate_hours(
            row["posted_at"],
            row["detected_sold_at"],
        )

        if hours < 0:
            continue

        detailed = product_family(row["title"])
        family = broad_family(detailed)

        groups[family].append({
            "hours": hours,
            "price": row["price"],
        })

    results = []

    for family, items in groups.items():
        durations = [item["hours"] for item in items]
        prices = [
            item["price"]
            for item in items
            if item["price"] is not None
        ]

        total = len(items)
        within_24h = (
            sum(item["hours"] <= 24 for item in items)
            / total
            * 100
        )

        results.append({
            "family": family,
            "total": total,
            "median_hours": median(durations),
            "within_24h": within_24h,
            "median_price": median(prices) if prices else None,
            "reliability": reliability(total),
        })

    results.sort(
        key=lambda result: (
            -result["total"],
            result["median_hours"],
        )
    )

    print("\n📊 PANORAMICA GENERALE DEL MERCATO")
    print("=" * 105)
    print(
        f"{'PRODOTTO':<24}"
        f"{'VENDUTI':>8}"
        f"{'TEMPO MEDIANO':>18}"
        f"{'ENTRO 24H':>12}"
        f"{'PREZZO':>14}  " 
        f"{'CAMPIONE':>20}" 
    )
    print("-" * 105)

    for result in results:
        price = (
            f"€{result['median_price']:.2f}"
            if result["median_price"] is not None
            else "-"
        )

        print(
            f"{result['family']:<24}"
            f"{result['total']:>8}"
            f"{format_duration(result['median_hours']):>18}"
            f"{result['within_24h']:>11.1f}%"
            f"{price:>14}  " 
            f"{result['reliability']:>20}"
        )


if __name__ == "__main__":
    main()
