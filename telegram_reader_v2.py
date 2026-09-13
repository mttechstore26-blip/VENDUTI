import asyncio
from pathlib import Path

from telethon import TelegramClient, events

from importer import import_messages
from database import get_connection


API_ID = 23825615
API_HASH = "cd2ef60a7380768e30fe5514da7143e6"

CHAT = "@subitovendutibot"

SESSION_PATH = str(
    Path(__file__).resolve().parent / "venduti_session"
)

client = TelegramClient(
    SESSION_PATH,
    API_ID,
    API_HASH
)


def get_last_message_id():
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telegram_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_message_id INTEGER
            )
        """)

        row = conn.execute("""
            SELECT last_message_id
            FROM telegram_state
            WHERE id = 1
        """).fetchone()

        if row is None:
            return 0

        return row["last_message_id"] or 0

    finally:
        conn.close()


def save_last_message_id(message_id):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO telegram_state (id, last_message_id)
            VALUES (1, ?)
            ON CONFLICT(id)
            DO UPDATE SET last_message_id = excluded.last_message_id
        """, (message_id,))

        conn.commit()

    finally:
        conn.close()


def already_imported(message_id):
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telegram_messages (
                message_id INTEGER PRIMARY KEY,
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        row = conn.execute("""
            SELECT message_id
            FROM telegram_messages
            WHERE message_id = ?
        """, (message_id,)).fetchone()

        return row is not None

    finally:
        conn.close()


def mark_imported(message_id):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT OR IGNORE INTO telegram_messages (message_id)
            VALUES (?)
        """, (message_id,))

        conn.commit()

    finally:
        conn.close()


async def process_message(
    message,
    live=False,
):
    message_id = message.id

    if already_imported(message_id):
        return

    text = message.text or ""

    if not text.strip():
        save_last_message_id(message_id)
        mark_imported(message_id)
        return

    print("\n" + "=" * 70)
    print("📩 NUOVO MESSAGGIO DA SUBITO VENDUTI")
    print("=" * 70)
    print(text)
    print("=" * 70)

    try:
        detected_sold_at = None

        if getattr(message, "date", None) is not None:
            detected_sold_at = message.date.isoformat()

        results = import_messages(
            text,
            detected_sold_at=detected_sold_at,
        )

        for result in results:
            print("📥", result)

        mark_imported(message_id)
        save_last_message_id(message_id)

        print(f"✅ Messaggio Telegram {message_id} elaborato")

    except Exception as exc:
        print(f"❌ Errore importando messaggio {message_id}: {exc}")


async def import_history():
    from datetime import datetime, timezone

    start_date = datetime(
        2026, 9, 10,
        tzinfo=timezone.utc
    )

    print("🔎 Recupero messaggi ricevuti dal 10/09/2026...")
    print(f"📅 Data iniziale: {start_date}")

    imported_count = 0

    async for message in client.iter_messages(
        CHAT,
        offset_date=start_date,
        reverse=True
    ):
        await process_message(message)
        imported_count += 1

    print(
        f"✅ Recupero storico completato. "
        f"Messaggi controllati: {imported_count}"
    )


@client.on(events.NewMessage(chats=CHAT))
async def new_message_handler(event):
    await process_message(
        event.message,
        live=True,
    )


async def main():
    print("🔌 Connessione a Telegram...")

    await client.start()

    print("✅ Telegram collegato")
    print(f"📡 Chat monitorata: {CHAT}")

    await import_history()

    print("👂 In ascolto dei nuovi messaggi...")
    print("⏹️ Premi CTRL+C per fermare")

    await client.run_until_disconnected()


try:
    client.loop.run_until_complete(main())

except KeyboardInterrupt:
    print("\n🛑 Reader fermato")

finally:
    client.disconnect()
