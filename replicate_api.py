import os
import time
import random
import requests
import asyncio

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

FRONT_SCENES = [
    "Standing next to a premium parked car",
    "Inside a modern glass elevator",
    "Standing in a clean urban street"
]

BACK_SCENES = [
    "Modern city street with stone pavement",
    "Underground parking level",
    "Contemporary business plaza"
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
        "Ultra-realistic RAW 9:16 portrait photograph. "
        "Sony A7R V, 35mm lens, f/11 aperture. "
        "Camera distance exactly 0.7 meters. "
        "Framing from head to knees. "
        "Subject occupies approximately 80–85 percent of vertical frame height. "
        "No background blur. "

        "Use the reference image exactly as hoodie source. "
        "ABSOLUTE RULE: no kangaroo pocket. No front pouch. No zippers. No drawstrings. "
        "Preserve front chest logo exactly in size and placement. "

        "Loose straight wide-leg black denim jeans. "
        "Clearly wide silhouette around thighs and calves. "
        "Not slim fit. Not skinny. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}."
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 environmental photograph. "
        "Sony A7R V, 35mm lens, f/11 aperture. "
        "Camera distance exactly 10 meters. "
        "Subject occupies approximately 18–22 percent of vertical frame height. "
        "The environment remains clearly visible. "
        "No close-up. No portrait framing. "

        "Black hoodie without pocket. "
        "Loose straight wide black jeans silhouette. "
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

        # Пропускаем ссылки на сами референсы чтобы не вернуть input вместо output
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

    # Сабмитим все джобы подряд
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

    # Скачиваем все фото
    paths = []

    for index, url in enumerate(urls):
        path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}_{index}.png")
        await download_image(url, path)
        paths.append(path)

    # Возвращаем paths, specs, urls — urls нужны для Buffer
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

    # Возвращаем path, spec, url — url нужен чтобы обновить storage["urls"]
    return path, spec, url
