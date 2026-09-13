from bot_message_parser import parse_bot_message
from ingestion import ingest_listing
from database import get_connection


def find_monitoring_id(category: str):
    if not category:
        return None

    category = category.strip()

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT id, name
            FROM monitorings
            WHERE active = 1
              AND UPPER(name) LIKE UPPER(?)
            ORDER BY id
            LIMIT 1
            """,
            (category + "%",),
        ).fetchone()

        if row:
            return row["id"]

        # Se il monitoraggio non esiste, lo creiamo automaticamente.
        cursor = conn.execute(
            """
            INSERT INTO monitorings (
                name,
                url,
                active
            )
            VALUES (?, ?, 1)
            """,
            (
                category,
                "",
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def import_messages(
    messages: str,
    detected_sold_at=None,
):
    blocks = messages.strip().split("\n\n")
    results = []

    for block in blocks:
        if not block.strip():
            continue

        parsed = parse_bot_message(block)

        if not parsed:
            results.append({
                "status": "ERROR",
                "reason": "Messaggio non riconosciuto",
            })
            continue

        category = parsed["monitoring_name"]

        monitoring_id = find_monitoring_id(category)

        if monitoring_id is None:
            results.append({
                "status": "SKIPPED",
                "external_id": parsed["external_id"],
                "title": parsed["title"],
                "category": category,
                "reason": "Categoria mancante",
            })
            continue

        if not parsed["external_id"]:
            results.append({
                "status": "SKIPPED",
                "title": parsed["title"],
                "category": category,
                "reason": "ID annuncio mancante",
            })
            continue

        result = ingest_listing(
            external_id=parsed["external_id"],
            monitoring_id=monitoring_id,
            title=parsed["title"],
            price=parsed["price"],
            url=parsed["url"],
            posted_at=parsed["posted_at"],
            transaction_status="SOLD",
            detected_sold_at=detected_sold_at,
        )

        results.append({
            "status": "IMPORTED",
            "external_id": parsed["external_id"],
            "title": parsed["title"],
            "category": category,
            "monitoring_id": monitoring_id,
            "action": result["action"],
            "listing_id": result["listing_id"],
        })

    return results