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

# ---------- FRONT СЦЕНЫ ----------
FRONT_SCENES = [
    "Интерьер премиального автомобиля ночью с кожаным салоном и мягкой подсветкой",
    "Современный стеклянный лифт бизнес-центра с холодной LED-подсветкой",
    "Салон автомобиля с панорамной крышей и естественным светом"
]

# ---------- BACK СЦЕНЫ ----------
BACK_SCENES = [
    "Современная городская улица с полированной каменной плиткой и стеклянными фасадами",
    "Современная подземная парковка с гладким бетоном и LED-подсветкой",
    "Современная бизнес-площадь со стеклянными небоскрёбами",
    "Вход в люксовый отель с тёмным гранитом и архитектурной подсветкой"
]

# ---------- ПОЗЫ ----------
FRONT_POSES = [
    "правая рука держит край капюшона у виска, левая рука в кармане джинсов",
    "обе руки подняты и поправляют капюшон, локти разведены",
    "правая рука тянет капюшон чуть вперед, левая согнута у пояса",
    "левая рука в кармане, правая касается воротника худи"
]

BACK_POSES = [
    "правая рука лежит на затылке поверх капюшона, левая рука согнута у бедра",
    "правая рука касается шва капюшона сзади, левая рука расслаблена",
    "обе руки подняты и поправляют капюшон",
    "правая рука на капюшоне, левая немного отведена от тела"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


# ---------- СПЕЦИФИКАЦИЯ ----------
def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX

    if side == "front":
        scene = random.choice(FRONT_SCENES)
        pose = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
        ref = REF_FRONT
    else:
        scene = random.choice(BACK_SCENES)
        pose = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
        ref = REF_BACK

    return {
        "side": side,
        "scene": scene,
        "pose": pose,
        "seed": random.randint(1, 999999),
        "ref": ref
    }


# ---------- ПРОМПТ ----------
def build_prompt(spec):

    base = (
        "Ultra-realistic RAW 9:16 photograph. "
        "Sony A7R V, 35mm lens, f/11 aperture for deep focus. "
        "No background blur. No bokeh. "
        "Natural human skin tones. Visible pores. No metallic reflections. "
        "Black heavy cotton hoodie (500GSM). "
        "STRICT RULE: NO kangaroo pocket. NO front pouch. NO zippers. NO drawstrings. "
        "Torso must be seamless flat fabric surface. "
        "Wide-leg black denim шаровары with heavy drape and visible stitching. "
    )

    if spec["side"] == "front":
        framing = (
            "FRONT VIEW. "
            "Camera distance exactly 0.7 meters. "
            "Framing from head to knees. "
            "Subject occupies approximately 80–85% of vertical frame height. "
            "Chest logo must be sharp and readable. "
        )
    else:
        framing = (
            "BACK VIEW. "
            "Camera distance approximately 10 meters. "
            "Wide environmental composition. "
            "Subject occupies about 25–30% of vertical frame height. "
            "The environment visually dominates the frame. "
            "Hood fully up. Face not visible. "
        )

    context = f"Scene: {spec['scene']}. Pose: {spec['pose']}. Seed: {spec['seed']}."

    return base + framing + context


# ---------- POLZA API ----------
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
    specs = [get_next_spec(side) for side in sides]

    paths = []
    for spec in specs:
        path = await generate_single(spec)
        paths.append(path)

    return paths, specs


async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single(new_spec)
    return path, new_spec
