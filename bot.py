from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]
    ])

    await update.message.reply_text(
        "Выберите режим:",
        reply_markup=keyboard
    )

async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Кнопка работает ✅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ai_handler, pattern="^ai$"))

    print("Бот погнал!")
    app.run_polling()

if __name__ == "__main__":
    main()
