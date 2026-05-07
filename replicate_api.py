import os
import time
import random
import requests
import asyncio

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# ---------------- СЦЕНЫ ----------------

FRONT_SCENES = [
    "Standing next to a premium parked car on an empty parking lot",
    "Standing in a clean minimalist urban street, modern architecture behind",
    "Standing in front of a luxury building entrance, glass doors behind"
]

BACK_SCENES = [
    # Убрал лифт — модель рисует его крупно
    "Wide open modern city street with stone pavement, shot from far distance",
    "Large underground parking garage, wide space, concrete pillars",
    "Contemporary business plaza, wide open area with fountain",
    "Wide empty rooftop terrace of a skyscraper, city skyline behind"
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


# ---------------- ПРОМПТЫ ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 portrait photograph. "
        "Sony A7R V, 35mm lens, f/11 aperture. "
        "Camera placed exactly 0.7 meters from subject. "
        "Framing from top of head to knees, nothing more. "
        "Subject occupies 80 to 85 percent of vertical frame height. "
        "Sharp background, no bokeh, no blur. "

        "Hoodie copied exactly from reference image. "
        "STRICT: absolutely no kangaroo pocket, no front pouch, no zipper, no drawstrings visible. "
        "Front chest logo preserved exactly — same size, same position. "

        "Bottoms: loose straight wide-leg black denim jeans. "
        "Clearly baggy silhouette around thighs and calves. "
        "Not slim fit. Not skinny jeans. Not tapered. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 environmental street photograph. "
        "Sony A7R V, 24mm wide-angle lens, f/11 aperture. "

        # Главное — расстояние и размер фигуры
        "CRITICAL: camera is placed very far from the subject, minimum 15 to 20 meters away. "
        "CRITICAL: the human figure must be very small — occupying only 15 to 20 percent "
        "of the total vertical frame height. "
        "CRITICAL: do not crop. Do not zoom in. Do not fill frame with the person. "
        "The person is a small silhouette inside a large environment. "

        # Окружение важнее персонажа
        "The environment, architecture and background occupy at least 80 percent of the frame. "
        "Show the full width and depth of the location. "
        "Large open space. Strong sense of depth and distance. "

        # Персонаж
        "Person: wearing a plain black hoodie with hood up, face completely hidden. "
        "Loose wide black jeans. "
        "Viewed entirely from behind. No face visible at any angle. "

        # Стиль
        "Cinematic mood. Natural lighting. Sharp everywhere. No blur. "
        "No portrait framing. No close-up. Wide establishing shot. "

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

    # Поллим параллельно
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
