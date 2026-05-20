import logging
import random
import json
import os
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN
from slides import get_random_photos, create_slides
from replicate_api import (
    generate_all_photos,
    regenerate_photo,
    get_unique_specs,
    build_front_prompt,
    build_back_prompt,
    MODEL_NAME,
    IMAGE_RESOLUTION,
    ASPECT_RATIO,
    OUTPUT_FORMAT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_DATA = {}
USER_DATA_FILE = "user_data.json"
GRAPHQL_URL = "https://api.buffer.com/graphql"

POV_PHRASES = [
    "POV: аура того самого парня который просто делает свое дело =>",
    "POV: твой парень воздуха и это буквально его аура =>",
    "POV: тот самый тип который летом начинает вставать в 6 утра, работать над собой =>",
    "POV: худи для парней чья аура ощущается буквально так =>",
    "POV: лучшее худи для твоего парня воздухана =>",
    "POV: аура того самого кента который все время занят =>",
    "POV: тот самый кент у которого на уме только тренировки и бизнес =>",
    "POV: когда твоя аура говорит громче чем твои слова =>",
    "POV: аура того самого кента который всегда на движе и в делах =>",
    "POV: тот самый тип который делает результат пока другие спят =>"
]


# ---------------- STORAGE ----------------

def load_user_data():
    global USER_DATA
    if not os.path.exists(USER_DATA_FILE):
        USER_DATA = {}
        return
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            USER_DATA = json.load(f)
    except Exception:
        USER_DATA = {}


def save_user_data():
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[STORAGE] Save error: {e}")


def get_user_storage(user_id):
    user_id = str(user_id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    return USER_DATA[user_id]


def get_random_caption():
    return random.choice(POV_PHRASES)


def get_clean_urls(storage):
    raw = storage.get("urls", [])
    return [u for u in raw if u and isinstance(u, str) and u.startswith("http")]


# ---------------- BUFFER API ----------------

async def graphql_request(api_key, query, variables=None):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            GRAPHQL_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "variables": variables or {}
            }
        )
    try:
        data = response.json()
    except Exception:
        raise Exception(f"Buffer вернул не JSON: {response.text}")
    if response.status_code >= 400:
        raise Exception(f"Buffer ошибка {response.status_code}: {data}")
    if "errors" in data:
        raise Exception(f"Buffer GraphQL ошибка: {data['errors']}")
    return data.get("data", {})


async def get_profiles(api_key):
    account_data = await graphql_request(
        api_key, "{ account { organizations { id name } } }"
    )
    organizations = account_data.get("account", {}).get("organizations", [])
    if not organizations:
        raise Exception("У аккаунта Buffer нет организаций")
    org_id = organizations[0]["id"]

    channels_query = """
    query GetChannels($input: ChannelsInput!) {
      channels(input: $input) { id name service }
    }
    """
    channels_data = await graphql_request(
        api_key, channels_query, {"input": {"organizationId": org_id}}
    )
    profiles = []
    for ch in channels_data.get("channels", []):
        profiles.append({
            "id": ch.get("id"),
            "service": ch.get("service", "unknown"),
            "formatted_username": ch.get("name") or ch.get("id"),
        })
    return profiles


async def send_to_buffer(api_key, profile_id, image_urls, caption):
    clean_urls = [u for u in image_urls if u and isinstance(u, str) and u.startswith("http")]
    if not clean_urls:
        raise Exception("Нет валидных URL для отправки в Buffer")

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess { post { id } }
        ... on InvalidInputError { message }
        ... on NotFoundError { message }
        ... on UnauthorizedError { message }
        ... on UnexpectedError { message }
        ... on RestProxyError { message }
        ... on LimitReachedError { message }
      }
    }
    """
    variables = {
        "input": {
            "channelId": profile_id,
            "text": caption,
            "schedulingType": "notification",
            "mode": "addToQueue",
            "assets": {
                "images": [{"url": url} for url in clean_urls]
            }
        }
    }
    data = await graphql_request(api_key, mutation, variables)
    result = data.get("createPost", {})
    typename = result.get("__typename", "")
    if typename != "PostActionSuccess":
        raise Exception(result.get("message", f"Buffer ошибка: {typename}"))
    return True


# ---------------- KEYBOARDS ----------------

def build_ai_keyboard(user_id, count):
    storage = get_user_storage(user_id)
    buffer_connected = bool(
        storage.get("buffer_api_key") and storage.get("buffer_profile_id")
    )

    rows = []

    if count > 0:
        regen_buttons = [
            InlineKeyboardButton(f"🔄 {i+1}", callback_data=f"regen_{i}")
            for i in range(count)
        ]
        rows.append(regen_buttons)

    rows.append([
        InlineKeyboardButton("🔄 Фраза", callback_data="regen_caption")
    ])

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

    rows.append([
        InlineKeyboardButton("🏠 В меню", callback_data="go_start")
    ])

    return InlineKeyboardMarkup(rows)


def build_start_keyboard(user_id):
    storage = get_user_storage(user_id)
    buffer_connected = bool(
        storage.get("buffer_api_key") and storage.get("buffer_profile_id")
    )

    buttons = [
        [InlineKeyboardButton("🎬 Слайды", callback_data="slides")],
        [InlineKeyboardButton("📸 AI Фотосессия", callback_data="ai")]
    ]

    if buffer_connected:
        profile_name = storage.get("buffer_profile_name", "подключён")
        buttons.append([
            InlineKeyboardButton(f"🔁 Buffer: {profile_name}", callback_data="buffer_connect")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🔗 Привязать Buffer", callback_data="buffer_connect")
        ])

    return InlineKeyboardMarkup(buttons)


# ---------------- SEND MEDIA ----------------

async def send_preview(context, user_id, paths):
    """Сжатое превью для быстрого просмотра"""
    valid_paths = [p for p in paths if p and os.path.exists(p)]
    if not valid_paths:
        raise Exception("Файлы не найдены")

    opened_files = []
    try:
        if len(valid_paths) == 1:
            f = open(valid_paths[0], "rb")
            opened_files.append(f)
            await context.bot.send_photo(chat_id=user_id, photo=f)
        else:
            media = []
            for path in valid_paths:
                f = open(path, "rb")
                opened_files.append(f)
                media.append(InputMediaPhoto(f))
            await context.bot.send_media_group(chat_id=user_id, media=media)
    finally:
        for f in opened_files:
            try:
                f.close()
            except Exception:
                pass


async def send_media(context, user_id, paths):
    """Оригиналы как документы без потери качества"""
    valid_paths = [p for p in paths if p and os.path.exists(p)]
    if not valid_paths:
        raise Exception("Файлы не найдены")

    opened_files = []
    try:
        for path in valid_paths:
            f = open(path, "rb")
            opened_files.append(f)
            await context.bot.send_document(
                chat_id=user_id,
                document=f,
                filename=os.path.basename(path)
            )
    finally:
        for f in opened_files:
            try:
                f.close()
            except Exception:
                pass


# ---------------- START / MENU ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        "Выберите режим:",
        reply_markup=build_start_keyboard(user_id)
    )


async def go_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.message.reply_text(
        "Выберите режим:",
        reply_markup=build_start_keyboard(user_id)
    )


# ---------------- DEBUG ----------------

async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    specs = get_unique_specs()
    message = "🔍 DEBUG — что улетит в Polza:\n\n"

    for i, spec in enumerate(specs):
        if spec["side"] == "front":
            prompt = build_front_prompt(spec)
        else:
            prompt = build_back_prompt(spec)

        message += (
            f"📸 ФОТО {i+1} ({spec['side'].upper()})\n"
            f"🤖 Модель: {MODEL_NAME}\n"
            f"📐 Разрешение: {IMAGE_RESOLUTION}\n"
            f"📏 Соотношение: {ASPECT_RATIO}\n"
            f"🖼 Формат: {OUTPUT_FORMAT}\n"
            f"🧍 Субъект (фото 1): {spec['ref']}\n"
            f"🌆 Фон (фото 2): {spec['background']}\n"
            f"📦 Images в запросе: 2\n"
            f"✏️ Промпт ({len(prompt)} символов):\n"
            f"{prompt[:200]}...\n"
            f"{'─' * 30}\n"
        )

    await update.message.reply_text(message)


# ---------------- SLIDES ----------------

async def generate_slides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    caption = get_random_caption()

    await query.edit_message_text("📸 Генерация слайдов...")

    try:
        photos = get_random_photos()
        paths = create_slides(caption, user_id, photos)

        storage = get_user_storage(user_id)
        storage["paths"] = paths
        storage["caption"] = caption
        storage["mode"] = "slides"
        storage.pop("urls", None)
        storage.pop("specs", None)
        save_user_data()

        await send_preview(context, user_id, paths)

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Слайды готовы"
        )

    except Exception as e:
        logger.error(f"[SLIDES] Error: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка слайдов: {e}"
        )


# ---------------- AI GENERATION ----------------

async def background_ai_generate(context, user_id):
    try:
        paths, specs, urls = await generate_all_photos()

        if not paths:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка генерации — не получено ни одного фото"
            )
            return

        safe_specs = []
        for s in specs:
            safe_specs.append({
                k: v for k, v in s.items()
                if isinstance(v, (str, int, float, bool, type(None)))
            })

        safe_urls = [
            u if (u and isinstance(u, str) and u.startswith("http")) else None
            for u in urls
        ]

        storage = get_user_storage(user_id)
        storage["paths"] = paths
        storage["specs"] = safe_specs
        storage["urls"] = safe_urls
        storage["caption"] = get_random_caption()
        storage["mode"] = "ai"
        save_user_data()

        await send_preview(context, user_id, paths)
        await send_media(context, user_id, paths)

        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ AI фотосессия готова\n\n{storage['caption']}",
            reply_markup=build_ai_keyboard(user_id, len(paths))
        )

    except Exception as e:
        import traceback
        logger.error(f"[AI_GENERATE] Error: {traceback.format_exc()}")
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


# ---------------- REGEN CAPTION ----------------

async def regen_caption_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    storage = get_user_storage(user_id)

    old_caption = storage.get("caption", "")
    new_caption = old_caption
    for _ in range(20):
        candidate = get_random_caption()
        if candidate != old_caption:
            new_caption = candidate
            break

    storage["caption"] = new_caption
    save_user_data()

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔄 Новая фраза:\n\n{new_caption}",
        reply_markup=build_ai_keyboard(user_id, len(storage.get("paths", [])))
    )


# ---------------- REGEN PHOTO ----------------

async def regen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    storage = get_user_storage(user_id)

    try:
        index = int(query.data.replace("regen_", ""))
    except Exception:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Неверный индекс фото"
        )
        return

    if "paths" not in storage or "specs" not in storage or "urls" not in storage:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Сначала сгенерируй AI фотосессию"
        )
        return

    if index < 0 or index >= len(storage["paths"]):
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Неверный номер фото"
        )
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔄 Перегенерация фото {index + 1}..."
    )

    try:
        new_path, new_spec, new_url = await regenerate_photo(index, storage["specs"])

        if not new_path or not new_spec or not new_url:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка генерации — пустой результат"
            )
            return

        safe_spec = {
            k: v for k, v in new_spec.items()
            if isinstance(v, (str, int, float, bool, type(None)))
        }

        storage["paths"][index] = new_path
        storage["specs"][index] = safe_spec
        storage["urls"][index] = new_url if (new_url and isinstance(new_url, str)) else None
        save_user_data()

        await send_preview(context, user_id, [new_path])
        await send_media(context, user_id, [new_path])

        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Фото {index + 1} обновлено\n\n{storage['caption']}",
            reply_markup=build_ai_keyboard(user_id, len(storage["paths"]))
        )

    except Exception as e:
        import traceback
        logger.error(f"[REGEN] Error: {traceback.format_exc()}")
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
            "🔗 Отправь свой Buffer API ключ одним сообщением.\n\n"
            "Как получить:\n"
            "1. Зайди на buffer.com\n"
            "2. Settings → Apps & Extras\n"
            "3. Manage Apps → Create an App\n"
            "4. Скопируй API Key\n\n"
            "Просто вставь его сюда одним сообщением."
        )
    )


async def buffer_token_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    storage = get_user_storage(user_id)

    if not storage.get("awaiting_buffer_token"):
        return

    api_key = update.message.text.strip()
    storage["awaiting_buffer_token"] = False
    save_user_data()

    await update.message.reply_text("⏳ Проверяю Buffer API ключ...")

    try:
        profiles = await get_profiles(api_key)

        if not profiles:
            await update.message.reply_text(
                "❌ У Buffer аккаунта не найдено профилей.\n"
                "Сначала подключи соцсеть в Buffer."
            )
            return

        profile = profiles[0]
        profile_id = profile.get("id")
        profile_name = profile.get("formatted_username") or profile_id
        profile_service = profile.get("service", "unknown")

        storage["buffer_api_key"] = api_key
        storage["buffer_profile_id"] = profile_id
        storage["buffer_profile_name"] = profile_name
        storage["buffer_service"] = profile_service
        save_user_data()

        if storage.get("mode") == "ai" and storage.get("paths"):
            reply_markup = build_ai_keyboard(user_id, len(storage.get("paths", [])))
        else:
            reply_markup = build_start_keyboard(user_id)

        await update.message.reply_text(
            f"✅ Buffer привязан!\n"
            f"Профиль: {profile_name}\n"
            f"Сервис: {profile_service}",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"[BUFFER_CONNECT] Error: {e}")
        await update.message.reply_text(f"❌ Не удалось привязать Buffer: {e}")


# ---------------- BUFFER SEND ----------------

async def buffer_send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    storage = get_user_storage(user_id)

    buffer_api_key = storage.get("buffer_api_key")
    buffer_profile_id = storage.get("buffer_profile_id")
    caption = storage.get("caption", get_random_caption())

    if not buffer_api_key or not buffer_profile_id:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Сначала привяжи Buffer"
        )
        return

    if storage.get("mode") != "ai":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ В Buffer можно отправить только AI фотосессию"
        )
        return

    image_urls = get_clean_urls(storage)

    if not image_urls:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Нет валидных URL. Сначала сгенерируй AI фотосессию"
        )
        return

    await context.bot.send_message(
        chat_id=user_id,
        text="📤 Отправляю в Buffer..."
    )

    try:
        await send_to_buffer(
            api_key=buffer_api_key,
            profile_id=buffer_profile_id,
            image_urls=image_urls,
            caption=caption
        )

        profile_name = storage.get("buffer_profile_name", "профиль")

        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Отправлено в Buffer\nПрофиль: {profile_name}"
        )

    except Exception as e:
        error_text = str(e)
        logger.error(f"[BUFFER_SEND] Error: {e}")

        if "Unauthorized" in error_text or "401" in error_text:
            storage.pop("buffer_api_key", None)
            storage.pop("buffer_profile_id", None)
            storage.pop("buffer_profile_name", None)
            storage.pop("buffer_service", None)
            save_user_data()

            await context.bot.send_message(
                chat_id=user_id,
                text="❌ API ключ Buffer недействителен. Привяжи заново.",
                reply_markup=build_start_keyboard(user_id)
            )
            return

        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ошибка Buffer: {e}"
        )


# ---------------- MAIN ----------------

def main():
    load_user_data()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("debug", debug_handler))
    app.add_handler(CallbackQueryHandler(go_start_handler, pattern="^go_start$"))
    app.add_handler(CallbackQueryHandler(generate_slides, pattern="^slides$"))
    app.add_handler(CallbackQueryHandler(ai_handler, pattern="^ai$"))
    app.add_handler(CallbackQueryHandler(regen_caption_handler, pattern="^regen_caption$"))
    app.add_handler(CallbackQueryHandler(regen_handler, pattern="^regen_\\d+$"))
    app.add_handler(CallbackQueryHandler(buffer_connect_handler, pattern="^buffer_connect$"))
    app.add_handler(CallbackQueryHandler(buffer_send_handler, pattern="^buffer_send$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buffer_token_message_handler))

    print("Бот погнал!")
    app.run_polling()


if __name__ == "__main__":
    main()
