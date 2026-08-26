from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.bot.handlers_customer import browse_category, start
from app.bot.handlers_delivery import (
    AWAITING_COLOR,
    product_detail,
    request_delivery_cancel,
    request_delivery_color,
    request_delivery_start,
)
from app.bot.handlers_owner import (
    CATEGORY,
    COLORS,
    NAME,
    PRICE,
    STOCK,
    add_product_cancel,
    add_product_category,
    add_product_colors,
    add_product_name,
    add_product_price,
    add_product_stock,
    add_product_start,
)
from app.bot.handlers_owner_manage import my_products, update_price, update_stock
from app.core.config import settings


def build_application() -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(browse_category, pattern=r"^category:"))
    application.add_handler(CallbackQueryHandler(product_detail, pattern=r"^product:"))
     application.add_handler(CommandHandler("myproducts", my_products))
    application.add_handler(CommandHandler("setstock", update_stock))
    application.add_handler(CommandHandler("setprice", update_price))
    add_product_conv = ConversationHandler(
        entry_points=[CommandHandler("addproduct", add_product_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            COLORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_colors)],
            STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_stock)],
        },
        fallbacks=[CommandHandler("cancel", add_product_cancel)],
    )
    application.add_handler(add_product_conv)

    delivery_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_delivery_start, pattern=r"^deliver:")],
        states={
            AWAITING_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_delivery_color)],
        },
        fallbacks=[CommandHandler("cancel", request_delivery_cancel)],
    )
    application.add_handler(delivery_conv)

    return application
