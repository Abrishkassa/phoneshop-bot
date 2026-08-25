from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import settings


def owner_only(handler):
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id != settings.telegram_owner_id:
            if update.message:
                await update.message.reply_text("This command is only available to the shop owner.")
            return
        return await handler(update, context)

    return wrapper
