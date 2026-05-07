import os
import time
import random
import requests
import asyncio

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

FRONT_SCENES = [
    "Standing next to a premium parked car in a realistic urban setting",
    "Standing in a clean modern city street with architecture visible behind",
    "Standing near the entrance of a luxury building with realistic urban background"
]

BACK_SCENES = [
    "Modern city street with stone pavement and realistic urban depth",
    "Underground parking garage with visible concrete pillars and open space",
    "Contemporary business plaza with open architectural background"
]

FRONT_POSES = [
    "right hand gripping the hood near the temple, left hand in jeans pocket",
    "both hands adjusting the hood from the front",
    "right hand pulling hood slightly forward, chin slightly down"
]

BACK_POSES = [
    "standing completely still, arms relaxed at sides, facing away",
    "slowly walking away from camera, natural stride",
    "right hand resting on the back of the hood, facing away"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


# ---------------- SPEC ----------------

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
        "seed": random.randint(100000, 999999),
        "ref": ref
    }


# ---------------- PROMPTS ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 environmental fashion photograph. "
        "Sony A7R V, 35mm lens, f/8 to f/11 aperture. "
        "Camera at eye level, straight-on angle. "
        "No high angle. No low angle. No tilt. "
        "Camera distance approximately 1.2 to 1.8 meters from subject. "

        "Framing from head to knees. "
        "Subject occupies approximately 65 to 75 percent of the vertical frame height. "

        "The person must feel naturally placed inside the environment. "
        "Not isolated from background. Not floating. "
        "Subject and background exist as one unified scene. "

        "Deep depth of field. "
        "Background is sharp and fully in focus. "
        "No bokeh. No background blur. No shallow depth of field. "
        "Not a studio portrait. Not a cutout look. "
        "Photographed by a standing photographer on location. "

        "Hoodie copied exactly from reference image. "
        "ABSOLUTE RULE: no kangaroo pocket. No front pouch. No zipper. No drawstrings visible. "
        "Front chest logo preserved exactly — same size, same position, same design. "

        "Bottoms: loose straight wide-leg black denim jeans. "
        "Clearly baggy silhouette around thighs and calves. "
        "Not slim fit. Not skinny. Not tapered. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 environmental fashion photograph. "
        "Sony A7R V, 35mm lens, f/8 to f/11 aperture. "

        "Photographed by a standing photographer at normal human eye level. "
        "Camera height approximately 1.6 meters from ground. "
        "Camera pointed straight forward, parallel to ground. "
        "STRICT RULE: no high-angle shot. No top-down view. "
        "No aerial view. No drone perspective. No elevated camera position. "
        "No surveillance camera angle. No rooftop angle. No balcony angle. "

        "Camera distance approximately 6 to 8 meters from subject. "
        "Full body visible from head to feet. "
        "Subject occupies approximately 28 to 35 percent of the vertical frame height. "
        "The person is clearly visible and readable. "
        "The person naturally belongs to the scene and environment. "

        "The surrounding environment is clearly visible and sharp. "
        "Deep depth of field. Everything in focus. No blur. "
        "No close-up. No portrait crop. No zoomed-in framing. "
        "Natural street-level perspective. "

        "Subject: black hoodie without any pocket. "
        "Loose straight wide black jeans. "
        "Hood up. Face completely hidden. "
        "Entire body seen from behind. No face visible at any angle. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
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


def extract_url(obj):
    if isinstance(obj, str) and obj.startswith("http"):
        return obj
    if isinstance(obj, list):
        for item in obj:
            found = extract_url(item)
            if found:
                return found
    if isinstance(obj, dict):
        for value in obj.values():
            found = extract_url(value)
            if found:
                return found
    return None


async def poll_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")

    MAX_WAIT = 600
    INTERVAL = 5
    waited = 0

    while waited < MAX_WAIT:
        await asyncio.sleep(INTERVAL)
        waited += INTERVAL

        response = await asyncio.to_thread(
            requests.get,
            f"https://polza.ai/api/v1/media/{job_id}",
            headers={"Authorization": f"Bearer {polza_key}"},
            timeout=30
        )

        data = response.json()
        url = extract_url(data)

        if url and "ibb.co" not in url:
            return url

    raise Exception("Generation timeout")


# ---------------- DOWNLOAD ----------------

async def download_image(url, path):
    response = await asyncio.to_thread(requests.get, url, timeout=60)
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(response.content)


# ---------------- GENERATION ----------------

async def generate_all_photos():
    specs = [
        get_next_spec("back"),
        get_next_spec("front"),
        get_next_spec("back")
    ]

    job_ids = []

    for i, spec in enumerate(specs):
        if spec["side"] == "front":
            prompt = build_front_prompt(spec)
        else:
            prompt = build_back_prompt(spec)

        job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
        job_ids.append(job_id)

        if i < len(specs) - 1:
            await asyncio.sleep(3)

    # Поллим все джобы параллельно
    urls = await asyncio.gather(*[poll_job(job_id) for job_id in job_ids])

    paths = []
    for index, url in enumerate(urls):
        path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}_{index}.png")
        await download_image(url, path)
        paths.append(path)

    return paths, specs, list(urls)


async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    spec = get_next_spec(side)

    if side == "front":
        prompt = build_front_prompt(spec)
    else:
        prompt = build_back_prompt(spec)

    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}_regen.png")
    await download_image(url, path)

    return path, spec, url
