from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.inquiry_service import mark_inquiry_sold


async def mark_sold_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != settings.telegram_owner_id:
        await query.answer("Only the shop owner can do this.", show_alert=True)
        return

    inquiry_id = int(query.data.split(":", 1)[1])

    async with AsyncSessionLocal() as db:
        inquiry = await mark_inquiry_sold(db, inquiry_id)

    if not inquiry:
        await query.edit_message_text("This inquiry could not be found.")
        return

    original_text = query.message.text or ""
    await query.edit_message_text(f"{original_text}\n\n✅ Marked as sold — stock updated.")