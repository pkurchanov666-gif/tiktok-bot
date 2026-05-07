import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN
from replicate_api import generate_all_photos

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]
    ])

    await update.message.reply_text(
        "Бот работает. Нажми кнопку.",
        reply_markup=keyboard
    )


async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    await context.bot.send_message(chat_id=user_id, text="🚀 Запуск генерации")

    try:
        paths, specs = await generate_all_photos()

        await context.bot.send_message(chat_id=user_id, text=f"✅ Получено {len(paths)} файлов")

        if not paths:
            await context.bot.send_message(chat_id=user_id, text="❌ Пустой список путей")
            return

        media = []
        opened_files = []

        for path in paths:
            f = open(path, "rb")
            opened_files.append(f)
            media.append(InputMediaPhoto(f))

        await context.bot.send_media_group(chat_id=user_id, media=media)

        for f in opened_files:
            f.close()

        await context.bot.send_message(chat_id=user_id, text="✅ Фото отправлены")

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ai_handler, pattern="^ai$"))

    print("Бот запущен")

    app.run_polling()


if __name__ == "__main__":
    main()
