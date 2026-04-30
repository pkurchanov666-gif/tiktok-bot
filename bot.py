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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    buffer_user = get_user_buffer(user_id)
    keyboard = [
        [InlineKeyboardButton("🎬 Сгенерировать слайды", callback_data="generate")],
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai_photoshoot")],
    ]
    if buffer_user:
        keyboard.append([InlineKeyboardButton("🔁 Перепривязать Buffer", callback_data="setup_buffer")])
    else:
        keyboard.append([InlineKeyboardButton("🔗 Привязать Buffer", callback_data="setup_buffer")])
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    user_id = query.from_user.id
    try:
        text = get_next_template()
        context.user_data["current_text"] = text
        await query.edit_message_text(f"📸 Собираю слайды...\nТекст: {text}")
        photos = get_random_photos()
        paths = await asyncio.to_thread(create_slides, text, user_id, photos)
        media = [InputMediaPhoto(open(p, "rb"), caption=text if i==0 else "") for i, p in enumerate(paths)]
        await context.bot.send_media_group(chat_id=user_id, media=media)
        
        keyboard = [[InlineKeyboardButton("📤 Отправить в Buffer", callback_data="send_buffer")],
                    [InlineKeyboardButton("➡️ Следующий пост", callback_data="generate")]]
        await context.bot.send_message(chat_id=user_id, text="Слайды готовы!", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data["last_slides"] = paths
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")

async def ai_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    user_id = query.from_user.id
    try:
        await query.edit_message_text("📸 Генерирую AI фотосессию (30-60 сек)...")
        paths = await generate_all_photos()
        context.user_data["ai_photos"] = paths
        media = [InputMediaPhoto(open(p, "rb"), caption="AI Photo" if i==0 else "") for i, p in enumerate(paths)]
        await context.bot.send_media_group(chat_id=user_id, media=media)
        
        keyboard = [[InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}") for i in range(5)],
                    [InlineKeyboardButton("📤 В Buffer", callback_data="send_ai_buffer")]]
        await context.bot.send_message(chat_id=user_id, text="AI Фотосессия готова! Нажми 🔄 для замены.", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка AI: {e}")

async def regen_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))
    try:
        await context.bot.send_message(chat_id=user_id, text=f"🔄 Переделываю фото #{index+1}...")
        new_path = await regenerate_photo(index)
        context.user_data["ai_photos"][index] = new_path
        await context.bot.send_photo(chat_id=user_id, photo=open(new_path, "rb"), caption=f"✅ Новое фото #{index+1}")
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")

async def send_buffer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    user_id = query.from_user.id
    buffer_user = get_user_buffer(user_id)
    key = "ai_photos" if "ai_buffer" in query.data else "last_slides"
    paths = context.user_data.get(key)
    text = context.user_data.get("current_text", "AI Photoshoot")
    if not buffer_user or not paths:
        await context.bot.send_message(chat_id=user_id, text="❌ Ошибка: привяжите Buffer.")
        return
    try:
        await query.edit_message_text("☁️ Загрузка...")
        urls = await upload_images_to_imgbb(paths)
        await send_to_buffer(buffer_user["buffer_api_key"], buffer_user["buffer_profile_id"], urls, text)
        await context.bot.send_message(chat_id=user_id, text="✅ Отправлено в Buffer!")
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка Buffer: {e}")

async def setup_buffer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    await query.edit_message_text("🔗 Отправь Buffer API Key:")
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
    except: pass
    profile_id = query.data.replace("profile_", "")
    save_user_buffer(query.from_user.id, context.user_data["buffer_api_key"], profile_id)
    await query.edit_message_text("✅ Buffer привязан!")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(setup_buffer_start, pattern="^setup_buffer$")],
        states={
            WAITING_BUFFER_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buffer_key)],
            WAITING_PROFILE: [CallbackQueryHandler(receive_profile, pattern="^profile_")],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(generate, pattern="^generate$"))
    app.add_handler(CallbackQueryHandler(ai_photoshoot, pattern="^ai_photoshoot$"))
    app.add_handler(CallbackQueryHandler(regen_photo, pattern="^regen_"))
    app.add_handler(CallbackQueryHandler(send_buffer_handler, pattern="^send_.*buffer$"))
    print("Бот погнал!")
    app.run_polling()

if __name__ == "__main__":
    main()