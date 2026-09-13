from collections import defaultdict
from statistics import median

from database import get_connection
from product_analysis import product_family, extract_storage
from sales_speed import calculate_hours, format_duration


def main():
    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT title, price, posted_at, detected_sold_at
            FROM listings
            WHERE detected_sold_at IS NOT NULL
              AND 
              R(title) LIKE '%iphone%'
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

        model = product_family(row["title"])
        storage = extract_storage(row["title"]) or "Memoria n/d"

        groups[(model, storage)].append({
            "hours": hours,
            "price": row["price"],
        })

    print("\n📱 ANALISI IPHONE PER MODELLO E MEMORIA")
    print("=" * 88)
    print(
        f"{'MODELLO':<24}"
        f"{'MEMORIA':<14}"
        f"{'VENDUTI':>8}"
        f"{'TEMPO MEDIANO':>18}"
        f"{'ENTRO 24H':>12}"
        f"{'PREZZO':>12}"
    )
    print("-" * 88)

    for (model, storage), items in sorted(groups.items()):
        durations = [item["hours"] for item in items]
        prices = [
            item["price"]
            for item in items
            if item["price"] is not None
        ]

        total = len(items)
        within_24h = sum(
            item["hours"] <= 24 for item in items
        ) / total * 100

        median_price = median(prices) if prices else None
        price = (
            f"€{median_price:.2f}"
            if median_price is not None
            else "-"
        )

        print(
            f"{model:<24}"
            f"{storage:<14}"
            f"{total:>8}"
            f"{format_duration(median(durations)):>18}"
            f"{within_24h:>11.1f}%"
            f"{price:>12}"
        )


if __name__ == "__main__":
    main()