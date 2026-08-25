from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.inquiry_service import create_inquiry
from app.services.product_service import get_product

AWAITING_COLOR = 1


async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":", 1)[1])

    async with AsyncSessionLocal() as db:
        product = await get_product(db, product_id)

    if not product:
        await query.edit_message_text("Sorry, that product is no longer available.")
        return

    specs_lines = "\n".join(f"• {k}: {v}" for k, v in (product.specs or {}).items())
    colors = ", ".join(product.colors) if product.colors else "N/A"
    price_line = f"{product.price} ETB"
    if product.discount_price:
        price_line = f"~{product.price} ETB~ → *{product.discount_price} ETB*"

    text = (
        f"*{product.name}*\n\n"
        f"{price_line}\n"
        f"Colors: {colors}\n"
        f"{specs_lines}\n\n"
        f"{'✅ In Stock' if product.in_stock else '❌ Out of Stock'}"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Request Delivery", callback_data=f"deliver:{product.id}")],
        [InlineKeyboardButton("📞 Call Shop Now", url=f"tel:{settings.shop_phone}")],
    ]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def request_delivery_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":", 1)[1])
    context.user_data["pending_product_id"] = product_id

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="What color would you like? (or type 'any' if no preference)",
    )
    return AWAITING_COLOR


async def request_delivery_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    color = update.message.text.strip()
    product_id = context.user_data.pop("pending_product_id", None)
    user = update.effective_user

    async with AsyncSessionLocal() as db:
        inquiry = await create_inquiry(
            db,
            customer_telegram_id=user.id,
            customer_username=user.username,
            product_id=product_id,
            preferred_color=None if color.lower() == "any" else color,
        )
        product = await get_product(db, product_id)

    await update.message.reply_text(
        f"✅ Got it! *{settings.shop_name}* will reach out within minutes.\n"
        f"Reference: *#{inquiry.reference_code}*\n\n"
        f"Prefer to skip the wait? Call {settings.shop_phone} directly.",
        parse_mode="Markdown",
    )

    if settings.telegram_owner_id:
        username_note = f"@{user.username}" if user.username else f"id {user.id}"
        await context.bot.send_message(
            chat_id=settings.telegram_owner_id,
            text=(
                f"🔔 New delivery request\n"
                f"Product: {product.name if product else product_id}\n"
                f"Customer: {username_note}\n"
                f"Color: {color}\n"
                f"Reference: #{inquiry.reference_code}"
            ),
        )

    return ConversationHandler.END


async def request_delivery_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("pending_product_id", None)
    await update.message.reply_text("No problem, cancelled.")
    return ConversationHandler.END
