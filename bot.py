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
from db import save_user_buffer, get_user_buffer
from buffer_api import get_profiles, send_to_buffer
from imgbb_api import upload_images_to_imgbb
from replicate_api import generate_all_photos, regenerate_photo

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
    keyboard = [
        [InlineKeyboardButton("🎬 Сгенерировать слайды", callback_data="generate")],
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai_photoshoot")],
    ]
    if buffer_user:
        keyboard.append([InlineKeyboardButton("✅ Buffer подключен", callback_data="buffer_status")])
        keyboard.append([InlineKeyboardButton("🔁 Перепривязать Buffer", callback_data="setup_buffer")])
    else:
        keyboard.append([InlineKeyboardButton("🔗 Привязать Buffer", callback_data="setup_buffer")])

    await update.message.reply_text(
        "Привет! Выбери действие:",
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
    try:
        await query.answer()
    except BadRequest:
        pass
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


async def ai_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id
    try:
        await query.edit_message_text(
            "📸 Генерирую AI фотосессию...\n\n"
            "Это займёт 1-2 минуты ⏳"
        )
        paths = await generate_all_photos()
        context.user_data["ai_photos"] = paths

        media = []
        for i, path in enumerate(paths):
            with open(path, "rb") as f:
                photo_bytes = f.read()
            if i == 0:
                media.append(InputMediaPhoto(media=photo_bytes, caption="📸 AI Фотосессия готова!"))
            else:
                media.append(InputMediaPhoto(media=photo_bytes))

        await context.bot.send_media_group(chat_id=user_id, media=media)

        keyboard = [
            [
                InlineKeyboardButton("🔄 1", callback_data="regen_0"),
                InlineKeyboardButton("🔄 2", callback_data="regen_1"),
                InlineKeyboardButton("🔄 3", callback_data="regen_2"),
                InlineKeyboardButton("🔄 4", callback_data="regen_3"),
                InlineKeyboardButton("🔄 5", callback_data="regen_4"),
            ],
            [InlineKeyboardButton("📤 Отправить в Buffer", callback_data="send_ai_buffer")],
            [InlineKeyboardButton("➡️ Сделать следующий пост", callback_data="generate")],
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text="Нажми 🔄 чтобы перегенерировать любое фото",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(f"AI фото ошибка: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


async def regen_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))
    try:
        await query.edit_message_text(f"🔄 Перегенерирую фото #{index + 1}...")
        new_path = await regenerate_photo(index)
        paths = context.user_data.get("ai_photos", [])
        if len(paths) > index:
            paths[index] = new_path
            context.user_data["ai_photos"] = paths

        with open(new_path, "rb") as f:
            photo_bytes = f.read()

        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo_bytes,
            caption=f"✅ Новое фото #{index + 1}"
        )

        keyboard = [
            [
                InlineKeyboardButton("🔄 1", callback_data="regen_0"),
                InlineKeyboardButton("🔄 2", callback_data="regen_1"),
                InlineKeyboardButton("🔄 3", callback_data="regen_2"),
                InlineKeyboardButton("🔄 4", callback_data="regen_3"),
                InlineKeyboardButton("🔄 5", callback_data="regen_4"),
            ],
            [InlineKeyboardButton("📤 Отправить в Buffer", callback_data="send_ai_buffer")],
            [InlineKeyboardButton("➡️ Сделать следующий пост", callback_data="generate")],
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text="Нажми 🔄 чтобы перегенерировать любое фото",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(f"Regen ошибка: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


async def send_buffer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id
    buffer_user = get_user_buffer(user_id)
    paths = context.user_data.get("last_slides")
    text = context.user_data.get("current_text")

    if not buffer_user or not paths:
        await context.bot.send_message(chat_id=user_id, text="❌ Ошибка: не привязан Buffer или нет слайдов")
        return

    try:
        await query.edit_message_text("☁️ Загружаю в облако...")
        image_urls = await upload_images_to_imgbb(paths)
        await query.edit_message_text("📤 Отправляю в Buffer...")
        await send_to_buffer(buffer_user["buffer_api_key"], buffer_user["buffer_profile_id"], image_urls, text)
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Отправлено в Buffer!\n\nОткрой Buffer на телефоне и заверши публикацию.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Сделать следующий пост", callback_data="generate")]
            ])
        )
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка Buffer: {e}")


async def send_ai_buffer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id
    buffer_user = get_user_buffer(user_id)
    paths = context.user_data.get("ai_photos")

    if not buffer_user or not paths:
        await context.bot.send_message(chat_id=user_id, text="❌ Ошибка: не привязан Buffer или нет фото")
        return

    try:
        await query.edit_message_text("☁️ Загружаю AI фото в облако...")
        image_urls = await upload_images_to_imgbb(paths)
        await query.edit_message_text("📤 Отправляю в Buffer...")
        caption = "AI Фотосессия"
        await send_to_buffer(buffer_user["buffer_api_key"], buffer_user["buffer_profile_id"], image_urls, caption)
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ AI фото отправлены в Buffer!\n\nОткрой Buffer на телефоне и заверши публикацию.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Сделать следующий пост", callback_data="generate")]
            ])
        )
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка Buffer: {e}")


async def setup_buffer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    await query.edit_message_text(
        "🔗 Отправь мне Buffer API Key:\n\n"
        "Получить на: publish.buffer.com/settings/api"
    )
    return WAITING_BUFFER_KEY


async def receive_buffer_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    context.user_data["buffer_api_key"] = api_key
    try:
        profiles = await get_profiles(api_key)
        keyboard = [
            [InlineKeyboardButton(
                f"{p['service']} - {p['formatted_username']}",
                callback_data=f"profile_{p['id']}"
            )] for p in profiles
        ]
        await update.message.reply_text(
            "✅ Выбери профиль:",
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
    profile_id = query.data.replace("profile_", "")
    save_user_buffer(query.from_user.id, context.user_data["buffer_api_key"], profile_id)
    await query.edit_message_text("✅ Buffer привязан! Жми /start")
    return ConversationHandler.END


async def buffer_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    user_id = query.from_user.id
    buffer_user = get_user_buffer(user_id)
    if buffer_user:
        await query.edit_message_text("✅ Buffer подключён.")
    else:
        await query.edit_message_text("❌ Buffer не подключён.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    buffer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(setup_buffer_start, pattern="^setup_buffer$")],
        states={
            WAITING_BUFFER_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buffer_key)],
            WAITING_PROFILE: [CallbackQueryHandler(receive_profile, pattern="^profile_")],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(buffer_conv)
    app.add_handler(CallbackQueryHandler(generate, pattern="^generate$"))
    app.add_handler(CallbackQueryHandler(change_text, pattern="^change_text$"))
    app.add_handler(CallbackQueryHandler(send_buffer_handler, pattern="^send_buffer$"))
    app.add_handler(CallbackQueryHandler(send_ai_buffer_handler, pattern="^send_ai_buffer$"))
    app.add_handler(CallbackQueryHandler(ai_photoshoot, pattern="^ai_photoshoot$"))
    app.add_handler(CallbackQueryHandler(regen_photo, pattern="^regen_"))
    app.add_handler(CallbackQueryHandler(buffer_status, pattern="^buffer_status$"))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()