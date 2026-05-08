import os
import time
import random
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# ---------------- FRONT SCENES ----------------

FRONT_SCENES = [
    {
        "scene": "leaning against a dark Porsche parked in a clean underground garage, "
                 "car door and fender very close to body, polished concrete floor, "
                 "soft LED lights, other cars blurred far away",
        "light": "soft ambient garage lighting, even illumination, no harsh shadows"
    },
    {
        "scene": "standing with body very close to a black Lamborghini Urus, "
                 "almost touching the car, only part of hood visible in frame, "
                 "modern business street behind, clean granite pavement",
        "light": "soft natural daylight, balanced light"
    },
    {
        "scene": "leaning against a dark glass building facade, "
                 "body pressed close to glass, contemporary architecture right behind",
        "light": "soft diffused daylight, gentle reflections from glass"
    },
    {
        "scene": "standing body-close to a black Mercedes-AMG GT, "
                 "car door very near, only small part of car visible, "
                 "marble columns and modern entrance barely visible",
        "light": "soft natural daylight, balanced illumination"
    },
    {
        "scene": "leaning close against modern glass railing, "
                 "railing tight against body, city view far behind",
        "light": "soft golden hour light, warm natural glow"
    },
    {
        "scene": "standing body-close to a black Audi A8 parked on quiet street, "
                 "almost touching car door, only part of door and fender in frame, "
                 "elegant house facade and plants blurred behind",
        "light": "soft natural daylight, even light across subject and car surface"
    },
    {
        "scene": "leaning tight against dark stone wall in modern residential courtyard, "
                 "wall close behind, body pressed against it, "
                 "minimalist architecture partially visible",
        "light": "soft natural daylight, clean even light"
    },
    {
        "scene": "standing very close to black granite entrance of modern business center, "
                 "body near glass door, only part of door and handles visible, "
                 "interior barely seen through glass",
        "light": "soft diffused daylight, gentle reflections from granite and glass"
    },
    {
        "scene": "leaning tight against a black luxury SUV in private garage, "
                 "body very close to car surface, only part of SUV in frame, "
                 "epoxy floor close beneath feet, soft ambient lighting",
        "light": "soft indirect LED lighting, subtle highlights on car and fabric"
    },
    {
        "scene": "standing on rooftop parking right next to a parked car, "
                 "body very close to vehicle, only small portion visible, "
                 "concrete and white parking lines at feet, open sky above",
        "light": "soft natural daylight, even overcast lighting"
    }
]

# ---------------- BACK SCENES ----------------

BACK_SCENES = [
    {
        "scene": "walking through underground parking garage, "
                 "person small in frame, rows of car tails far in background, "
                 "polished floor stretches ahead, LED lights above",
        "light": "soft ambient LED lighting, even illumination"
    },
    {
        "scene": "standing in courtyard of modern apartment complex, "
                 "person small in frame, contemporary architecture surrounds, "
                 "geometric landscaping visible, far away view",
        "light": "soft natural daylight, balanced light across courtyard"
    },
    {
        "scene": "walking on wide plaza in front of business center, "
                 "person small in frame, glass towers far ahead, "
                 "granite pavement stretches, modern furniture scattered",
        "light": "soft diffused daylight, clean modern light"
    },
    {
        "scene": "standing on elevated driveway of hotel entrance, "
                 "person small in frame, valet parking zone stretches ahead, "
                 "hotel facade visible in distance",
        "light": "soft natural daylight with warm hotel lighting"
    },
    {
        "scene": "walking up wide modern stone staircase, "
                 "person small climbing, clean steps ahead, steel railings on sides, "
                 "store windows visible far above, shoppers tiny in distance",
        "light": "soft even daylight, reflections from storefronts"
    },
    {
        "scene": "standing on wide pedestrian street in city center, "
                 "person small in frame, modern office buildings far ahead, "
                 "shops visible in distance, cars parked along street sides",
        "light": "soft overcast daylight, even light across entire street"
    },
    {
        "scene": "walking through private driveway of gated community, "
                 "person small in frame, manicured gardens on sides, "
                 "modern minimalist houses visible in distance, premium pavement",
        "light": "soft natural daylight, clean even illumination"
    },
    {
        "scene": "standing in courtyard of modern office campus, "
                 "person small in frame, glass buildings far ahead, "
                 "water feature visible, professionals walking in far distance",
        "light": "soft diffused daylight, balanced campus lighting"
    }
]

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "leaning naturally, right fingertips resting lightly on the hood fabric near the temple, "
    "left hand resting loosely on upper thigh",

    "leaning naturally, both hands resting lightly on both sides of the hood from the front, "
    "chin slightly down, elbows relaxed",

    "leaning naturally, left fingertips resting lightly on the hood fabric near the cheek, "
    "right arm relaxed along outer thigh",

    "leaning naturally, both hands resting lightly near the hood opening without pulling the fabric, "
    "shoulders relaxed",

    "leaning naturally, right hand resting lightly on the hood fabric near the temple, "
    "left hand resting flat on upper thigh",

    "leaning naturally, right hand resting on the back of the head, "
    "left arm relaxed along outer thigh",

    "leaning naturally, left hand resting on the back of the head, "
    "right arm relaxed along outer thigh",

    "leaning naturally, right hand resting on the back of the head, "
    "left hand resting on upper thigh, chin slightly down"
]

BACK_POSES = [
    "standing facing away, right hand resting lightly on the back of the hood, "
    "left arm relaxed along outer thigh",

    "standing facing away, left hand resting lightly on the back of the hood, "
    "right arm relaxed along outer thigh",

    "standing facing away, both hands resting lightly on the hood from behind, "
    "elbows slightly outward",

    "walking away, right hand resting lightly on the back of the hood, "
    "left arm moving naturally with stride",

    "walking away, left hand resting lightly on the back of the hood, "
    "right arm moving naturally with stride",

    "walking away, both hands lightly touching the hood from behind, head slightly lowered",

    "standing facing away, right hand resting on the back of the head above the neck, "
    "left arm relaxed along outer thigh",

    "standing facing away, left hand resting on the back of the head above the neck, "
    "right arm relaxed along outer thigh",

    "walking away, right hand resting on the back of the head above the neck, "
    "left arm moving naturally with stride",

    "walking away, left hand resting on the back of the head above the neck, "
    "right arm moving naturally with stride"
]


# ---------------- SPEC ----------------

def get_unique_specs():
    specs = []
    used_scenes = set()
    used_poses = set()
    sides = ["back", "front", "back"]

    for side in sides:
        if side == "front":
            scenes = FRONT_SCENES
            poses = FRONT_POSES
            ref = REF_FRONT
        else:
            scenes = BACK_SCENES
            poses = BACK_POSES
            ref = REF_BACK

        available_scenes = [s for s in scenes if s["scene"][:50] not in used_scenes]
        if not available_scenes:
            available_scenes = scenes
        scene_data = random.choice(available_scenes)
        used_scenes.add(scene_data["scene"][:50])

        available_poses = [p for p in poses if p not in used_poses]
        if not available_poses:
            available_poses = poses
        pose = random.choice(available_poses)
        used_poses.add(pose)

        specs.append({
            "side": side,
            "scene": scene_data["scene"],
            "light": scene_data["light"],
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": ref
        })

    return specs


# ---------------- FRONT PROMPT ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic 9:16 photograph. "
        "Professional fashion shot, front view. "
        "Sony A7R V, 35mm lens, f/4, ISO 200. "
        "Camera at eye level, 1.5 meters from subject. "
        "Framing from head to knees. Subject 70-75 percent of frame. "

        "Sharp focus throughout - subject and background equally sharp. "
        "No blur, no bokeh. One unified photograph. "

        "Subject leans or stands against environment naturally. "
        "Visible contact with surface: wall, car, or railing. "
        "Not floating. Part of the location. "

        "Premium black hoodie, no front pocket, no zipper. "
        "Chest logo sharp, exact from reference. "
        "Black wide-leg denim, heavy texture visible. "

        "Hands active, visible in frame, not in pockets. "
        "If touching hood: fingers visible on fabric. "

        "Background sharp and detailed. Not blurred. "
        "Architecture, pavement, car details all clear. "

        f"Lighting: {spec['light']}. "
        "Soft natural light, no harsh shadows, no flash. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


# ---------------- BACK PROMPT ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic 9:16 photograph. "
        "Environmental back view shot. "
        "Sony A7R V, 35mm, f/4, ISO 400. "
        "Camera at 1.6m height, straight forward. "

        "Camera 25-30 meters from subject. "
        "Full body visible, feet on ground. "
        "Ground visible 30 percent of frame below feet. "
        "Subject 8-12 percent of frame height - small but clear. "
        "Environment dominates, subject is focal point. "

        "Sharp focus everywhere - foreground, subject, background all sharp. "
        "No blur, no bokeh. Unified photograph. "

        "Subject stands or walks naturally in location. "
        "Authentically part of the scene, not floating. "

        "Black hoodie, hood up, face hidden, back view only. "
        "Hands light contact on hood or back of head above neck. "
        "Black wide-leg denim, wide silhouette visible from distance. "

        "Background sharp and detailed - buildings, pavement, "
        "architecture all clear and visible. "

        f"Lighting: {spec['light']}. "
        "Soft natural light, even across entire scene, no harsh shadows. "

        "Only pedestrian zones - streets, plazas, stairs, promenades. "
        "Never on traffic lanes. "

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

    try:
        data = response.json()
    except Exception:
        raise Exception(f"Polza вернула не JSON: {response.text}")

    logger.info(f"[POLZA] submit: {data}")

    job_id = data.get("id") or data.get("task_id")
    if not job_id:
        raise Exception(f"Polza submit error: {data}")

    return job_id


def extract_url(obj, depth=0):
    if depth > 10:
        return None

    if isinstance(obj, str):
        if obj.startswith("http") and "ibb.co" not in obj:
            return obj
        return None

    if isinstance(obj, list):
        for item in obj:
            found = extract_url(item, depth + 1)
            if found:
                return found

    if isinstance(obj, dict):
        priority_keys = ["output", "result", "url", "image", "images", "file", "src", "data"]
        for key in priority_keys:
            if key in obj:
                found = extract_url(obj[key], depth + 1)
                if found:
                    return found
        for value in obj.values():
            found = extract_url(value, depth + 1)
            if found:
                return found

    return None


async def poll_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")
    max_wait = 900
    interval = 5
    waited = 0
    last_data = None

    while waited < max_wait:
        await asyncio.sleep(interval)
        waited += interval

        try:
            response = await asyncio.to_thread(
                requests.get,
                f"https://polza.ai/api/v1/media/{job_id}",
                headers={"Authorization": f"Bearer {polza_key}"},
                timeout=30
            )

            try:
                data = response.json()
            except Exception:
                logger.warning(f"[POLZA] non-JSON: {response.text[:300]}")
                continue

            last_data = data
            status = str(data.get("status", "")).lower()

            logger.info(
                f"[POLZA] job={job_id} waited={waited}s status={status} keys={list(data.keys())}"
            )

            if status in {"failed", "error", "canceled", "cancelled"}:
                raise Exception(f"Polza job failed: {data}")

            url = extract_url(data)
            if url:
                logger.info(f"[POLZA] url: {url}")
                return url

        except Exception as e:
            if "failed" in str(e).lower():
                raise
            logger.warning(f"[POLZA] poll error job={job_id}: {e}")

    raise Exception(f"Timeout {max_wait}s. Last: {last_data}")


async def download_image(url, path):
    response = await asyncio.to_thread(requests.get, url, timeout=60)
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(response.content)


# ---------------- GENERATION ----------------

async def generate_all_photos():
    specs = get_unique_specs()
    job_ids = []

    for i, spec in enumerate(specs):
        prompt = build_front_prompt(spec) if spec["side"] == "front" else build_back_prompt(spec)
        job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
        job_ids.append(job_id)
        if i < len(specs) - 1:
            await asyncio.sleep(3)

    urls = await asyncio.gather(*[poll_job(job_id) for job_id in job_ids])

    paths = []
    for index, url in enumerate(urls):
        path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_{index}.png")
        await download_image(url, path)
        paths.append(path)

    return paths, specs, list(urls)


async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    old_scene = current_specs[index].get("scene", "")[:50]
    old_pose = current_specs[index].get("pose", "")

    if side == "front":
        scenes = FRONT_SCENES
        poses = FRONT_POSES
        ref = REF_FRONT
    else:
        scenes = BACK_SCENES
        poses = BACK_POSES
        ref = REF_BACK

    available_scenes = [s for s in scenes if s["scene"][:50] != old_scene]
    if not available_scenes:
        available_scenes = scenes
    scene_data = random.choice(available_scenes)

    available_poses = [p for p in poses if p != old_pose]
    if not available_poses:
        available_poses = poses
    pose = random.choice(available_poses)

    spec = {
        "side": side,
        "scene": scene_data["scene"],
        "light": scene_data["light"],
        "pose": pose,
        "seed": random.randint(100000, 999999),
        "ref": ref
    }

    prompt = build_front_prompt(spec) if side == "front" else build_back_prompt(spec)
    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_regen.png")
    await download_image(url, path)

    return path, spec, url
