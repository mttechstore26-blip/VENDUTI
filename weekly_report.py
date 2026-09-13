import argparse
import html
from collections import Counter
from datetime import date, datetime, timedelta
from statistics import median
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from daily_report import (
    ROME,
    load_env,
    get_unique_listings,
    detected_date,
)
from market_overview import broad_family
from product_analysis import product_family
from sales_speed import calculate_hours, format_duration


def build_weekly_report(end_date):
    start_date = end_date - timedelta(days=7)
    all_rows = get_unique_listings()

    rows = [
        row for row in all_rows
        if start_date <= detected_date(row) < end_date
    ]

    analysed = []

    for row in rows:
        hours = calculate_hours(
            row["posted_at"],
            row["detected_sold_at"],
        )

        if hours < 0:
            continue

        detailed = product_family(row["title"])
        analysed.append({
            "title": row["title"],
            "price": row["price"],
            "hours": hours,
            "broad": broad_family(detailed),
            "detailed": detailed,
        })

    if not analysed:
        return (
            "📊 <b>REPORT SETTIMANALE MT TECH</b>\n\n"
            "Nessun annuncio venduto rilevato."
        )

    total = len(analysed)
    products = Counter(item["broad"] for item in analysed)
    models = Counter(item["detailed"] for item in analysed)

    durations = [item["hours"] for item in analysed]
    prices = [
        item["price"]
        for item in analysed
        if item["price"] is not None
    ]

    fastest = min(analysed, key=lambda item: item["hours"])
    within_24h = sum(item["hours"] <= 24 for item in analysed) / total * 100

    lines = [
        "📊 <b>REPORT SETTIMANALE MT TECH</b>",
        f"📅 {start_date.strftime('%d/%m/%Y')} – "
        f"{(end_date - timedelta(days=1)).strftime('%d/%m/%Y')}",
        "",
        f"📦 Annunci venduti: <b>{total}</b>",
        f"⏱ Tempo mediano di vendita: <b>{format_duration(median(durations))}</b>",
        f"⚡ Venduti entro 24 ore: <b>{within_24h:.1f}%</b>",
        f"💶 Prezzo mediano: <b>€{median(prices):.2f}</b>",
        "",
        "🏆 <b>PRODOTTI PIÙ VENDUTI</b>",
    ]

    for product, amount in products.most_common(10):
        lines.append(f"• {html.escape(product)}: {amount}")

    lines.extend([
        "",
        "🚀 <b>PRODOTTI PIÙ VELOCI</b>",
    ])

    fastest_products = []

    for product, amount in products.items():
        product_rows = [
            item for item in analysed
            if item["broad"] == product
        ]

        if len(product_rows) >= 2:
            median_hours = median(
                item["hours"] for item in product_rows
            )
            fastest_products.append(
                (median_hours, product, amount)
            )

    fastest_products.sort()

    for median_hours, product, amount in fastest_products[:5]:
        lines.append(
            f"• {html.escape(product)}: "
            f"{format_duration(median_hours)} "
            f"({amount} venduti)"
        )

    lines.extend([
        "",
        "🔎 <b>MODELLI PIÙ VENDUTI</b>",
    ])

    for model, amount in models.most_common(10):
        lines.append(f"• {html.escape(model)}: {amount}")

    lines.extend([
        "",
        "🚀 <b>ANNUNCIO PIÙ VELOCE DELLA SETTIMANA</b>",
        f"• {html.escape(fastest['title'])}",
        f"• Tempo: {format_duration(fastest['hours'])}",
        f"• Prezzo: €{fastest['price']:.2f}",
    ])

    unclassified = products.get("Altro", 0)

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

    end_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ROME).date()
    )

    report = build_weekly_report(end_date)
    print(report)

    if args.send:
        send_telegram(report)
        print("\n✅ Report inviato su Telegram")


if __name__ == "__main__":
    main()