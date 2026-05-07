import logging
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import BOT_TOKEN
from slides import get_random_photos, create_slides
from replicate_api import generate_all_photos, regenerate_photo

logging.basicConfig(level=logging.INFO)

USER_DATA = {}

POV_PHRASES = [
    "POV: аура того самого парня",
    "POV: дисциплина и характер",
    "POV: энергия уверенности",
    "POV: спокойствие и контроль"
]


# ---------------- UTILS ----------------

def get_user_storage(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    return USER_DATA[user_id]


def get_random_caption():
    return random.choice(POV_PHRASES)


def build_ai_keyboard(count):
    buttons = [
        InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}")
        for i in range(count)
    ]
    return InlineKeyboardMarkup([buttons])


# ---------------- SEND MEDIA ----------------

async def send_media(context, user_id, paths):
    media = []
    opened_files = []

    try:
        for path in paths:
            f = open(path, "rb")
            opened_files.append(f)
            media.append(InputMediaPhoto(f))

        await context.bot.send_media_group(chat_id=user_id, media=media)

    finally:
        for f in opened_files:
            try:
                f.close()
            except:
                pass


# ---------------- SLIDES MODE ----------------

async def generate_slides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    caption = get_random_caption()

    await query.edit_message_text("📸 Генерация слайдов...")

    photos = get_random_photos()
    paths = create_slides(caption, user_id, photos)

    await send_media(context, user_id, paths)

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Слайды готовы"
    )


# ---------------- AI MODE ----------------

async def background_ai_generate(context, user_id):
    try:
        paths, specs = await generate_all_photos()

        if not paths:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка генерации"
            )
            return

        storage = get_user_storage(user_id)
        storage["paths"] = paths
        storage["specs"] = specs

        await send_media(context, user_id, paths)

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ AI фотосессия готова",
            reply_markup=build_ai_keyboard(len(paths))
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка: {e}"
        )


async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    await query.edit_message_text("⏳ Запуск AI генерации...")

    context.application.create_task(
        background_ai_generate(context, user_id)
    )


async def regen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))

    storage = get_user_storage(user_id)

    if "paths" not in storage:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Сначала сгенерируй AI фотосессию"
        )
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔄 Перегенерация фото {index+1}..."
    )

    new_path, new_spec = await regenerate_photo(index, storage["specs"])

    storage["paths"][index] = new_path
    storage["specs"][index] = new_spec

    await send_media(context, user_id, storage["paths"])


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Слайды", callback_data="slides")],
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]
    ])

    await update.message.reply_text(
        "Выберите режим:",
        reply_markup=keyboard
    )


# ---------------- MAIN ----------------

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(generate_slides, pattern="^slides$"))
    app.add_handler(CallbackQueryHandler(ai_handler, pattern="^ai$"))
    app.add_handler(CallbackQueryHandler(regen_handler, pattern="^regen_"))

    print("Бот погнал!")

    app.run_polling()


if __name__ == "__main__":
    main()
