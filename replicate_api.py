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

# ---------- СЦЕНЫ ----------
FRONT_SCENES = [
    "Интерьер премиального автомобиля с кожаным салоном",
    "Современный стеклянный лифт бизнес-центра",
    "Салон автомобиля с панорамной крышей"
]

BACK_SCENES = [
    "Современная городская улица с каменной плиткой",
    "Подземная парковка с гладким бетоном",
    "Современная бизнес-площадь со стеклянными фасадами",
    "Вход в люксовый отель с гранитной отделкой"
]

# ---------- ПОЗЫ ----------
FRONT_POSES = [
    "правая рука держит край капюшона у виска, левая рука в кармане джинсов",
    "обе руки подняты и поправляют капюшон",
    "правая рука тянет капюшон вперед, левая согнута у пояса",
    "левая рука в кармане, правая касается воротника худи"
]

BACK_POSES = [
    "правая рука лежит на затылке поверх капюшона, левая согнута у бедра",
    "правая рука касается шва капюшона сзади, левая расслаблена",
    "обе руки подняты и поправляют капюшон",
    "правая рука на капюшоне, левая слегка отведена"
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


# ---------- ДЛИННЫЙ ПРОМПТ 200+ СЛОВ ----------
def build_prompt(spec):

    camera_block = (
        "Ultra-realistic RAW 9:16 photograph captured on a Sony A7R V with a 35mm lens set to f/11 aperture. "
        "The image maintains deep focus across the entire frame with absolutely no background blur and no bokeh. "
        "Every distant architectural surface remains sharp and clearly defined. "
    )

    skin_block = (
        "Natural human skin tones must be preserved with visible pores and realistic softness. "
        "Skin should not appear metallic, glossy, plastic-like or artificially smoothed. "
        "Subtle natural texture and authentic light falloff must be present. "
    )

    hoodie_block = (
        "The hoodie is made from heavy 500GSM black cotton fabric with visible textile weave and natural folds. "
        "STRICT RULE: NO kangaroo pocket, NO front pouch, NO zippers, NO drawstrings. "
        "The entire torso must remain smooth and uninterrupted without stitching indicating a pocket. "
    )

    jeans_block = (
        "The jeans are wide black denim with relaxed loose fit. "
        "Fabric drapes naturally around hips and knees with visible stitching at waistband and pockets. "
        "Denim grain appears realistic without stiffness. "
    )

    if spec["side"] == "front":

        framing_block = (
            "FRONT VIEW. Camera distance exactly 0.7 meters. "
            "Framing from head to knees. "
            "Subject occupies approximately 80–85 percent of vertical frame height. "
            "The chest logo must be sharply rendered and fully readable. "
        )

    else:

        framing_block = (
            "BACK VIEW. Camera distance MUST be exactly 10 meters and must not be closer. "
            "Ultra-wide environmental composition. "
            "Subject occupies only 12–15 percent of vertical frame height. "
            "The environment visually dominates the frame. "
            "No portrait framing and no close-up crop. "
            "Hood fully up. Face not visible. "
        )

    environment_block = (
        f"Scene: {spec['scene']}. "
        "Architectural lines, pavement seams, building edges and glass reflections must remain crisp and clearly resolved. "
        "Lighting is neutral urban light around 4500K with balanced exposure and realistic shadow falloff. "
    )

    pose_block = f"Pose: {spec['pose']}. "

    return (
        camera_block +
        skin_block +
        hoodie_block +
        jeans_block +
        framing_block +
        environment_block +
        pose_block
    )


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

    MAX_WAIT = 900
    INTERVAL = 5
    waited = 0

    while waited < MAX_WAIT:
        await asyncio.sleep(INTERVAL)
        waited += INTERVAL

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
