import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from app.core.config import settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Customer entry point — opens the Telegram Mini App for browsing.
    All product browsing, filtering, and comparing now happens inside the
    Mini App (static/index.html), which talks to the /api/* endpoints.

    The ?v= timestamp is a cache-buster: Telegram's in-app browser caches
    Mini App pages aggressively, so without a changing query param it can
    keep showing an old version even after the server is updated.
    """
    miniapp_url = f"{settings.miniapp_url}/app/?v={int(time.time())}"
    keyboard = [[InlineKeyboardButton("🛍️ Open Shop", web_app=WebAppInfo(url=miniapp_url))]]
    await update.message.reply_text(
        f"👋 Welcome to *{settings.shop_name}*!\n\n"
        "Tap below to browse phones, laptops, earphones, and accessories — "
        "check prices, colors, and request delivery right from the app.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )