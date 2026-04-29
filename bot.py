from telegram.error import BadRequest
import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from config import BOT_TOKEN
from templates import get_next_template
from slides import get_random_photos, create_slides
from db import save_user_buffer, get_user_buffer
from buffer_api import get_profiles, send_to_buffer

logging.basicConfig(level=logging.WARNING)

WAITING_BUFFER_KEY = 1
WAITING_PROFILE = 2


async def send_slides(context, user_id, paths, text):
    media = []
    for i, path in enumerate(paths):
        with open(path, "rb") as f:
            photo_bytes = f.read()
        if i == 0:
            media.append(InputMediaPhoto(media=photo_bytes, caption=f"Текст: {text}"))
        else:
            media.append(InputMediaPhoto(media=photo_bytes))

    await context.bot.send_media_group(chat_id=user_id, media=media)

    buffer_user = get_user_buffer(user_id)

    keyboard = [
        [InlineKeyboardButton("🔄 Другой текст", callback_data="change_text")],
        [InlineKeyboardButton("🎬 Новые фото + текст", callback_data="generate")],
    ]

    if buffer_user:
        keyboard.insert(1, [InlineKeyboardButton("📤 Отправить в Buffer", callback_data="send_buffer")])
    else:
        keyboard.append([InlineKeyboardButton("🔗 Привязать Buffer", callback_data="setup_buffer")])

    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ Готово!\n\nТекст: {text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    buffer_user = get_user_buffer(user_id)

    if buffer_user:
        buffer_status = "✅ Buffer подключен"
        buffer_btn = [InlineKeyboardButton("🔁 Перепривязать Buffer", callback_data="setup_buffer")]
    else:
        buffer_status = "❌ Buffer не подключен"
        buffer_btn = [InlineKeyboardButton("🔗 Привязать Buffer", callback_data="setup_buffer")]

    keyboard = [
        [InlineKeyboardButton("🎬 Сгенерировать слайды", callback_data="generate")],
        buffer_btn,
    ]

    await update.message.reply_text(
        f"Привет!\n\n"
        f"Статус: {buffer_status}\n\n"
        f"Что умею:\n"
        f"- Генерирую 5 слайдов\n"
        f"- На первый слайд добавляю текст\n"
        f"- Отправляю в Buffer\n\n"
        f"Кнопка 'Другой текст' меняет только текст\n"
        f"Кнопка 'Новые фото + текст' меняет всё",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id

    try:
        text = get_next_template()
        context.user_data["current_text"] = text

        await query.edit_message_text(f"📸 Выбираю новые фото и накладываю текст...\n\nТекст:\n{text}")

        photos = get_random_photos()
        context.user_data["selected_photos"] = photos

        paths = await asyncio.to_thread(create_slides, text, user_id, photos)
        context.user_data["last_slides"] = paths

        await send_slides(context, user_id, paths, text)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


async def change_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id

    try:
        photos = context.user_data.get("selected_photos")

        if not photos:
            photos = get_random_photos()
            context.user_data["selected_photos"] = photos

        text = get_next_template()
        context.user_data["current_text"] = text

        await query.edit_message_text(f"🔄 Меняю текст...\nФото остаются те же\n\nНовый текст:\n{text}")

        paths = await asyncio.to_thread(create_slides, text, user_id, photos)
        context.user_data["last_slides"] = paths

        await send_slides(context, user_id, paths, text)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


async def setup_buffer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass

    await query.edit_message_text(
        "🔗 Привязка Buffer\n\n"
        "Как получить API Key:\n"
        "1. Зайди на publish.buffer.com/settings/api\n"
        "2. Нажми + New API Key\n"
        "3. Назови Telegram Bot\n"
        "4. Выбери срок 1 year\n"
        "5. Скопируй ключ\n\n"
        "Отправь мне API Key:"
    )
    return WAITING_BUFFER_KEY


async def receive_buffer_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    context.user_data["buffer_api_key"] = api_key

    try:
        await update.message.reply_text("🔍 Проверяю ключ...")
        profiles = await get_profiles(api_key)

        if not profiles:
            await update.message.reply_text("❌ Профили не найдены. Проверь что TikTok подключён к Buffer.")
            return ConversationHandler.END

        keyboard = []
        for profile in profiles:
            profile_id = profile.get("id")
            service = profile.get("service", "?")
            username = profile.get("formatted_username") or profile.get("username") or profile_id
            keyboard.append([InlineKeyboardButton(f"{service} — {username}", callback_data=f"profile_{profile_id}")])

        await update.message.reply_text(
            "✅ Ключ принят!\n\nВыбери профиль:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_PROFILE

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        return ConversationHandler.END


async def receive_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass

    user_id = query.from_user.id
    profile_id = query.data.replace("profile_", "")
    api_key = context.user_data.get("buffer_api_key")

    save_user_buffer(user_id, api_key, profile_id)

    await query.edit_message_text(
        "✅ Buffer подключён!\n\n"
        "Теперь нажми /start и генерируй слайды 🎬"
    )
    return ConversationHandler.END


import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from telegram.error import BadRequest

from config import BOT_TOKEN
from templates import get_next_template
from slides import get_random_photos, create_slides
from db import save_user_buffer, get_user_buffer, delete_user_buffer
from buffer_api import get_profiles, send_to_buffer
from imgbb_api import upload_images_to_imgbb

logging.basicConfig(level=logging.WARNING)

WAITING_BUFFER_KEY = 1
WAITING_PROFILE = 2

async def send_slides(context, user_id, paths, text):
    media = []
    for i, path in enumerate(paths):
        with open(path, "rb") as f:
            photo_bytes = f.read()
        if i == 0:
            media.append(InputMediaPhoto(media=photo_bytes, caption=f"Текст: {text}"))
        else:
            media.append(InputMediaPhoto(media=photo_bytes))

    await context.bot.send_media_group(chat_id=user_id, media=media)
    buffer_user = get_user_buffer(user_id)
    keyboard = [
        [InlineKeyboardButton("🔄 Другой текст", callback_data="change_text")],
        [InlineKeyboardButton("🎬 Новые фото + текст", callback_data="generate")],
    ]
    if buffer_user:
        keyboard.insert(1, [InlineKeyboardButton("📤 Отправить в Buffer", callback_data="send_buffer")])
    else:
        keyboard.append([InlineKeyboardButton("🔗 Привязать Buffer", callback_data="setup_buffer")])

    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ Готово!\n\nТекст: {text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    buffer_user = get_user_buffer(user_id)
    keyboard = [[InlineKeyboardButton("🎬 Сгенерировать слайды", callback_data="generate")]]
    if buffer_user:
        keyboard.append([InlineKeyboardButton("✅ Buffer подключен", callback_data="buffer_status")])
        keyboard.append([InlineKeyboardButton("🔁 Перепривязать Buffer", callback_data="setup_buffer")])
    else:
        keyboard.append([InlineKeyboardButton("🔗 Привязать Buffer", callback_data="setup_buffer")])

    await update.message.reply_text("Привет! Нажми кнопку для работы:", reply_markup=InlineKeyboardMarkup(keyboard))

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except BadRequest: pass
    user_id = query.from_user.id
    try:
        text = get_next_template()
        context.user_data["current_text"] = text
        await query.edit_message_text(f"📸 Собираю слайды...\nТекст: {text}")
        photos = get_random_photos()
        context.user_data["selected_photos"] = photos
        paths = await asyncio.to_thread(create_slides, text, user_id, photos)
        context.user_data["last_slides"] = paths
        await send_slides(context, user_id, paths, text)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")

async def change_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except BadRequest: pass
    user_id = query.from_user.id
    try:
        photos = context.user_data.get("selected_photos") or get_random_photos()
        context.user_data["selected_photos"] = photos
        text = get_next_template()
        context.user_data["current_text"] = text
        await query.edit_message_text(f"🔄 Меняю текст...\n\nНовый текст: {text}")
        paths = await asyncio.to_thread(create_slides, text, user_id, photos)
        context.user_data["last_slides"] = paths
        await send_slides(context, user_id, paths, text)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")

async def send_buffer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except BadRequest: pass
    user_id = query.from_user.id
    buffer_user = get_user_buffer(user_id)
    paths = context.user_data.get("last_slides")
    text = context.user_data.get("current_text")

    if not buffer_user or not paths:
        await context.bot.send_message(chat_id=user_id, text="❌ Ошибка: не привязан Buffer или нет слайдов")
        return

    try:
        await query.edit_message_text("☁️ Загружаю в облако (ImgBB)...")
        image_urls = await upload_images_to_imgbb(paths)
        await query.edit_message_text("📤 Отправляю в Buffer...")
        await send_to_buffer(buffer_user["buffer_api_key"], buffer_user["buffer_profile_id"], image_urls, text)
        await context.bot.send_message(chat_id=user_id, text="✅ Отправлено в Buffer!\n\nОткрой Buffer на телефоне и заверши публикацию.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Сделать следующий пост", callback_data="generate")]]))
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка Buffer: {e}")

async def setup_buffer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except BadRequest: pass
    await query.edit_message_text("🔗 Отправь мне Buffer API Key (с сайта Buffer):")
    return WAITING_BUFFER_KEY

async def receive_buffer_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    context.user_data["buffer_api_key"] = api_key
    try:
        profiles = await get_profiles(api_key)
        keyboard = [[InlineKeyboardButton(f"{p['service']} - {p['formatted_username']}", callback_data=f"profile_{p['id']}")] for p in profiles]
        await update.message.reply_text("✅ Выбери профиль:", reply_markup=InlineKeyboardMarkup(keyboard))
        return WAITING_PROFILE
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
        return ConversationHandler.END

async def receive_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except BadRequest: pass
    profile_id = query.data.replace("profile_", "")
    save_user_buffer(query.from_user.id, context.user_data["buffer_api_key"], profile_id)
    await query.edit_message_text("✅ Buffer привязан! Жми /start")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    buffer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(setup_buffer_start, pattern="^setup_buffer$")],
        states={
            WAITING_BUFFER_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buffer_key)],
            WAITING_PROFILE: [CallbackQueryHandler(receive_profile, pattern="^profile_")],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(buffer_conv)
    app.add_handler(CallbackQueryHandler(generate, pattern="^generate$"))
    app.add_handler(CallbackQueryHandler(change_text, pattern="^change_text$"))
    app.add_handler(CallbackQueryHandler(send_buffer_handler, pattern="^send_buffer$"))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()