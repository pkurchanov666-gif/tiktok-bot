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
    "Standing next to a premium parked car with open door visible",
    "Inside a modern glass elevator with LED lighting",
    "Standing near a luxury vehicle with city reflections"
]

BACK_SCENES = [
    "Modern city street with clean stone pavement",
    "Underground parking level with smooth concrete floor",
    "Contemporary business plaza with glass buildings"
]

FRONT_POSES = [
    "right hand gripping the hood near the temple, left hand in jeans pocket",
    "both hands adjusting the hood",
    "right hand pulling hood slightly forward"
]

BACK_POSES = [
    "right hand resting on the back of the hood",
    "walking away with hood up",
    "standing still facing away"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


# ---------- SPEC ----------
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


# ---------- PROMPT ----------
def build_prompt(spec):

    uid = f" UID:{spec['seed']}-{random.random()}"

    if spec["side"] == "front":

        return (
            "Ultra-realistic RAW 9:16 portrait photograph. "
            "Sony A7R V, 35mm lens, f/11 aperture. "
            "Camera distance exactly 0.7 meters. "
            "Framing from head to knees. "
            "Subject occupies 80–85% of vertical frame height. "
            "No background blur. No bokeh. "

            "Use the provided reference image as the exact hoodie source. "
            "HIGH PRIORITY: preserve hoodie design exactly as shown in reference. "
            "The front chest logo must remain identical in size, placement and typography. "
            "Do not remove or redesign the logo. "

            "Black heavy cotton hoodie without pocket. "
            "Wide black denim jeans with relaxed loose fit. "

            f"Scene: {spec['scene']}. "
            f"Pose: {spec['pose']}."
        ) + uid

    else:

        return (
            "Ultra-realistic RAW 9:16 ultra-wide environmental photograph. "
            "Sony A7R V, 35mm lens, f/11 aperture. "
            "Camera distance MUST be exactly 10 meters. "
            "Subject occupies only 10–12% of vertical frame height. "
            "The person appears as a distant silhouette. "
            "The architecture dominates the frame. "
            "No close-up. No medium shot. "

            "Black hoodie without pocket. "
            "Hood up. Face not visible. "

            f"Scene: {spec['scene']}. "
            f"Pose: {spec['pose']}."
        ) + uid


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


# ---------- GENERATE SINGLE ----------
async def generate_single(spec):

    prompt = build_prompt(spec)
    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    response = await asyncio.to_thread(requests.get, url, timeout=180)

    if response.status_code != 200:
        raise Exception("Image download failed")

    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}.png")

    with open(path, "wb") as f:
        f.write(response.content)

    if os.path.getsize(path) == 0:
        raise Exception("Downloaded image is empty")

    return path


# ---------- GENERATE 3 ----------
async def generate_all_photos():

    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]

    job_ids = []

    for i, spec in enumerate(specs):
        prompt = build_prompt(spec)
        job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
        job_ids.append((job_id, spec))

        if i < 2:
            await asyncio.sleep(3)

    paths = []

    for job_id, spec in job_ids:
        path = await generate_single(spec)
        paths.append(path)

    return paths, specs


async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single(new_spec)
    return path, new_spec
