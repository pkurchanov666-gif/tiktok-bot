import os
import time
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Твои прямые ссылки на референсы
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

MEGA_PROMPT = """Ты — топовый fashion prompt engineer для ultra-realistic AI product photography. Специализация: рекламные фото одежды люкс-класса.

Твоя задача: при каждом запросе выдавать только ОДИН финальный промпт на английском языке для image-to-image генератора (FLUX.1 pro). Без пояснений, без заголовков, без списков, без нумерации — только один цельный готовый текст длиной не более 4900 символов.

В самом конце промпта, после всего текста, на отдельной строке обязательно добавляй одну из двух пометок:
КАДР СПЕРЕДИ — Reference Image 2
или
КАДР СЗАДИ — Reference Image 1

КРИТИЧЕСКОЕ ПРАВИЛО СТОРОН:
- If the selected angle shows the BACK of the hoodie — use the design strictly from Reference Image 1.
- If the selected angle shows the FRONT or three-quarters front — use the design strictly from Reference Image 2.
- Never mix elements from both sides in one shot.

ЖЁСТКИЕ ПРАВИЛА:
- Hoodie must have NO pocket.
- Do not change the face or body shape.
- All scenes must be evening or night only.
- Jeans must always be strictly black AND wide-leg.

СЦЕНЫ — выбери одну случайно: Moscow City skyline, Rolls-Royce interior, Bentley backseat, Lamborghini underground parking, luxury hotel corridor, private jet cabin, wet neon Moscow street, penthouse balcony.

ПОЗЫ — выбери одну случайно: confident standing, walking toward camera, leaning with crossed arms, seated with elbows on knees, hood up, chin raised.

РАКУРСЫ — выбери один случайно: Direct frontal, Slight low angle, Three-quarters left, Three-quarters right.

ВАЙБ: Dark moody luxury. Cold blue or violet shadows. Warm amber highlights. Cinematic color grading.

В КОНЦЕ ВСЕГДА ДОБАВЛЯЙ: The logo and text shown in the correct reference image are the master branding assets. Render the text on the hoodie with maximum clarity and extreme precision. Do not blur, distort, mirror, simplify, stylize, crop, fade, or alter the logo or text in any way whatsoever."""

def _post_json(url, headers, payload, timeout=300):
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise Exception(f"HTTP {r.status_code}: {r.text[:1500]}")
    return r.json()

def generate_prompt_from_groq():
    groq_key = os.getenv("GROQ_API_KEY")
    res = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        payload={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": MEGA_PROMPT}],
            "temperature": 1.0,
            "max_tokens": 2000
        }
    )
    return res["choices"][0]["message"]["content"].strip()

def parse_prompt(raw_text):
    lines = raw_text.strip().split("\n")
    last_line = lines[-1].upper()
    clean_prompt = "\n".join(lines[:-1]).strip()
    selected_ref = REF_FRONT if "СПЕРЕДИ" in last_line else REF_BACK
    return clean_prompt, selected_ref

def generate_image_with_polza(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")
    
    # Прямой вызов Media API по твоему примеру
    res = _post_json(
        "https://polza.ai/api/v1/media",
        headers={
            "Authorization": f"Bearer {polza_key}",
            "Content-Type": "application/json"
        },
        payload={
            "model": "black-forest-labs/flux.2-pro",
            "input": {
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "image_resolution": "1K",
                "images": [
                    {
                        "type": "url",
                        "data": image_url
                    }
                ]
            },
            "async": False # Ждем готовую картинку сразу
        }
    )

    print("POLZA MEDIA RESPONSE:", res)

    try:
        # Media API возвращает список ссылок в поле output
        final_url = res["output"][0]
    except Exception:
        raise Exception(f"Polza response error: {res}")

    img_data = requests.get(final_url, timeout=180).content
    os.makedirs("output", exist_ok=True)
    path = f"output/ai_fashion_{int(time.time())}.png"
    with open(path, "wb") as f:
        f.write(img_data)
    return path

async def generate_all_photos():
    raw = generate_prompt_from_groq()
    p, r = parse_prompt(raw)
    path = await asyncio.to_thread(generate_image_with_polza, p, r)
    return [path]

async def regenerate_photo(index):
    paths = await generate_all_photos()
    return paths[0]
