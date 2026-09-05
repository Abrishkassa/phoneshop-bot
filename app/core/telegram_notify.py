import httpx

from app.core.config import settings


async def notify_owner(text: str, reply_markup: dict | None = None) -> None:
    """Send a message to the shop owner via Telegram's HTTP API directly —
    used when the FastAPI process needs to notify without going through the
    bot's own polling/webhook Application (e.g. inquiries created via the
    Mini App API). Optionally attaches an inline keyboard (e.g. a "Mark as
    Sold" button) — taps on it are still delivered to and handled by the
    bot's own polling Application, since it's the same bot token."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": settings.telegram_owner_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload)