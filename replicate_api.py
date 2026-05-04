import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

SAVE_DIR = "generations"
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# ---------- СЦЕНЫ (ЧИСТЫЕ, БЕЗ МЕТАЛЛА) ----------
SCENES = [
    "clean modern city street with stone pavement",
    "minimalist underground parking with smooth concrete",
    "luxury hotel entrance with neutral architectural lighting",
    "modern business district plaza with glass buildings",
    "premium pedestrian zone with clean stone tiles"
]

FRONT_POSES = [
    "one hand gripping the hood near the temple, other hand inside jeans pocket",
    "both hands adjusting hood edges near jawline",
    "one hand touching neck area, other hand hooked into pocket",
    "one hand pulling hood slightly forward, other arm relaxed but bent"
]

BACK_POSES = [
    "back facing camera, one hand resting on back of hood",
    "walking away from camera with hood up",
    "standing still facing away, one hand adjusting hood seam",
    "three-quarters back stance, head slightly lowered"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


# ---------- PYTHON РЕЖИССУРА ----------
def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX

    scene = random.choice(SCENES)

    if side == "front":
        pose = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
        ref = REF_FRONT
    else:
        pose = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
        ref = REF_BACK

    return {
        "side": side,
        "pose": pose,
        "scene": scene,
        "seed": random.randint(1, 999999),
        "ref": ref
    }


# ---------- ЧИСТЫЙ ПРОМПТ БЕЗ МЕТАЛЛА ----------
def build_prompt(spec):
    base = (
        "Ultra-realistic RAW 9:16 photograph. "
        "Sony A7R V, 35mm lens, f/11 aperture for deep focus. "
        "No background blur. No bokeh. "
        "Natural human skin tones. Visible pores. No metallic shine. "
        "No plastic effect. "
        "Black heavy cotton hoodie (500GSM). "
        "STRICT RULE: NO kangaroo pocket. NO front pouch. NO zippers. NO drawstrings. "
        "Torso must be seamless flat fabric surface. "
        "Wide-leg black denim jeans with natural fabric drape and visible stitching. "
    )

    if spec["side"] == "front":
        framing = (
            "FRONT VIEW. "
            "Camera distance exactly 0.7 meters. "
            "Framing slightly below the waist. "
            "Upper jeans and waistband visible. "
            "Subject occupies about 80% of vertical frame height. "
            "Chest logo must be sharp, readable, clean-edged. "
        )
    else:
        framing = (
            "BACK VIEW. "
            "Camera distance approximately 8 meters. "
            "Wide environmental composition. "
            "Subject occupies about 30% of vertical frame height. "
            "Hood up. Face not visible. "
        )

    context = f"Scene: {spec['scene']}. Pose: {spec['pose']}. Seed: {spec['seed']}."

    return base + framing + context


# ---------- POLZA ----------
def submit_job(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")

    response = requests.post(
        "https://polza.ai/api/v1/media",
        headers={
            "Authorization": f"Bearer {polza_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "black-forest-labs/flux.2-pro",
            "input": {
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "image_resolution": "1K",
                "images": [{"type": "url", "data": image_url}]
            },
            "async": True
        },
        timeout=30
    )

    data = response.json()
    job_id = data.get("id") or data.get("task_id")
    if not job_id:
        raise Exception(f"Polza error: {data}")
    return job_id


async def poll_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")

    for _ in range(60):
        await asyncio.sleep(5)

        try:
            res = await asyncio.to_thread(
                requests.get,
                f"https://polza.ai/api/v1/media/{job_id}",
                headers={"Authorization": f"Bearer {polza_key}"},
                timeout=30
            )
            data = res.json()
            status = (data.get("status") or "").lower()

            if status in ["succeeded", "completed", "done"]:
                output = data.get("output")
                if isinstance(output, list) and output:
                    return output[0]
        except:
            continue

    raise Exception("Generation timeout")


async def generate_single(spec):
    prompt = build_prompt(spec)
    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    img = await asyncio.to_thread(requests.get, url)
    os.makedirs(SAVE_DIR, exist_ok=True)

    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}.png")
    with open(path, "wb") as f:
        f.write(img.content)

    with Image.open(path) as im:
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.93))).save(path)

    return path


# ---------- ГЕНЕРАЦИЯ 3 ФОТО ----------
async def generate_all_photos():
    sides = ["back", "front", "back"]
    specs = [get_next_spec(s) for s in sides]

    paths = []
    for spec in specs:
        path = await generate_single(spec)
        paths.append(path)

    return paths, specs
