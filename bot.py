import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import BOT_TOKEN, BUFFER_API_KEY, BUFFER_PROFILE_ID
from replicate_api import generate_all_photos, regenerate_photo
from buffer import send_to_buffer, get_profiles

logging.basicConfig(level=logging.INFO)
USER_DATA = {}

def get_user_storage(user_id):
    if user_id not in USER_DATA: USER_DATA[user_id] = {}
    return USER_DATA[user_id]

def build_ai_keyboard(count):
    buttons = [InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}") for i in range(count)]
    return InlineKeyboardMarkup([buttons, [InlineKeyboardButton("📤 Отправить в Buffer", callback_data="buffer_send")]])

async def send_media(context, user_id, paths):
    if len(paths) == 1:
        with open(paths[0], "rb") as f: await context.bot.send_photo(chat_id=user_id, photo=f)
    else:
        media = [InputMediaPhoto(open(p, "rb")) for p in paths]
        await context.bot.send_media_group(chat_id=user_id, media=media)

async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text("⏳ Запуск AI генерации (примерно 2-3 минуты)...")
    
    try:
        paths, specs, urls = await generate_all_photos()
        storage = get_user_storage(user_id)
        storage.update({"paths": paths, "specs": specs, "urls": urls, "caption": "POV: Аура уверенности"})
        
        await send_media(context, user_id, paths)
        await context.bot.send_message(chat_id=user_id, text="✅ Готово", reply_markup=build_ai_keyboard(len(paths)))
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")

async def regen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))
    storage = get_user_storage(user_id)
    
    await context.bot.send_message(chat_id=user_id, text=f"🔄 Переделываю фото {index+1}...")
    new_p, new_s, new_u = await regenerate_photo(index, storage["specs"])
    
    storage["paths"][index] = new_p
    storage["specs"][index] = new_s
    storage["urls"][index] = new_u
    
    await send_media(context, user_id, storage["paths"])
    await context.bot.send_message(chat_id=user_id, text="✅ Обновлено", reply_markup=build_ai_keyboard(len(storage["paths"])))

async def buffer_send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    storage = get_user_storage(user_id)
    
    if "urls" not in storage:
        await query.message.reply_text("❌ Сначала создай фото")
        return

    await context.bot.send_message(chat_id=user_id, text="📤 Отправка в Buffer...")
    try:
        p_id = BUFFER_PROFILE_ID
        if not p_id:
            profiles = await get_profiles(BUFFER_API_KEY)
            p_id = profiles[0]["id"]
            
        await send_to_buffer(BUFFER_API_KEY, p_id, storage["urls"], storage["caption"])
        await context.bot.send_message(chat_id=user_id, text="✅ Успешно отправлено в очередь Buffer!")
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка Buffer: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]])
    await update.message.reply_text("Выберите режим:", reply_markup=kb)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ai_handler, pattern="^ai$"))
    app.add_handler(CallbackQueryHandler(regen_handler, pattern="^regen_"))
    app.add_handler(CallbackQueryHandler(buffer_send_handler, pattern="^buffer_send$"))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
