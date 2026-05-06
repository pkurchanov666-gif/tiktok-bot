import os
import time
import random
import requests
import asyncio

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

FRONT_SCENES = [
    "Standing next to a premium parked car with open door visible",
    "Inside a modern glass elevator with LED lighting",
    "Standing in a clean urban street environment"
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


# ---------------- SPEC ----------------

def get_next_front_spec():
    global CURRENT_FRONT_INDEX

    scene = random.choice(FRONT_SCENES)
    pose = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
    CURRENT_FRONT_INDEX += 1

    return {
        "side": "front",
        "scene": scene,
        "pose": pose,
        "seed": random.randint(100000, 999999),
        "ref": REF_FRONT
    }


def get_next_back_spec():
    global CURRENT_BACK_INDEX

    scene = random.choice(BACK_SCENES)
    pose = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
    CURRENT_BACK_INDEX += 1

    return {
        "side": "back",
        "scene": scene,
        "pose": pose,
        "seed": random.randint(100000, 999999),
        "ref": REF_BACK
    }


# ---------------- PROMPTS ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 portrait photograph. "
        "Camera distance exactly 0.7 meters. "
        "Framing from head to knees. "
        "Subject occupies 80–85% of vertical frame height. "
        "No background blur. "

        "Use the reference image exactly as hoodie source. "
        "ABSOLUTE RULE: no kangaroo pocket. No front pouch. No zippers. No drawstrings. "
        "Preserve front chest logo exactly in size and placement. "

        "Loose straight wide-leg black denim jeans. Not slim fit. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}."
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-wide environmental RAW 9:16 photograph. "
        "Camera distance exactly 10 meters. "
        "Subject occupies only 10–12% of vertical frame height. "
        "The person appears as a small distant silhouette. "
        "The architecture dominates the frame. "
        "No close-up. No medium shot. No fashion framing. "

        "Black hoodie without pocket. "
        "Hood up. Face not visible. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}."
    ) + uid


# ---------------- POLZA ----------------

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


# ---------------- GENERATION ----------------

async def generate_single_front():
    spec = get_next_front_spec()
    prompt = build_front_prompt(spec)
    job_id = submit_job(prompt, spec["ref"])
    url = await poll_job(job_id)

    img = requests.get(url)
    os.makedirs(SAVE_DIR, exist_ok=True)

    path = os.path.join(SAVE_DIR, f"front_{int(time.time()*1000)}.png")

    with open(path, "wb") as f:
        f.write(img.content)

    return path, spec


async def generate_single_back():
    spec = get_next_back_spec()
    prompt = build_back_prompt(spec)
    job_id = submit_job(prompt, spec["ref"])
    url = await poll_job(job_id)

    img = requests.get(url)
    os.makedirs(SAVE_DIR, exist_ok=True)

    path = os.path.join(SAVE_DIR, f"back_{int(time.time()*1000)}.png")

    with open(path, "wb") as f:
        f.write(img.content)

    return path, spec


# ---------------- SESSION (3 PHOTOS) ----------------

async def generate_session():
    # back → front → back
    back1, spec1 = await generate_single_back()
    await asyncio.sleep(3)

    front, spec2 = await generate_single_front()
    await asyncio.sleep(3)

    back2, spec3 = await generate_single_back()

    return [back1, front, back2], [spec1, spec2, spec3]


async def regenerate_photo(index, current_specs):
    if current_specs[index]["side"] == "front":
        return await generate_single_front()
    else:
        return await generate_single_back()
