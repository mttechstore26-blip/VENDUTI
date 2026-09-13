import re
from typing import Optional


def parse_bot_message(message: str) -> Optional[dict]:
    """
    Analizza un singolo messaggio del bot dei venduti.
    Supporta sia il formato normale sia il formato Markdown di Telegram.
    """

    if not message or not message.strip():
        return None

    text = message.strip()

    # ---------------------------------------------------------
    # TITOLO + URL
    # Formato Markdown:
    # 📦 [**Titolo**](https://www.subito.it/...)
    #
    # Formato normale:
    # 📦 Titolo
    # URL: https://www.subito.it/...
    # ---------------------------------------------------------

    title = None
    url = None

    markdown_title_match = re.search(
        r"📦\s*\[\*\*(.*?)\*\*\]\((https?://www\.subito\.it/[^\s)]+)\)",
        text,
        re.DOTALL,
    )

    if markdown_title_match:
        title = markdown_title_match.group(1).strip()
        url = markdown_title_match.group(2).strip()

    else:
        title_match = re.search(
            r"📦\s*(.+?)(?:\n|$)",
            text,
        )

        url_match = re.search(
            r"URL:\s*(https?://www\.subito\.it/[^\s\]\)]+)",
            text,
        )

        if title_match:
            title = title_match.group(1).strip()

        if url_match:
            url = url_match.group(1).strip()

    if not title or not url:
        return None

    # ---------------------------------------------------------
    # PREZZO
    # Supporta:
    # 💰 140 €
    # 💰 **140 €**
    # ---------------------------------------------------------

    price_match = re.search(
        r"💰\s*(?:\*\*)?([\d.,]+)\s*€",
        text,
    )

    price = None

    if price_match:
        price_text = (
            price_match.group(1)
            .replace(".", "")
            .replace(",", ".")
        )

        try:
            price = float(price_text)
        except ValueError:
            price = None

    # ---------------------------------------------------------
    # DATA DI PUBBLICAZIONE
    # ---------------------------------------------------------

    posted_match = re.search(
        r"⏰\s*(?:\*\*)?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        text,
    )

    posted_at = None

    if posted_match:
        posted_at = posted_match.group(1)

    # ---------------------------------------------------------
    # CATEGORIA
    #
    # Markdown:
    # ▪️ [COLLEZIONISMO]
    #
    # Normale:
    # ▪️ COLLEZIONISMO
    # ---------------------------------------------------------

    category_match = re.search(
        r"▪️\s*(?:\[([^\]]+)\]|(.+?))\s*$",
        text,
        re.MULTILINE,
    )

    monitoring_name = None

    if category_match:
        monitoring_name = (
            category_match.group(1)
            or category_match.group(2)
        ).strip()

    # ---------------------------------------------------------
    # ID ANNUNCIO SUBITO
    # ---------------------------------------------------------

    external_id = None

    id_match = re.search(
        r"-(\d+)\.htm",
        url,
    )

    if id_match:
        external_id = id_match.group(1)

    return {
        "external_id": external_id,
        "title": title,
        "url": url,
        "price": price,
        "posted_at": posted_at,
        "monitoring_name": monitoring_name,
    }


def parse_bot_messages(messages: str) -> list[dict]:
    """
    Analizza più messaggi del bot presenti nello stesso testo.
    """

    if not messages or not messages.strip():
        return []

    blocks = re.split(
        r"(?=📦\s*)",
        messages.strip(),
    )

    results = []

    for block in blocks:
        if not block.strip():
            continue

        parsed = parse_bot_message(block)

        if parsed:
            results.append(parsed)

    return results