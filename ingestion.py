from datetime import datetime
from typing import Optional

from database import get_connection


def ingest_listing(
    external_id: str,
    monitoring_id: int,
    title: str,
    price: Optional[float] = None,
    url: Optional[str] = None,
    location: Optional[str] = None,
    posted_at: Optional[str] = None,
    body: Optional[str] = None,
    transaction_status: str = "ACTIVE",
    photos: Optional[list[str]] = None,
    detected_sold_at: Optional[str] = None,
):
    """
    Inserisce o aggiorna un annuncio nel database locale.

    Regole:
    - nuovo annuncio -> evento FOUND
    - annuncio già presente -> aggiorna i dati
    - se il prezzo cambia -> registra il nuovo prezzo
    - se passa da ACTIVE a SOLD -> registra detected_sold_at
    - import storico già SOLD -> detected_sold_at resta NULL
    - nuovo messaggio live -> detected_sold_at viene passato dal reader
    - le foto vengono salvate una sola volta
    """

    now = datetime.now().isoformat()
    new_status = transaction_status.upper()

    conn = get_connection()

    try:
        existing = conn.execute(
            """
            SELECT
                id,
                price,
                transaction_status,
                detected_sold_at,
                imported_at
            FROM listings
            WHERE external_id = ?
              AND monitoring_id = ?
            """,
            (
                str(external_id).strip(),
                monitoring_id,
            ),
        ).fetchone()

        # ---------------------------------------------------------
        # NUOVO ANNUNCIO
        # ---------------------------------------------------------
        if existing is None:

            # Se è un import storico, il valore sarà None.
            # Se è un messaggio live, arriva il timestamp Telegram.
            detected_sold_at_value = detected_sold_at

            cursor = conn.execute(
                """
                INSERT INTO listings (
                    external_id,
                    monitoring_id,
                    title,
                    url,
                    price,
                    location,
                    posted_at,
                    first_seen_at,
                    last_seen_at,
                    transaction_status,
                    body,
                    created_at,
                    updated_at,
                    detected_sold_at,
                    imported_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(external_id).strip(),
                    monitoring_id,
                    title.strip(),
                    url,
                    price,
                    location,
                    posted_at,
                    now,
                    now,
                    new_status,
                    body,
                    now,
                    now,
                    detected_sold_at_value,
                    now,
                ),
            )

            listing_id = cursor.lastrowid

            conn.execute(
                """
                INSERT INTO listing_events (
                    listing_id,
                    event_type,
                    event_at,
                    price
                )
                VALUES (?, 'FOUND', ?, ?)
                """,
                (
                    listing_id,
                    now,
                    price,
                ),
            )

            if price is not None:
                conn.execute(
                    """
                    INSERT INTO price_history (
                        listing_id,
                        price,
                        recorded_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        listing_id,
                        price,
                        now,
                    ),
                )

            if photos:
                for position, photo_url in enumerate(photos):
                    conn.execute(
                        """
                        INSERT INTO listing_photos (
                            listing_id,
                            url,
                            position
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            listing_id,
                            photo_url,
                            position,
                        ),
                    )

            conn.commit()

            return {
                "action": "created",
                "listing_id": listing_id,
            }

        # ---------------------------------------------------------
        # ANNUNCIO ESISTENTE
        # ---------------------------------------------------------

        listing_id = existing["id"]
        old_price = existing["price"]
        old_status = (
            existing["transaction_status"] or "ACTIVE"
        ).upper()

        detected_sold_at_existing = existing["detected_sold_at"]

        # L'annuncio è passato da ACTIVE a SOLD.
        became_sold = (
            new_status == "SOLD"
            and old_status != "SOLD"
        )

        if new_status == "SOLD" and detected_sold_at_existing is None:

            if detected_sold_at is not None:
                detected_sold_at_existing = detected_sold_at
            elif became_sold:
                detected_sold_at_existing = now

        conn.execute(
            """
            UPDATE listings
            SET
                title = ?,
                url = ?,
                price = ?,
                location = ?,
                posted_at = ?,
                last_seen_at = ?,
                transaction_status = ?,
                body = ?,
                updated_at = ?,
                detected_sold_at = ?,
                imported_at = ?
            WHERE id = ?
            """,
            (
                title.strip(),
                url,
                price,
                location,
                posted_at,
                now,
                new_status,
                body,
                now,
                detected_sold_at_existing,
                now,
                listing_id,
            ),
        )

        # ---------------------------------------------------------
        # CAMBIO PREZZO
        # ---------------------------------------------------------

        if (
            price is not None
            and old_price is not None
            and float(price) != float(old_price)
        ):
            conn.execute(
                """
                INSERT INTO price_history (
                    listing_id,
                    price,
                    recorded_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    listing_id,
                    price,
                    now,
                ),
            )

        # ---------------------------------------------------------
        # PASSAGGIO ACTIVE -> SOLD
        # ---------------------------------------------------------

        if became_sold:
            conn.execute(
                """
                INSERT INTO listing_events (
                    listing_id,
                    event_type,
                    event_at,
                    price
                )
                VALUES (?, 'SOLD', ?, ?)
                """,
                (
                    listing_id,
                    detected_sold_at_existing,
                    price,
                ),
            )

        conn.commit()

        return {
            "action": "updated",
            "listing_id": listing_id,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()