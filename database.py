import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "market.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_database():
    conn = get_connection()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS monitorings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT NOT NULL,
            monitoring_id INTEGER,
            title TEXT NOT NULL,
            url TEXT,
            price REAL,
            location TEXT,
            posted_at TEXT,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TEXT,
            transaction_status TEXT,
            body TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(external_id, monitoring_id),

            FOREIGN KEY (monitoring_id)
                REFERENCES monitorings(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS listing_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY (listing_id)
                REFERENCES listings(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS listing_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            price REAL,

            FOREIGN KEY (listing_id)
                REFERENCES listings(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            price REAL NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (listing_id)
                REFERENCES listings(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS monitoring_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitoring_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(monitoring_id, word),

            FOREIGN KEY (monitoring_id)
                REFERENCES monitorings(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS listing_exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            monitoring_id INTEGER,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (listing_id)
                REFERENCES listings(id)
                ON DELETE CASCADE,

            FOREIGN KEY (monitoring_id)
                REFERENCES monitorings(id)
                ON DELETE SET NULL
        );
    """)

    # Migrazione: date relative alla rilevazione delle vendite
    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(listings)").fetchall()
    }

    if "detected_sold_at" not in existing_columns:
        conn.execute(
            "ALTER TABLE listings ADD COLUMN detected_sold_at TEXT"
        )

    if "imported_at" not in existing_columns:
        conn.execute(
            "ALTER TABLE listings ADD COLUMN imported_at TEXT"
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
    print(f"Database inizializzato: {DB_PATH}")