import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

from config import BOT_TOKEN
from replicate_api import generate_all_photos

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai_photoshoot")]
    ]
    await update.message.reply_text(
        "Бот работает ✅",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ai_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Генерирую фото...")

    try:
        paths = await generate_all_photos()
        media = [InputMediaPhoto(open(p, "rb")) for p in paths]
        await context.bot.send_media_group(chat_id=query.from_user.id, media=media)
    except Exception as e:
        await context.bot.send_message(chat_id=query.from_user.id, text=f"Ошибка AI: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ai_photoshoot, pattern="^ai_photoshoot$"))

    print("Бот погнал!")

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://tiktok-bot-production-4530.up.railway.app/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()
