from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.access import owner_only
from app.core.database import AsyncSessionLocal
from app.core.storage import upload_product_photo
from app.services.product_service import (
    add_photo_url,
    get_product,
    list_all_products,
    set_brand_and_specs,
    set_price,
    set_stock,
)

AWAITING_PHOTO_FOR_PRODUCT = 1
AWAITING_SPECS_TEXT = 2


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


@owner_only
async def add_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /addphoto <product_id>\nExample: /addphoto 3")
        return ConversationHandler.END

    try:
        product_id = int(args[0])
    except ValueError:
        await update.message.reply_text("product_id must be a whole number.")
        return ConversationHandler.END

    async with AsyncSessionLocal() as db:
        product = await get_product(db, product_id)

    if not product:
        await update.message.reply_text(f"No product found with id #{product_id}.")
        return ConversationHandler.END

    context.user_data["photo_target_product_id"] = product_id
    await update.message.reply_text(f"Send a photo for *{product.name}*.", parse_mode="Markdown")
    return AWAITING_PHOTO_FOR_PRODUCT


async def add_photo_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = context.user_data.pop("photo_target_product_id", None)
    if not product_id or not update.message.photo:
        await update.message.reply_text("Please send a photo, or /cancel to stop.")
        return AWAITING_PHOTO_FOR_PRODUCT

    largest = update.message.photo[-1]
    file = await context.bot.get_file(largest.file_id)
    file_bytes = bytes(await file.download_as_bytearray())

    try:
        photo_url = await upload_product_photo(file_bytes)
    except Exception:
        await update.message.reply_text("⚠️ Upload failed. Please try again with /addphoto.")
        return ConversationHandler.END

    async with AsyncSessionLocal() as db:
        product = await add_photo_url(db, product_id, photo_url)

    await update.message.reply_text(f"✅ Photo added to {product.name if product else 'product'}.")
    return ConversationHandler.END


async def add_photo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("photo_target_product_id", None)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


@owner_only
async def edit_specs_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /editspecs <product_id>\nExample: /editspecs 3")
        return ConversationHandler.END

    try:
        product_id = int(args[0])
    except ValueError:
        await update.message.reply_text("product_id must be a whole number.")
        return ConversationHandler.END

    async with AsyncSessionLocal() as db:
        product = await get_product(db, product_id)

    if not product:
        await update.message.reply_text(f"No product found with id #{product_id}.")
        return ConversationHandler.END

    context.user_data["specs_target_product_id"] = product_id
    await update.message.reply_text(
        f"Editing *{product.name}*.\n\n"
        "Send brand and specs as lines like:\n"
        "brand: Samsung\nram: 8GB\nstorage: 128GB\nprocessor: Snapdragon 8 Gen 3\nbattery: 5000mAh\n\n"
        "Send only the lines you want to update.",
        parse_mode="Markdown",
    )
    return AWAITING_SPECS_TEXT


async def edit_specs_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = context.user_data.pop("specs_target_product_id", None)
    if not product_id:
        return ConversationHandler.END

    lines = update.message.text.strip().splitlines()
    brand = None
    specs = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip().lower(), value.strip()
        if not key or not value:
            continue
        if key == "brand":
            brand = value
        else:
            specs[key] = value

    async with AsyncSessionLocal() as db:
        product = await set_brand_and_specs(db, product_id, brand, specs)

    if not product:
        await update.message.reply_text("Product not found.")
        return ConversationHandler.END

    await update.message.reply_text(f"✅ Updated {product.name}.")
    return ConversationHandler.END


async def edit_specs_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("specs_target_product_id", None)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END