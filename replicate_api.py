# replicate_api.py

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

FRONT_POSES = [
    "правая рука держит край капюшона у виска, левая рука в кармане джинсов",
    "обе руки подняты и поправляют капюшон",
    "правая рука тянет капюшон вперед, левая согнута у пояса"
]

BACK_POSES = [
    "правая рука лежит на затылке поверх капюшона",
    "правая рука касается шва капюшона сзади",
    "обе руки подняты и поправляют капюшон"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


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


def build_prompt(spec):

    if spec["side"] == "front":

        return (
            "Ultra-realistic RAW 9:16 portrait photograph. "
            "Sony A7R V, 35mm lens, f/11 aperture. "
            "Camera distance exactly 0.7 meters. "
            "Framing from head to knees. "
            "Subject occupies 80–85% of frame height. "
            "No background blur. No bokeh. "
            "Black heavy cotton hoodie (500GSM). "
            "STRICT RULE: NO kangaroo pocket. NO front pouch. NO zippers. NO drawstrings. "
            "Wide black denim jeans with relaxed loose fit. "
            "Natural skin tones. "
            f"Scene: {spec['scene']}. "
            f"Pose: {spec['pose']}. "
            f"UID:{spec['seed']}"
        )

    else:

        return (
            "Ultra-realistic RAW 9:16 ultra-wide environmental photograph. "
            "Sony A7R V, 35mm lens, f/11 aperture. "
            "Camera distance MUST be exactly 10 meters. "
            "Subject occupies only 10–12% of frame height. "
            "The environment dominates the frame. "
            "No close-up. No medium shot. "
            "Black hoodie without pocket. "
            "Wide black jeans. "
            "Hood up. Face not visible. "
            f"Scene: {spec['scene']}. "
            f"Pose: {spec['pose']}. "
            f"UID:{spec['seed']}"
        )


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
    MAX_WAIT = 600
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


async def generate_all_photos():

    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]

    job_ids = []

    # отправляем 3 запроса с паузой 3 секунды
    for i, spec in enumerate(specs):
        prompt = build_prompt(spec)
        job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
        job_ids.append((job_id, spec))

        if i < 2:
            await asyncio.sleep(3)

    paths = []

    for index, (job_id, spec) in enumerate(job_ids):
        url = await poll_job(job_id)
        img = await asyncio.to_thread(requests.get, url)

        os.makedirs(SAVE_DIR, exist_ok=True)
        path = os.path.join(
            SAVE_DIR, f"ai_{int(time.time()*1000)}_{index}.png"
        )

        with open(path, "wb") as f:
            f.write(img.content)

        paths.append(path)

    return paths, specs


async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)

    prompt = build_prompt(new_spec)
    job_id = await asyncio.to_thread(submit_job, prompt, new_spec["ref"])
    url = await poll_job(job_id)

    img = await asyncio.to_thread(requests.get, url)

    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(
        SAVE_DIR, f"ai_{int(time.time()*1000)}_regen.png"
    )

    with open(path, "wb") as f:
        f.write(img.content)

    return path, new_spec
