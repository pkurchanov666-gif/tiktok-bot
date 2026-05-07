import logging
import random
import json
import os
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
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from replicate_api import generate_all_photos, regenerate_photo
from buffer import send_to_buffer, get_profiles

logging.basicConfig(level=logging.INFO)

USER_DATA = {}
USER_DATA_FILE = "user_data.json"

POV_PHRASES = [
    "POV: аура того самого парня",
    "POV: дисциплина и характер",
    "POV: энергия уверенности",
    "POV: спокойствие и контроль"
]


# ---------------- STORAGE ----------------

def load_user_data():
    global USER_DATA
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                USER_DATA = json.load(f)
        except:
            USER_DATA = {}


def save_user_data():
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(USER_DATA, f)
    except:
        pass


def get_user_storage(user_id):
    user_id = str(user_id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    return USER_DATA[user_id]


def get_random_caption():
    return random.choice(POV_PHRASES)


# ---------------- KEYBOARDS ----------------

def build_ai_keyboard(user_id, count):
    storage = get_user_storage(user_id)
    buffer_connected = bool(
        storage.get("buffer_api_key") and storage.get("buffer_profile_id")
    )

    regen_buttons = [
        InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}")
        for i in range(count)
    ]

    rows = [regen_buttons]

    if buffer_connected:
        rows.append([
            InlineKeyboardButton("📤 Отправить в Buffer", callback_data="buffer_send")
        ])
        rows.append([
            InlineKeyboardButton("🔁 Перепривязать Buffer", callback_data="buffer_connect")
        ])
    else:
        rows.append([
            InlineKeyboardButton("🔗 Привязать Buffer", callback_data="buffer_connect")
        ])

    return InlineKeyboardMarkup(rows)


# ---------------- SEND MEDIA ----------------

async def send_media(context, user_id, paths):
    if not paths:
        return

    opened_files = []

    try:
        if len(paths) == 1:
            f = open(paths[0], "rb")
            opened_files.append(f)
            await context.bot.send_photo(chat_id=user_id, photo=f)
        else:
            media = []
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


# ---------------- AI GENERATION ----------------

async def background_ai_generate(context, user_id):
    try:
        paths, specs, urls = await generate_all_photos()

        if not paths:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка генерации"
            )
            return

        storage = get_user_storage(user_id)
        storage["paths"] = paths
        storage["specs"] = specs
        storage["urls"] = urls
        storage["caption"] = get_random_caption()
        save_user_data()

        await send_media(context, user_id, paths)

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ AI фотосессия готова",
            reply_markup=build_ai_keyboard(user_id, len(paths))
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

    await query.edit_message_text("⏳ Запуск AI генерации (2-3 минуты)...")

    context.application.create_task(
        background_ai_generate(context, user_id)
    )


# ---------------- REGEN ----------------

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

    if index >= len(storage["paths"]):
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Неверный номер фото"
        )
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔄 Перегенерация фото {index+1}..."
    )

    try:
        new_path, new_spec, new_url = await regenerate_photo(index, storage["specs"])

        storage["paths"][index] = new_path
        storage["specs"][index] = new_spec
        storage["urls"][index] = new_url
        save_user_data()

        await send_media(context, user_id, storage["paths"])

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Фото обновлены",
            reply_markup=build_ai_keyboard(user_id, len(storage["paths"]))
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка: {e}"
        )


# ---------------- BUFFER CONNECT ----------------

async def buffer_connect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    storage = get_user_storage(user_id)
    storage["awaiting_buffer_token"] = True
    save_user_data()

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            
