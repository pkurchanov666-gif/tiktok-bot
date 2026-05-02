import os
import asyncio
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

from config import BOT_TOKEN
from slides import get_random_photos, create_slides
from db import save_user_buffer, get_user_buffer
from buffer_api import get_profiles, send_to_buffer
from imgbb_api import upload_images_to_imgbb
from replicate_api import generate_all_photos, regenerate_photo

logging.basicConfig(level=logging.WARNING)

WAITING_BUFFER_KEY = 1
WAITING_PROFILE = 2

POV_PHRASES = [
    "POV: аура того самого парня который просто делает свое дело =>",
    "POV: твой парень воздуха и это буквально его аура =>",
    "POV: тот самый тип который летом начинает вставать в 6 утра, работать над собой =>",
    "POV: лучшее худи для твоего парня воздухана =>",
    "POV: худи для парней чья аура ощущается буквально так =>",
    "POV: аура того самого кента который постоянно говорит о каких-то темках =>",
    "POV: аура того самого кента который все время занят =>",
    "POV: аура того самого типа который пропал из соцсетей ради цели =>",
    "POV: твоя аура когда ты зашел в зал под правильный трек =>",
    "POV: тот самый кент у которого на уме только тренировки и бизнес =>",
    "POV: аура парня чья дисциплина пугает окружающих =>",
    "POV: худи для тех кто предпочитает делать а не говорить =>",
    "POV: аура типа который знает цену своего времени =>",
    "POV: тот самый кент который в 20 лет уже думает как построить империю =>",
    "POV: аура парня который никогда не ищет оправданий =>",
    "POV: когда твоя аура говорит громче чем твои слова =>",
    "POV: аура того самого кента который всегда на движе и в делах =>",
    "POV: тот самый тип который делает результат пока другие спят =>",
    "POV: аура парня который живет в режиме 24/7 =>",
    "POV: худи для парней с вайбом не беспокоить =>",
    "POV: аура того самого типа который не объясняет свои действия =>",
    "POV: когда у тебя и твоего кента одинаково мощная аура =>",
    "POV: аура парня который видит возможности там где другие видят стены =>",
    "POV: тот самый тип который изменился за лето до неузнаваемости =>",
    "POV: аура кента который всегда знает какой-то секретный способ заработать =>",
    "POV: худи которое добавляет плюс 100 к твоей ауре =>",
    "POV: аура парня который идет к своей цели несмотря ни на что =>",
    "POV: когда твоя аура ощущается как главный босс в комнате =>",
    "POV: аура того самого типа который молча вывозит любые трудности =>",
    "POV: тот самый кент у которого всегда есть план на миллион =>",
]


def get_random_caption():
    return random.choice(POV_PHRASES)


def build_ai_keyboard(count: int):
    regen_buttons = [
        InlineKeyboardButton(f"🔄 {i + 1}", callback_data=f"regen_{i}")
        for i in range(count)
    ]
    return InlineKeyboardMarkup([
        regen_buttons,
        [InlineKeyboardButton("📤 В Buffer", callback_data="send_ai_buffer")]
    ])


async def send_gallery_with_text(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    paths: list,
    text: str,
    keyboard: InlineKeyboardMarkup,
    done_text: str
):
    await context.bot.send_message(chat_id=user_id, text=text)

    if len(paths) == 1:
        with open(paths[0], "rb") as f:
            await context.bot.send_photo(chat_id=user_id, photo=f)
    else:
        media = []
        opened = []
        try:
            for path in paths:
                f = open(path, "rb")
                opened.append(f)
                media.append(InputMediaPhoto(media=f))
            await context.bot.send_media_group(chat_id=user_id, media=media)
        finally:
            for f in opened:
                try:
                    f.close()
                except:
                    pass

    await context.bot.send_message(
        chat_id=user_id,
        text=done_text,
        reply_markup=keyboard
    )


# ===== ФОНОВЫЕ ЗАДАЧИ =====

async def bg_generate_all(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        paths, specs = await generate_all_photos()
        caption = get_random_caption()

        # Сохраняем в user_data приложения
        app_data = context.application.user_data
        if user_id not in app_data:
            app_data[user_id] = {}
        app_data[user_id]["ai_photos"] = paths
        app_data[user_id]["ai_specs"] = specs
        app_data[user_id]["ai_caption"] = caption

        await send_gallery_with_text(
            context=context,
            user_id=user_id,
            paths=paths,
            text=caption,
            keyboard=build_ai_keyboard(len(paths)),
            done_text=f"✅ AI Фотосессия готова! Фото: {len(paths)}"
        )

    except Exception as e:
        print(f"BG generate error: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка генерации: {e}"
        )


async def bg_regenerate_one(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    index: int
):
    try:
        app_data = context.application.user_data
        user_storage = app_data.get(user_id, {})

        paths = user_storage.get("ai_photos", [])
        specs = user_storage.get("ai_specs", [])

        if not paths or not specs:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Нет данных. Сначала сгенерируй AI фотосессию."
            )
            return

        if index < 0 or index >= len(paths):
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Неверный индекс фото."
            )
            return

        new_path, new_spec = await regenerate_photo(index, specs)

        paths[index] = new_path
        specs[index] = new_spec

        caption = get_random_caption()

        app_data[user_id]["ai_photos"] = paths
        app_data[user_id]["ai_specs"] = specs
        app_data[user_id]["ai_caption"] = caption

        await send_gallery_with_text(
            context=context,
            user_id=user_id,
            paths=paths,
            text=caption,
            keyboard=build_ai_keyboard(len(paths)),
            done_text=f"✅ Фото #{index + 1} обновлено!"
        )

    except Exception as e:
        print(f"BG regen error: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка перегенерации: {e}"
        )


# ===== ХЕНДЛЕРЫ =====

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

    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    user_id = query.from_user.id

    try:
        caption = get_random_caption()

        app_data = context.application.user_data
        if user_id not in app_data:
            app_data[user_id] = {}
        app_data[user_id]["current_text"] = caption

        await query.edit_message_text("📸 Собираю реальные фото...")

        photos = get_random_photos()
        paths = await asyncio.to_thread(create_slides, caption, user_id, photos)
        app_data[user_id]["last_slides"] = paths

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Отправить в Buffer", callback_data="send_buffer")],
            [InlineKeyboardButton("➡️ Следующий пост", callback_data="generate")]
        ])

        await send_gallery_with_text(
            context=context,
            user_id=user_id,
            paths=paths,
            text=caption,
            keyboard=keyboard,
            done_text="✅ Реальные фото готовы!"
        )

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")


async def ai_photoshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    user_id = query.from_user.id

    # Сразу отвечаем — не ждём генерацию
    await query.edit_message_text(
        "⏳ Запустил генерацию 5 фото.\n"
        "Займёт 1–3 минуты.\n"
        "Пришлю когда будет готово 🔥"
    )

    # Запускаем в фоне
    asyncio.create_task(bg_generate_all(context, user_id))


async def regen_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    user_id = query.from_user.id
    index = int(query.data.replace("regen_", ""))

    # Сразу отвечаем
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔄 Перегенерирую фото #{index + 1}...\nПришлю когда будет готово."
    )

    # Запускаем в фоне
    asyncio.create_task(bg_regenerate_one(context, user_id, index))


async def send_buffer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    user_id = query.from_user.id
    buffer_user = get_user_buffer(user_id)

    app_data = context.application.user_data
    user_storage = app_data.get(user_id, {})

    is_ai_mode = "ai_buffer" in query.data

    if is_ai_mode:
        paths = user_storage.get("ai_photos")
        text = user_storage.get("ai_caption", "AI Photoshoot")
    else:
        paths = user_storage.get("last_slides")
        text = user_storage.get("current_text", "Post")

    if not buffer_user or not paths:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Привяжите Buffer или сначала создайте контент."
        )
        return

    try:
        await query.edit_message_text("☁️ Загружаю в Buffer...")

        urls = await upload_images_to_imgbb(paths)
        await send_to_buffer(
            buffer_user["buffer_api_key"],
            buffer_user["buffer_profile_id"],
            urls,
            text
        )

        await context.bot.send_message(chat_id=user_id, text="✅ Отправлено в Buffer!")

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка Buffer: {e}")


async def setup_buffer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    await query.edit_message_text("🔗 Отправь Buffer API Key:")
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
            )]
            for p in profiles
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
    except:
        pass

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
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(generate, pattern="^generate$"))
    app.add_handler(CallbackQueryHandler(ai_photoshoot, pattern="^ai_photoshoot$"))
    app.add_handler(CallbackQueryHandler(regen_photo, pattern="^regen_"))
    app.add_handler(CallbackQueryHandler(send_buffer_handler, pattern="^send_.*buffer$"))

    print("Бот погнал!")

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://tiktok-bot-production-4530.up.railway.app/{BOT_TOKEN}",
    )


if __name__ == "__main__":
    main()
