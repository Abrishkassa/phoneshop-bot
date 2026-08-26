from telegram import Update
from telegram.ext import ContextTypes

from app.bot.access import owner_only
from app.core.database import AsyncSessionLocal
from app.services.product_service import list_all_products, set_price, set_stock


@owner_only
async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as db:
        products = await list_all_products(db)

    if not products:
        await update.message.reply_text("No products yet. Use /addproduct to add one.")
        return

    lines = ["*Your products:*\n"]
    for p in products:
        stock_note = f"{p.stock_qty} in stock" if p.stock_qty > 0 else "OUT OF STOCK"
        lines.append(f"#{p.id} — {p.name} ({p.category}) — {p.price} ETB — {stock_note}")

    lines.append("\nUpdate with:\n/setstock <id> <qty>\n/setprice <id> <price>")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@owner_only
async def update_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /setstock <product_id> <quantity>\nExample: /setstock 3 10")
        return

    try:
        product_id = int(args[0])
        qty = int(args[1])
    except ValueError:
        await update.message.reply_text("Both product_id and quantity must be whole numbers.")
        return

    async with AsyncSessionLocal() as db:
        product = await set_stock(db, product_id, qty)

    if not product:
        await update.message.reply_text(f"No product found with id #{product_id}.")
        return

    await update.message.reply_text(f"✅ {product.name} stock updated to {qty}.")


@owner_only
async def update_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /setprice <product_id> <price>\nExample: /setprice 3 14500")
        return

    try:
        product_id = int(args[0])
        price = float(args[1])
    except ValueError:
        await update.message.reply_text("product_id must be a whole number and price must be a number.")
        return

    async with AsyncSessionLocal() as db:
        product = await set_price(db, product_id, price)

    if not product:
        await update.message.reply_text(f"No product found with id #{product_id}.")
        return

    await update.message.reply_text(f"✅ {product.name} price updated to {price} ETB.")