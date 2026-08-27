import httpx

from app.core.config import settings


async def notify_owner(text: str) -> None:
    """Send a plain text message to the shop owner via Telegram's HTTP API directly —
    used when the FastAPI process needs to notify without going through the bot's
    own polling/webhook Application (e.g. inquiries created via the Mini App API)."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": settings.telegram_owner_id, "text": text})
