from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from app.bot.access import owner_only
from app.core.database import AsyncSessionLocal
from app.core.storage import upload_product_photo
from app.services.product_service import create_product

(
    NAME,
    CATEGORY,
    BRAND,
    PRICE,
    COLORS,
    STOCK,
    SPEC_RAM,
    SPEC_STORAGE,
    SPEC_PROCESSOR,
    SPEC_BATTERY,
    SPEC_EARPHONE_BATTERY,
    SPEC_EARPHONE_TYPE,
    PHOTO,
    REVIEW,
) = range(14)

CATEGORY_KEYBOARD = ReplyKeyboardMarkup(
    [["phone", "laptop"], ["earphone", "accessory"], ["⬅️ back"]], one_time_keyboard=True, resize_keyboard=True
)
EARPHONE_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    [["Wireless", "Wired"], ["⬅️ back"]], one_time_keyboard=True, resize_keyboard=True
)
BACK_HINT = "\n\n(type 'back' to go to the previous step, or /cancel to stop)"

SPEC_CATEGORIES = {"phone", "laptop"}

# Maps each state to the state you land on when you type "back" from it.
PREVIOUS_STATE = {
    CATEGORY: NAME,
    BRAND: CATEGORY,
    PRICE: BRAND,
    COLORS: PRICE,
    STOCK: COLORS,
    SPEC_RAM: STOCK,
    SPEC_STORAGE: SPEC_RAM,
    SPEC_PROCESSOR: SPEC_STORAGE,
    SPEC_BATTERY: SPEC_PROCESSOR,
    SPEC_EARPHONE_BATTERY: STOCK,
    SPEC_EARPHONE_TYPE: SPEC_EARPHONE_BATTERY,
}


def _is_back(text: str) -> bool:
    return text.strip().lower() in ("back", "⬅️ back")


async def _prompt_for_state(update: Update, state: int, context: ContextTypes.DEFAULT_TYPE):
    """Re-sends the question for a given state — used both on first arrival
    and when the owner types 'back' to return to a previous step."""
    data = context.user_data.get("new_product", {})

    if state == NAME:
        await update.message.reply_text("What's the product name?", reply_markup=ReplyKeyboardRemove())
    elif state == CATEGORY:
        await update.message.reply_text("Category?", reply_markup=CATEGORY_KEYBOARD)
    elif state == BRAND:
        await update.message.reply_text(
            "Brand? (e.g. Samsung, Apple, JBL)" + BACK_HINT, reply_markup=ReplyKeyboardRemove()
        )
    elif state == PRICE:
        await update.message.reply_text("Price (numbers only, e.g. 15000)?" + BACK_HINT)
    elif state == COLORS:
        await update.message.reply_text(
            "What colors are available? (comma-separated, e.g. Black, Blue, Gold)" + BACK_HINT
        )
    elif state == STOCK:
        await update.message.reply_text("How many units in stock?" + BACK_HINT)
    elif state == SPEC_RAM:
        await update.message.reply_text("RAM? (e.g. 8GB)" + BACK_HINT)
    elif state == SPEC_STORAGE:
        await update.message.reply_text("Storage? (e.g. 128GB)" + BACK_HINT)
    elif state == SPEC_PROCESSOR:
        await update.message.reply_text("Processor? (e.g. Snapdragon 8 Gen 3)" + BACK_HINT)
    elif state == SPEC_BATTERY:
        await update.message.reply_text("Battery? (e.g. 5000mAh)" + BACK_HINT)
    elif state == SPEC_EARPHONE_BATTERY:
        await update.message.reply_text("Battery life? (e.g. 20 hours)" + BACK_HINT)
    elif state == SPEC_EARPHONE_TYPE:
        await update.message.reply_text("Wireless or Wired?", reply_markup=EARPHONE_TYPE_KEYBOARD)
    elif state == PHOTO:
        await update.message.reply_text(
            "Send a photo of the product now, or type 'skip' to add it later with /addphoto."
            + BACK_HINT
        )

    _ = data  # data currently unused in prompts but kept for future pre-filling


async def _go_back(update: Update, context: ContextTypes.DEFAULT_TYPE, current_state: int) -> int:
    previous = PREVIOUS_STATE.get(current_state, NAME)
    await _prompt_for_state(update, previous, context)
    return previous


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
    await _prompt_for_state(update, CATEGORY, context)
    return CATEGORY


async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, CATEGORY)
    context.user_data["new_product"]["category"] = update.message.text.strip().lower()
    await _prompt_for_state(update, BRAND, context)
    return BRAND


async def add_product_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, BRAND)
    context.user_data["new_product"]["brand"] = update.message.text.strip()
    await _prompt_for_state(update, PRICE, context)
    return PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, PRICE)
    text = update.message.text.strip()
    try:
        price = float(text)
    except ValueError:
        await update.message.reply_text("Please send a valid number for price, e.g. 15000" + BACK_HINT)
        return PRICE
    context.user_data["new_product"]["price"] = price
    await _prompt_for_state(update, COLORS, context)
    return COLORS


async def add_product_colors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, COLORS)
    colors = [c.strip() for c in update.message.text.split(",") if c.strip()]
    context.user_data["new_product"]["colors"] = colors
    await _prompt_for_state(update, STOCK, context)
    return STOCK


async def add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, STOCK)
    text = update.message.text.strip()
    try:
        stock_qty = int(text)
    except ValueError:
        await update.message.reply_text("Please send a whole number, e.g. 5" + BACK_HINT)
        return STOCK

    context.user_data["new_product"]["stock_qty"] = stock_qty
    context.user_data["new_product"].setdefault("specs", {})

    category = context.user_data["new_product"]["category"]
    if category in SPEC_CATEGORIES:
        await _prompt_for_state(update, SPEC_RAM, context)
        return SPEC_RAM
    elif category == "earphone":
        await _prompt_for_state(update, SPEC_EARPHONE_BATTERY, context)
        return SPEC_EARPHONE_BATTERY
    else:
        await _prompt_for_state(update, PHOTO, context)
        return PHOTO


async def add_product_spec_ram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, SPEC_RAM)
    context.user_data["new_product"]["specs"]["ram"] = update.message.text.strip()
    await _prompt_for_state(update, SPEC_STORAGE, context)
    return SPEC_STORAGE


async def add_product_spec_storage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, SPEC_STORAGE)
    context.user_data["new_product"]["specs"]["storage"] = update.message.text.strip()
    await _prompt_for_state(update, SPEC_PROCESSOR, context)
    return SPEC_PROCESSOR


async def add_product_spec_processor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, SPEC_PROCESSOR)
    context.user_data["new_product"]["specs"]["processor"] = update.message.text.strip()
    await _prompt_for_state(update, SPEC_BATTERY, context)
    return SPEC_BATTERY


async def add_product_spec_battery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, SPEC_BATTERY)
    context.user_data["new_product"]["specs"]["battery"] = update.message.text.strip()
    await _prompt_for_state(update, PHOTO, context)
    return PHOTO


async def add_product_spec_earphone_battery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, SPEC_EARPHONE_BATTERY)
    context.user_data["new_product"]["specs"]["battery_life"] = update.message.text.strip()
    await _prompt_for_state(update, SPEC_EARPHONE_TYPE, context)
    return SPEC_EARPHONE_TYPE


async def add_product_spec_earphone_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if _is_back(update.message.text):
        return await _go_back(update, context, SPEC_EARPHONE_TYPE)
    context.user_data["new_product"]["specs"]["type"] = update.message.text.strip()
    await _prompt_for_state(update, PHOTO, context)
    return PHOTO


def _review_text(data: dict) -> str:
    lines = [
        "*Review your product:*\n",
        f"Name: {data.get('name')}",
        f"Category: {data.get('category')}",
        f"Brand: {data.get('brand')}",
        f"Price: {data.get('price')} ETB",
        f"Colors: {', '.join(data.get('colors', []))}",
        f"Stock: {data.get('stock_qty')}",
    ]
    for key, value in (data.get("specs") or {}).items():
        lines.append(f"{key.replace('_', ' ').title()}: {value}")
    if data.get("photo_urls"):
        lines.append("Photo: ✅ attached")
    else:
        lines.append("Photo: none yet")
    return "\n".join(lines)


async def add_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and _is_back(update.message.text):
        return await _go_back(update, context, PHOTO)

    data = context.user_data["new_product"]

    if update.message.photo:
        largest = update.message.photo[-1]
        file = await context.bot.get_file(largest.file_id)
        file_bytes = bytes(await file.download_as_bytearray())
        try:
            photo_url = await upload_product_photo(file_bytes)
            data["photo_urls"] = [photo_url]
        except Exception:
            await update.message.reply_text(
                "⚠️ Photo upload failed — you can add one later with /addphoto. Continuing..."
            )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Confirm & Add", callback_data="review_confirm")],
            [InlineKeyboardButton("⬅️ Back", callback_data="review_back")],
            [InlineKeyboardButton("❌ Cancel", callback_data="review_cancel")],
        ]
    )
    await update.message.reply_text(_review_text(data), parse_mode="Markdown", reply_markup=keyboard)
    return REVIEW


async def review_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = context.user_data.pop("new_product")
    async with AsyncSessionLocal() as db:
        product = await create_product(db, **data)

    await query.edit_message_text(
        f"✅ Added *{product.name}* ({product.brand}) — {product.price} ETB, "
        f"{data['stock_qty']} in stock.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def review_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Okay, let's redo the photo step.")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Send a photo of the product now, or type 'skip' to add it later with /addphoto." + BACK_HINT,
    )
    return PHOTO


async def review_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("new_product", None)
    await query.edit_message_text("Cancelled.")
    return ConversationHandler.END


async def add_product_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END