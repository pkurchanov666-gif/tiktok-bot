import os
import time
import random
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

SCENES = [
    "Moscow City skyline at night, glass towers reflecting neon lights",
    "Rolls-Royce interior, leather seats, ambient lighting",
    "Bentley backseat, dark tinted windows, city lights outside",
    "Lamborghini underground parking, dramatic spotlights",
    "luxury hotel corridor, marble floors, golden lighting",
    "private jet cabin, cream leather seats, night flight",
    "wet neon Moscow street, rain reflections, midnight",
    "penthouse balcony, city panorama at night",
    "VIP airport lounge, dark ambiance, premium furniture",
    "yacht deck at night, ocean horizon, moonlight",
    "five-star marble hotel lobby, chandelier lighting",
    "elite casino interior, dim dramatic lighting",
]

POSES = [
    "confident standing, hands relaxed at sides",
    "walking toward camera, slow motion vibe",
    "leaning against wall with crossed arms",
    "seated with elbows on knees, looking at camera",
    "hood up, chin slightly raised",
    "slight torso rotation, looking over shoulder",
    "hands in pockets, relaxed stance",
    "slight forward lean, direct eye contact",
]

ANGLES = [
    ("Direct frontal, chest level", "СПЕРЕДИ"),
    ("Slight low angle, looking up at subject", "СПЕРЕДИ"),
    ("Three-quarters left", "СПЕРЕДИ"),
    ("Three-quarters right", "СПЕРЕДИ"),
    ("Back view, camera facing the back", "СЗАДИ"),
    ("Three-quarters back left", "СЗАДИ"),
]

MEGA_PROMPT_TEMPLATE = """You are a top fashion prompt engineer for ultra-realistic AI product photography. Luxury streetwear editorial.

Generate ONE final image generation prompt in English. No explanations, no headers, no lists — just one solid paragraph of max 1500 characters.

Use exactly this scene: {scene}
Use exactly this pose: {pose}
Use exactly this camera angle: {angle}

STRICT RULES:
- Hoodie has NO pocket, no zipper, no extra stitching.
- Do NOT change face, body shape or proportions.
- Evening or night scene only.
- Jeans: strictly black AND wide-leg, baggy silhouette, deep rich black denim.
- Dark moody luxury atmosphere. Underexposed 1 stop. Cold blue/violet shadows. Warm amber highlights. Cinematic color grading. Subtle vignette.
- Camera: Leica Q3 or Hasselblad. Lens 35mm or 85mm. Aperture f/1.4. RAW look.
- Vertical composition, waist-up framing. Shallow depth of field.
- Ultra-realistic skin texture, detailed cotton fibers, realistic fabric folds.

{"If angle is FRONT: use front design from Reference Image 2. Logo and text must be fully readable, razor sharp, perfectly placed." if side == "СПЕРЕДИ" else "If angle is BACK: use back design from Reference Image 1. Back print must be fully visible and precisely rendered."}

The logo and text are the most important element. Render every letter with 100% accuracy. Do not blur, distort, mirror or alter the text in any way.

SEED: {seed}"""


def build_one_prompt():
    scene = random.choice(SCENES)
    pose = random.choice(POSES)
    angle_text, side = random.choice(ANGLES)
    seed = random.randint(100000, 999999)

    prompt_text = MEGA_PROMPT_TEMPLATE.format(
        scene=scene,
        pose=pose,
        angle=angle_text,
        side=side,
        seed=seed
    )

    ref = REF_FRONT if side == "СПЕРЕДИ" else REF_BACK

    return prompt_text, ref


def generate_final_prompt_from_groq(raw_prompt):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise Exception("GROQ_API_KEY missing")

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": raw_prompt}],
            "temperature": 1.3,
            "max_tokens": 1000
        },
        timeout=60
    )

    if resp.status_code >= 400:
        raise Exception(f"Groq error: {resp.text}")

    return resp.json()["choices"][0]["message"]["content"].strip()


def _extract_url(obj):
    if isinstance(obj, str) and obj.startswith("http"):
        return obj
    if isinstance(obj, list):
        for item in obj:
            found = _extract_url(item)
            if found:
                return found
    if isinstance(obj, dict):
        for key in ["output", "url", "image_url", "data", "result"]:
            if key in obj:
                found = _extract_url(obj[key])
                if found:
                    return found
    return None


def generate_single_image():
    raw_prompt, image_url = build_one_prompt()
    final_prompt = generate_final_prompt_from_groq(raw_prompt)

    polza_key = os.getenv("POLZA_API_KEY")
    if not polza_key:
        raise Exception("POLZA_API_KEY missing")

    response = requests.post(
        "https://polza.ai/api/v1/media",
        headers={
            "Authorization": f"Bearer {polza_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "black-forest-labs/flux.2-pro",
            "input": {
                "prompt": final_prompt,
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
        },
        timeout=300
    )

    try:
        res = response.json()
    except Exception:
        raise Exception(f"Non-JSON from Polza: {response.text[:500]}")

    final_url = _extract_url(res)

    if not final_url:
        raise Exception(f"No URL in Polza response: {res}")

    img = requests.get(final_url, timeout=180)
    os.makedirs("output", exist_ok=True)
    path = f"output/ai_{int(time.time() * 1000)}_{random.randint(1000, 9999)}.png"

    with open(path, "wb") as f:
        f.write(img.content)

    return path


async def generate_all_photos():
    paths = []
    errors = []

    # Запускаем 5 генераций по очереди
    for i in range(5):
        try:
            path = await asyncio.to_thread(generate_single_image)
            paths.append(path)
        except Exception as e:
            errors.append(str(e))
            print(f"Photo {i+1} failed: {e}")

        await asyncio.sleep(1)

    if paths:
        return paths

    raise Exception(errors[0] if errors else "Все генерации упали")


async def regenerate_photo(index):
    return await asyncio.to_thread(generate_single_image)
