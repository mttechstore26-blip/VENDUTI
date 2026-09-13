from collections import Counter
from datetime import datetime, timezone
from statistics import median
from zoneinfo import ZoneInfo

from database import get_connection


ROME = ZoneInfo("Europe/Rome")

BANDS = [
    ("🔥 Entro 3 ore", 3),
    ("⚡ 3–6 ore", 6),
    ("🟢 6–10 ore", 10),
    ("🟡 10–24 ore", 24),
    ("🟠 1–3 giorni", 72),
    ("🔴 Oltre 3 giorni", float("inf")),
]


def calculate_hours(posted_at, detected_sold_at):
    posted = datetime.fromisoformat(posted_at)
    detected = datetime.fromisoformat(detected_sold_at)

    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=ROME)

    if detected.tzinfo is None:
        detected = detected.replace(tzinfo=timezone.utc)

    difference = (
        detected.astimezone(timezone.utc)
        - posted.astimezone(timezone.utc)
    )

    return difference.total_seconds() / 3600


def classify_speed(hours):
    for label, maximum_hours in BANDS:
        if hours <= maximum_hours:
            return label

    return "🔴 Oltre 3 giorni"


def format_duration(hours):
    if hours < 24:
        return f"{hours:.1f} ore"

    return f"{hours / 24:.1f} giorni"


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

    counts = Counter()
    durations = []
    valid_rows = []

    for row in rows:
        hours = calculate_hours(
            row["posted_at"],
            row["detected_sold_at"],
        )

        if hours < 0:
            continue

        label = classify_speed(hours)
        counts[label] += 1
        durations.append(hours)
        valid_rows.append((hours, row))

    total = len(valid_rows)

    print("\n📊 REPORT VELOCITÀ DI VENDITA")
    print("=" * 50)
    print(f"Annunci analizzati: {total}")

    if not total:
        print("Nessun annuncio disponibile.")
        return

    print(f"Tempo mediano: {format_duration(median(durations))}")

    print("\nDISTRIBUZIONE")
    print("-" * 50)

    for label, _ in BANDS:
        amount = counts[label]
        percentage = amount / total * 100
        print(f"{label}: {amount} ({percentage:.1f}%)")

    print("\n10 ANNUNCI PIÙ VELOCI")
    print("-" * 50)

    for hours, row in sorted(valid_rows, key=lambda item: item[0])[:10]:
        print(
            f"{format_duration(hours):>10} | "
            f"{row['title']} | €{row['price'] or 0:.2f}"
        )


if __name__ == "__main__":
    main()
