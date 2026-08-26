from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import AsyncSessionLocal
from app.services.product_service import get_product


async def compare_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """First 'Compare' tap — remember this product, ask the customer to pick a second one."""
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":", 1)[1])

    pending = context.user_data.get("compare_product_id")

    if pending is None or pending == product_id:
        context.user_data["compare_product_id"] = product_id
        async with AsyncSessionLocal() as db:
            product = await get_product(db, product_id)
        name = product.name if product else f"#{product_id}"
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Comparing *{name}* — now open another product and tap Compare on it too.",
            parse_mode="Markdown",
        )
        return

    # Second product picked — show the comparison.
    async with AsyncSessionLocal() as db:
        product_a = await get_product(db, pending)
        product_b = await get_product(db, product_id)

    context.user_data.pop("compare_product_id", None)

    if not product_a or not product_b:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="One of those products is no longer available.",
        )
        return

    def price_of(p):
        return p.discount_price if p.discount_price else p.price

    def specs_of(p):
        return ", ".join(f"{k}: {v}" for k, v in (p.specs or {}).items()) or "—"

    text = (
        f"*Comparing*\n\n"
        f"*{product_a.name}* vs *{product_b.name}*\n\n"
        f"💰 Price: {price_of(product_a)} ETB  vs  {price_of(product_b)} ETB\n"
        f"🎨 Colors: {', '.join(product_a.colors) or '—'}  vs  {', '.join(product_b.colors) or '—'}\n"
        f"📦 Stock: {product_a.stock_qty}  vs  {product_b.stock_qty}\n"
        f"🔧 Specs A: {specs_of(product_a)}\n"
        f"🔧 Specs B: {specs_of(product_b)}"
    )
    await context.bot.send_message(chat_id=query.message.chat_id, text=text, parse_mode="Markdown")