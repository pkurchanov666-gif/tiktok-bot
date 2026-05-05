import os
import asyncio
import logging
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import BOT_TOKEN
from replicate_api import generate_all_photos, regenerate_photo

logging.basicConfig(level=logging.INFO)

USER_DATA = {}

POV_PHRASES = [
    "POV: аура того самого парня который просто делает свое дело",
    "POV: твой парень воздуха и это буквально его вайб",
    "POV: дисциплина и характер",
    "POV: энергия уверенности",
    "POV: спокойствие и контроль"
]


def get_random_caption():
    return random.choice(POV_PHRASES)


def get_user_storage(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    return USER_DATA[user_id]


def build_ai_keyboard(count):
    regen_buttons = [
        InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}")
        for i in range(count)
    ]

    return InlineKeyboardMarkup([
        regen_buttons
    ])


async def send_gallery(context, user_id, paths, caption, keyboard):

    await context.bot.send_message(chat_id=user_id, text=caption)

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

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Готово",
        reply_markup=keyboard
    )


# ---------- ФОНОВАЯ ГЕНЕРАЦИЯ ----------

async def bg_generate(context, user_id):

    try:
        paths, specs = await generate_all_photos()

        if not paths:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка генерации"
            )
            return

        caption = get_random_caption()

        storage = get_user_storage(user_id)
        storage["paths"] = paths
        storage["specs"] = specs
        storage["caption"] = caption

        await send_gallery(
            context=context,
            user_id=user_id,
            paths=paths,
            caption=caption,
            keyboard=build_ai_keyboard(len(paths))
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка генерации: {e}"
        )


async def bg_regen(context, user_id, index):

    try:
        storage = get_user_storage(user_id)

        if "paths" not in storage:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Сначала сгенерируй фотосессию"
            )
            return

        new_path, new_spec = await regenerate_photo(index, storage["specs"])

        storage["paths"][index] = new_path
        storage["specs"][index] = new_spec

        caption = get_random_caption()
        storage["caption"] = caption

        await send_gallery(
            context=context,
            user_id=user_id,
            paths=storage["paths"],
            caption=caption,
            keyboard=build_ai_keyboard(len(storage["paths"]))
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка перегенерации: {e}"
        )


# ---------- ХЕНДЛЕРЫ ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]
    ])

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=keyboard
    )


async def ai_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    await query.edit_message_text(
        "⏳ Запуск генерации 3 фото...\nПодожди 1–3 минуты."
    )

    # ✅ ВАЖНО: используем application.create_task
    context.application.create_task(bg_generate(context, user_id))


async def regen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔄 Перегенерация фото {index+1}..."
    )

    context.application.create_task(bg_regen(context, user_id, index))


# ---------- MAIN ----------

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ai_photoshoot, pattern="^ai$"))
    app.add_handler(CallbackQueryHandler(regen_handler, pattern="^regen_"))

    print("Бот погнал!")

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://YOUR-APP-URL/{BOT_TOKEN}",
    )


if __name__ == "__main__":
    main()
