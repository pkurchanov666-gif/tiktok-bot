import os
import time
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

MEGA_PROMPT = """ТВОЙ ПОЛНЫЙ МЕГА-ПРОМПТ ЗДЕСЬ"""

def _post_json(url, headers, payload, timeout=300):
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise Exception(f"HTTP {r.status_code}: {r.text[:1500]}")
    return r.json()


def generate_prompt_from_groq():
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise Exception("GROQ_API_KEY missing")

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
    if not polza_key:
        raise Exception("POLZA_API_KEY missing")

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
            "async": False
        }
    )

    print("POLZA MEDIA RESPONSE:", res)

    try:
        # media endpoint возвращает output
        final_url = res["output"][0]
    except Exception:
        raise Exception(f"Unexpected Polza response: {res}")

    img = requests.get(final_url, timeout=180)

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_fashion_{int(time.time())}.png"

    with open(path, "wb") as f:
        f.write(img.content)

    return path


async def generate_all_photos():
    raw = generate_prompt_from_groq()
    clean_prompt, selected_ref = parse_prompt(raw)
    path = await asyncio.to_thread(generate_image_with_polza, clean_prompt, selected_ref)
    return [path]


async def regenerate_photo(index):
    return (await generate_all_photos())[0]
