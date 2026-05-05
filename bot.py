# bot.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, FSInputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from replicate_api import generate_all_photos, regenerate_photo
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

USER_DATA = {}


def get_storage(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    return USER_DATA[user_id]


def build_keyboard(count):
    buttons = [InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}") for i in range(count)]
    return InlineKeyboardMarkup([buttons])


async def send_gallery(context, user_id, paths):

    media = []

    for path in paths:
        media.append(InputMediaPhoto(FSInputFile(path)))

    await context.bot.send_media_group(chat_id=user_id, media=media)


async def background_generate(context, user_id):

    try:
        paths, specs = await generate_all_photos()

        if not paths:
            await context.bot.send_message(chat_id=user_id, text="❌ Ошибка генерации")
            return

        storage = get_storage(user_id)
        storage["paths"] = paths
        storage["specs"] = specs

        await send_gallery(context, user_id, paths)

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Готово",
            reply_markup=build_keyboard(len(paths))
        )

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


async def regen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))

    context.application.create_task(background_regen(context, user_id, index))


async def background_regen(context, user_id, index):

    storage = get_storage(user_id)

    new_path, new_spec = await regenerate_photo(index, storage["specs"])

    storage["paths"][index] = new_path
    storage["specs"][index] = new_spec

    await send_gallery(context, user_id, storage["paths"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="generate")]
    ])

    await update.message.reply_text("Выберите действие:", reply_markup=keyboard)


async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    await query.edit_message_text("⏳ Генерация...")

    context.application.create_task(background_generate(context, user_id))


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(generate_handler, pattern="^generate$"))
    app.add_handler(CallbackQueryHandler(regen_handler, pattern="^regen_"))

    print("Бот погнал!")

    app.run_polling()


if __name__ == "__main__":
    main()
