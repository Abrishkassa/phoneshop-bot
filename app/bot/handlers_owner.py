from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.access import owner_only
from app.core.database import AsyncSessionLocal
from app.core.storage import upload_product_photo
from app.services.product_service import create_product

NAME, CATEGORY, PRICE, COLORS, STOCK, PHOTO = range(6)

CATEGORY_KEYBOARD = ReplyKeyboardMarkup(
    [["phone", "earphone", "accessory"]], one_time_keyboard=True, resize_keyboard=True
)


@owner_only
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_product"] = {}
    await update.message.reply_text(
        "Let's add a new product. What's the product name?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_product"]["name"] = update.message.text.strip()
    await update.message.reply_text("Category?", reply_markup=CATEGORY_KEYBOARD)
    return CATEGORY


async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_product"]["category"] = update.message.text.strip().lower()
    await update.message.reply_text("Price (numbers only, e.g. 15000)?", reply_markup=ReplyKeyboardRemove())
    return PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        price = float(text)
    except ValueError:
        await update.message.reply_text("Please send a valid number for price, e.g. 15000")
        return PRICE
    context.user_data["new_product"]["price"] = price
    await update.message.reply_text("What colors are available? (comma-separated, e.g. Black, Blue, Gold)")
    return COLORS


async def add_product_colors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    colors = [c.strip() for c in update.message.text.split(",") if c.strip()]
    context.user_data["new_product"]["colors"] = colors
    await update.message.reply_text("How many units in stock?")
    return STOCK


async def add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        stock_qty = int(text)
    except ValueError:
        await update.message.reply_text("Please send a whole number, e.g. 5")
        return STOCK

    context.user_data["new_product"]["stock_qty"] = stock_qty
    await update.message.reply_text(
        "Send a photo of the product now, or type 'skip' to add it later with /addphoto."
    )
    return PHOTO


async def add_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.pop("new_product")
    photo_url = None

    if update.message.photo:
        largest = update.message.photo[-1]
        file = await context.bot.get_file(largest.file_id)
        file_bytes = bytes(await file.download_as_bytearray())
        try:
            photo_url = await upload_product_photo(file_bytes)
        except Exception:
            await update.message.reply_text(
                "⚠️ Photo upload failed, but the product will still be added without a photo. "
                "You can try again later with /addphoto."
            )

    if photo_url:
        data["photo_urls"] = [photo_url]

    async with AsyncSessionLocal() as db:
        product = await create_product(db, **data)

    photo_note = " with photo" if photo_url else " (no photo — use /addphoto to add one later)"
    await update.message.reply_text(
        f"✅ Added *{product.name}* — {product.price} ETB, {data['stock_qty']} in stock{photo_note}.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def add_product_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END