import os
import time
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

MEGA_PROMPT = """ВСТАВЬ СЮДА СВОЙ ПОЛНЫЙ МЕГА-ПРОМПТ (как у тебя сейчас)"""

POLZA_BASE_URL = os.getenv("POLZA_BASE_URL", "https://api.polza.ai/v1")


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 180):
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    # Если Polza вернула ошибку — сразу покажем её текстом
    if r.status_code >= 400:
        raise Exception(f"HTTP {r.status_code} from {url}: {r.text[:1500]}")
    try:
        return r.json()
    except Exception:
        raise Exception(f"Non-JSON response from {url}: {r.text[:1500]}")


def generate_prompt_from_groq() -> str:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise Exception("GROQ_API_KEY is missing in Railway Variables")

    res = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        payload={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": MEGA_PROMPT}],
            "temperature": 1.0,
            "max_tokens": 2000
        },
        timeout=120
    )

    # Если тут снова когда-то будет KeyError — ты увидишь это сразу
    return res["choices"][0]["message"]["content"].strip()


def parse_prompt(raw_text: str):
    lines = raw_text.strip().split("\n")
    last_line = lines[-1].upper()
    clean_prompt = "\n".join(lines[:-1]).strip()

    # по твоему правилу
    selected_ref = REF_FRONT if "СПЕРЕДИ" in last_line else REF_BACK
    return clean_prompt, selected_ref


def generate_image_with_polza(prompt: str, image_url: str) -> str:
    polza_key = os.getenv("POLZA_API_KEY")
    if not polza_key:
        raise Exception("POLZA_API_KEY is missing in Railway Variables")

    # ВАЖНО: здесь мы намеренно используем images endpoint, а не chat,
    # чтобы уйти от истории с 'choices'
    res = _post_json(
        f"{POLZA_BASE_URL}/images/generations",
        headers={"Authorization": f"Bearer {polza_key}", "Content-Type": "application/json"},
        payload={
            "model": "black-forest-labs/flux.2-pro",
            "prompt": prompt,
            "image": image_url,         # если Polza не принимает image URL — она скажет это в тексте ошибки
            "size": "1024x1024",
            "n": 1
        },
        timeout=300
    )

    # Пытаемся вытащить URL максимально гибко
    final_url = None
    if isinstance(res, dict):
        if "data" in res and isinstance(res["data"], list) and res["data"]:
            final_url = res["data"][0].get("url")
        if not final_url and "url" in res:
            final_url = res["url"]
        if not final_url and "output" in res:
            # иногда бывает output: [url]
            out = res["output"]
            if isinstance(out, list) and out:
                final_url = out[0]
            elif isinstance(out, str):
                final_url = out

    if not final_url or not isinstance(final_url, str) or not final_url.startswith("http"):
        raise Exception(f"Polza unexpected JSON format: {str(res)[:1500]}")

    img = requests.get(final_url, timeout=180)
    if img.status_code >= 400:
        raise Exception(f"Failed to download image HTTP {img.status_code}: {img.text[:500]}")

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_fashion_{int(time.time())}.jpg"
    with open(path, "wb") as f:
        f.write(img.content)
    return path


async def generate_all_photos():
    raw = generate_prompt_from_groq()
    clean_prompt, selected_ref = parse_prompt(raw)
    path = await asyncio.to_thread(generate_image_with_polza, clean_prompt, selected_ref)
    return [path]


async def regenerate_photo(index):
    paths = await generate_all_photos()
    return paths[0]
