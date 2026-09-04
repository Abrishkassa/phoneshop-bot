from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.handlers_customer import start
from app.bot.handlers_owner import (
    BRAND,
    CATEGORY,
    COLORS,
    NAME,
    PHOTO,
    PRICE,
    REVIEW,
    SPEC_BATTERY,
    SPEC_EARPHONE_BATTERY,
    SPEC_EARPHONE_TYPE,
    SPEC_PROCESSOR,
    SPEC_RAM,
    SPEC_STORAGE,
    STOCK,
    add_product_brand,
    add_product_cancel,
    add_product_category,
    add_product_colors,
    add_product_name,
    add_product_photo,
    add_product_price,
    add_product_spec_battery,
    add_product_spec_earphone_battery,
    add_product_spec_earphone_type,
    add_product_spec_processor,
    add_product_spec_ram,
    add_product_spec_storage,
    add_product_start,
    add_product_stock,
    review_back,
    review_cancel,
    review_confirm,
)
from app.bot.handlers_owner_manage import (
    AWAITING_PHOTO_FOR_PRODUCT,
    AWAITING_SPECS_TEXT,
    add_photo_cancel,
    add_photo_receive,
    add_photo_start,
    edit_specs_cancel,
    edit_specs_receive,
    edit_specs_start,
    my_products,
    update_price,
    update_stock,
)
from app.core.config import settings

BOT_COMMANDS = [
    BotCommand("start", "Open the shop (customers)"),
    BotCommand("addproduct", "Add a new product (owner)"),
    BotCommand("myproducts", "List all your products (owner)"),
    BotCommand("setstock", "Update stock: /setstock <id> <qty>"),
    BotCommand("setprice", "Update price: /setprice <id> <price>"),
    BotCommand("addphoto", "Add a photo: /addphoto <id>"),
    BotCommand("editspecs", "Edit brand/specs: /editspecs <id>"),
    BotCommand("cancel", "Cancel whatever you're doing"),
]


async def _post_init(application: Application) -> None:
    """Sets the persistent "/" command menu shown in Telegram's UI."""
    await application.bot.set_my_commands(BOT_COMMANDS)


def build_application() -> Application:
    """Builds the bot's command set.

    Product browsing, filtering, comparing, and delivery requests live in the
    Telegram Mini App (static/index.html + /api/* endpoints) — see
    app/bot/handlers_customer.py and app/routers/miniapp.py. Only owner
    management stays as bot commands.
    """
    application = (
        Application.builder().token(settings.telegram_bot_token).post_init(_post_init).build()
    )

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("myproducts", my_products))
    application.add_handler(CommandHandler("setstock", update_stock))
    application.add_handler(CommandHandler("setprice", update_price))

    add_product_conv = ConversationHandler(
        entry_points=[CommandHandler("addproduct", add_product_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)],
            BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_brand)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            COLORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_colors)],
            STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_stock)],
            SPEC_RAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_spec_ram)],
            SPEC_STORAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_spec_storage)],
            SPEC_PROCESSOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_spec_processor)],
            SPEC_BATTERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_spec_battery)],
            SPEC_EARPHONE_BATTERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_spec_earphone_battery)
            ],
            SPEC_EARPHONE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_spec_earphone_type)
            ],
            PHOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), add_product_photo)],
            REVIEW: [
                CallbackQueryHandler(review_confirm, pattern="^review_confirm$"),
                CallbackQueryHandler(review_back, pattern="^review_back$"),
                CallbackQueryHandler(review_cancel, pattern="^review_cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", add_product_cancel)],
    )
    application.add_handler(add_product_conv)

    add_photo_conv = ConversationHandler(
        entry_points=[CommandHandler("addphoto", add_photo_start)],
        states={
            AWAITING_PHOTO_FOR_PRODUCT: [MessageHandler(filters.PHOTO, add_photo_receive)],
        },
        fallbacks=[CommandHandler("cancel", add_photo_cancel)],
    )
    application.add_handler(add_photo_conv)

    edit_specs_conv = ConversationHandler(
        entry_points=[CommandHandler("editspecs", edit_specs_start)],
        states={
            AWAITING_SPECS_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_specs_receive)],
        },
        fallbacks=[CommandHandler("cancel", edit_specs_cancel)],
    )
    application.add_handler(edit_specs_conv)

    return application