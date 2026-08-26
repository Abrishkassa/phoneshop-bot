from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.product_service import list_products_by_category_and_price

CATEGORY_LABELS = {
    "phone": "📱 Phones",
    "earphone": "🎧 Earphones",
    "accessory": "🔌 Accessories",
}

PRICE_FILTER_LABELS = {
    "under10k": "Under 10k ETB",
    "10to20k": "10k–20k ETB",
    "over20k": "20k+ ETB",
    "all": "All prices",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"category:{key}")]
        for key, label in CATEGORY_LABELS.items()
    ]
    await update.message.reply_text(
        f"👋 Welcome to *{settings.shop_name}*!\n\n"
        "Browse our products below, check prices and colors, "
        "and request delivery when you're ready — no need to call first.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def browse_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Category tapped — show price filter options before listing products."""
    query = update.callback_query
    await query.answer()
    category = query.data.split(":", 1)[1]

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"filter:{category}:{key}")]
        for key, label in PRICE_FILTER_LABELS.items()
    ]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"{CATEGORY_LABELS.get(category, category)} — filter by price:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def filter_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Price filter tapped — actually list matching products."""
    query = update.callback_query
    await query.answer()
    _, category, price_key = query.data.split(":", 2)

    async with AsyncSessionLocal() as db:
        products = await list_products_by_category_and_price(db, category, price_key)

    if not products:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"No {CATEGORY_LABELS.get(category, category)} found in that price range.",
        )
        return

    for product in products:
        stock_note = "In Stock" if product.in_stock else "Out of Stock"
        if 0 < product.stock_qty <= 2:
            stock_note = f"⚡ Only {product.stock_qty} left"

        price_line = f"{product.price} ETB"
        if product.discount_price:
            price_line = f"~{product.price} ETB~ → *{product.discount_price} ETB*"

        featured_tag = "🔥 " if product.is_featured else ""

        text = (
            f"{featured_tag}*{product.name}*\n"
            f"{price_line}\n"
            f"{stock_note}"
        )
        keyboard = [[InlineKeyboardButton("View Details", callback_data=f"product:{product.id}")]]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )