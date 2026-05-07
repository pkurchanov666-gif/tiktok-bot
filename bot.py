from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN
from replicate_api import generate_all_photos

USER_DATA = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]
    ])

    await update.message.reply_text(
        "Выберите режим:",
        reply_markup=keyboard
    )

async def send_gallery(context, user_id, paths):

    media = []
    opened = []

    try:
        for path in paths:
            f = open(path, "rb")
            opened.append(f)
            media.append(InputMediaPhoto(f))

        await context.bot.send_media_group(chat_id=user_id, media=media)

    finally:
        for f in opened:
            try:
                f.close()
            except:
                pass

async def background_generate(context, user_id):

    try:
        paths, specs = await generate_all_photos()

        print("DEBUG PATHS:", paths)

        if not paths:
            await context.bot.send_message(chat_id=user_id, text="❌ Нет фото")
            return

        await send_gallery(context, user_id, paths)

        await context.bot.send_message(chat_id=user_id, text="✅ Готово")

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")

async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    await query.edit_message_text("⏳ Генерация...")

    context.application.create_task(
        background_generate(context, user_id)
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ai_handler, pattern="^ai$"))

    print("Бот погнал!")
    app.run_polling()

if __name__ == "__main__":
    main()
