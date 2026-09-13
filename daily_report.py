import argparse
import html
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from database import get_connection
from market_overview import broad_family
from product_analysis import product_family
from sales_speed import calculate_hours, format_duration


ROME = ZoneInfo("Europe/Rome")
ENV_PATH = Path("/opt/SubitoBot/.env")


def load_env():
    values = {}

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip("\"'")

    return values


def get_unique_listings():
    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT
                external_id,
                title,
                price,
                posted_at,
                detected_sold_at
            FROM listings
            WHERE posted_at IS NOT NULL
              AND detected_sold_at IS NOT NULL
            ORDER BY detected_sold_at
        """).fetchall()
    finally:
        conn.close()

    unique = {}

    for row in rows:
        unique.setdefault(row["external_id"], row)

    return list(unique.values())


def detected_date(row):
    detected = datetime.fromisoformat(row["detected_sold_at"])
    return detected.astimezone(ROME).date()


def build_daily_report(target_date):
    all_rows = get_unique_listings()

    rows = [
        row for row in all_rows
        if detected_date(row) == target_date
    ]

    if not rows:
        return (
            f"📊 <b>REPORT GIORNALIERO</b>\n"
            f"📅 {target_date.strftime('%d/%m/%Y')}\n\n"
            f"Nessun annuncio venduto rilevato."
        )

    analysed = []

    for row in rows:
        hours = calculate_hours(
            row["posted_at"],
            row["detected_sold_at"],
        )

        if hours < 0:
            continue

        detailed = product_family(row["title"])
        broad = broad_family(detailed)

        analysed.append({
            "title": row["title"],
            "price": row["price"],
            "hours": hours,
            "detailed": detailed,
            "broad": broad,
        })

    total = len(analysed)
    durations = [item["hours"] for item in analysed]
    prices = [
        item["price"]
        for item in analysed
        if item["price"] is not None
    ]

    broad_counts = Counter(
        item["broad"] for item in analysed
    )
    model_counts = Counter(
        item["detailed"] for item in analysed
    )

    fastest = min(
        analysed,
        key=lambda item: item["hours"],
    )

    within_24h = (
        sum(item["hours"] <= 24 for item in analysed)
        / total
        * 100
    )

    previous_start = target_date - timedelta(days=7)

    previous_count = sum(
        previous_start <= detected_date(row) < target_date
        for row in all_rows
    )

    daily_average = previous_count / 7

    if daily_average:
        difference = (total - daily_average) / daily_average * 100
        comparison = f"{difference:+.1f}% rispetto alla media dei 7 giorni"
    else:
        comparison = "Confronto settimanale non ancora disponibile"

    lines = [
        "📊 <b>REPORT GIORNALIERO MT TECH</b>",
        f"📅 {target_date.strftime('%d/%m/%Y')}",
        "",
        f"📦 Venduti rilevati: <b>{total}</b>",
        f"⏱ Tempo mediano: <b>{format_duration(median(durations))}</b>",
        f"⚡ Entro 24 ore: <b>{within_24h:.1f}%</b>",
        f"💶 Prezzo mediano: <b>€{median(prices):.2f}</b>",
        f"📈 Andamento: <b>{comparison}</b>",
        "",
        "🏆 <b>PRODOTTI PIÙ VENDUTI</b>",
    ]

    for product, amount in broad_counts.most_common(5):
        lines.append(f"• {html.escape(product)}: {amount}")

    lines.extend([
        "",
        "🔎 <b>MODELLI PIÙ VENDUTI</b>",
    ])

    for model, amount in model_counts.most_common(5):
        lines.append(f"• {html.escape(model)}: {amount}")

    lines.extend([
        "",
        "🚀 <b>ANNUNCIO PIÙ VELOCE</b>",
        f"• {html.escape(fastest['title'])}",
        f"• Tempo: {format_duration(fastest['hours'])}",
        f"• Prezzo: €{fastest['price']:.2f}",
    ])

    unclassified = broad_counts.get("Altro", 0)

    if unclassified:
        lines.extend([
            "",
            f"⚠️ Da classificare: {unclassified}",
        ])

    return "\n".join(lines)


def send_telegram(message):
    env = load_env()

    token = (
        env.get("TELEGRAM_WA_BOT_TOKEN")
        or env.get("TELEGRAM_BOT_TOKEN")
    )
    chat_id = (
        env.get("TELEGRAM_WA_CHAT_ID")
        or env.get("TELEGRAM_CHAT_ID")
    )

    if not token or not chat_id:
        raise RuntimeError("Configurazione Telegram mancante")

    data = urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }).encode()

    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
    )

    with urlopen(request, timeout=30) as response:
        response.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    target_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ROME).date() - timedelta(days=1)
    )

    report = build_daily_report(target_date)
    print(report)

    if args.send:
        send_telegram(report)
        print("\n✅ Report inviato su Telegram")


if __name__ == "__main__":
    main()