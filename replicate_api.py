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
        "scene": "leaning lightly with one shoulder against a clean dark pillar in an upscale underground parking garage, "
                 "polished concrete floor, premium parked cars softly visible deeper in the background, "
                 "quiet expensive atmosphere, realistic premium urban setting",
        "light": "soft overhead parking light, subtle reflections on the polished floor, "
                 "natural realistic illumination with no harsh shadows"
    },
    {
        "scene": "standing very close beside a matte black Lamborghini Urus parked naturally on a refined city street, "
                 "premium architecture around, clean pavement, expensive urban setting, car remains secondary",
        "light": "soft natural daylight, subtle reflections from the matte car surface, balanced realistic illumination"
    },
    {
        "scene": "standing close to a dark iron gate on a refined residential street, "
                 "elegant facades nearby, premium parked cars along the curb, "
                 "clean stone paving and calm upscale neighborhood atmosphere",
        "light": "soft natural daylight, balanced even illumination, realistic premium residential light"
    },
    {
        "scene": "leaning lightly with one shoulder against the railing of an elegant pedestrian bridge, "
                 "refined bridge design, calm city backdrop, premium urban atmosphere",
        "light": "soft diffused daylight, clean natural illumination, no harsh contrast"
    },
    {
        "scene": "standing near a quiet riverside promenade in an upscale district, "
                 "clean railing, elegant stone walkway, refined residential buildings nearby, calm premium atmosphere",
        "light": "soft natural daylight, balanced even light, realistic atmosphere"
    },
    {
        "scene": "leaning lightly against a clean stone column near the entrance of a refined urban block, "
                 "premium paving, elegant city architecture around, realistic upscale environment",
        "light": "soft natural daylight, even illumination across fabric and stone textures"
    },
    {
        "scene": "standing beside a dark premium coupe parked naturally in an elegant city quarter, "
                 "clean pavement, refined facades nearby, understated expensive atmosphere, car remains secondary",
        "light": "soft natural daylight, subtle reflection from the car body, realistic balanced illumination"
    },
    {
        "scene": "leaning lightly against a dark garage-style facade in an upscale townhouse quarter, "
                 "clean paving underfoot, elegant residential architecture nearby, "
                 "quiet expensive neighborhood atmosphere",
        "light": "soft diffused natural light, gentle shadow transition, realistic calm urban illumination"
    },
    {
        "scene": "standing near a refined stone staircase in an upscale urban quarter, "
                 "clean wide steps, elegant materials, premium residential surroundings, calm success aesthetic",
        "light": "soft natural daylight, even illumination across stone, fabric and face"
    },
    {
        "scene": "standing beside a low dark railing along a refined city promenade, "
                 "clean stone paving, elegant district around, subtle premium urban details, calm realistic atmosphere",
        "light": "soft natural daylight, balanced even illumination, no harsh shadows"
    }
]

# ---------------- BACK SCENES ----------------

BACK_SCENES = [
    {
        "scene": "standing far away on a refined street in an upscale city quarter, "
                 "elegant residential facades, premium parked cars along the street, clean pavement, person small in frame",
        "light": "soft natural daylight, balanced realistic illumination, no harsh shadows"
    },
    {
        "scene": "standing far away on an elegant pedestrian bridge, "
                 "refined bridge railings, calm premium city atmosphere, person small in a graceful architectural setting",
        "light": "soft diffused daylight, natural even light, realistic bridge atmosphere"
    },
    {
        "scene": "standing far away on a quiet riverside promenade in an upscale district, "
                 "clean railing, elegant stone walkway, premium buildings nearby, person small in frame",
        "light": "soft natural daylight, balanced even illumination, calm realistic atmosphere"
    },
    {
        "scene": "standing far away in a refined urban quarter with premium architecture and parked luxury cars, "
                 "clean pavement, elegant facades, person small in a realistic success-oriented setting",
        "light": "soft natural daylight, realistic even light, no harsh contrast"
    },
    {
        "scene": "standing far away beside a parked Ferrari in a refined city setting, "
                 "only part of the car visible, elegant architecture around, person small in frame, car remains secondary",
        "light": "soft natural daylight, gentle even illumination across subject, car and street"
    },
    {
        "scene": "walking upward on a wide elegant stone staircase in an upscale urban setting, "
                 "clean lines, premium materials, architectural depth, person small in frame",
        "light": "soft diffused daylight, even realistic illumination across staircase and subject"
    },
    {
        "scene": "standing far away in a covered walkway within a refined premium district, "
                 "clean columns, elegant materials, long perspective depth, person small in frame",
        "light": "soft ambient daylight, gentle bounce from surrounding surfaces, realistic upscale atmosphere"
    },
    {
        "scene": "standing far away near the entrance approach of a premium residential quarter, "
                 "elegant paving, parked premium vehicles, refined urban details, person small in frame",
        "light": "soft natural daylight, smooth even light, realistic premium neighborhood atmosphere"
    }
]

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "leaning naturally, right fingertips resting lightly on the hood fabric near the temple, "
    "left hand resting loosely on upper thigh",

    "leaning naturally, both hands resting lightly on both sides of the hood from the front, "
    "chin slightly down, elbows relaxed",

    "leaning naturally, left fingertips resting lightly on the hood fabric near the cheek, "
    "right hand resting loosely on upper thigh",

    "leaning naturally, both hands resting lightly near the hood opening without pulling the fabric, "
    "shoulders relaxed",

    "leaning naturally, right hand resting lightly on the hood fabric near the temple, "
    "left hand resting flat on upper thigh",

    "leaning naturally, right hand resting on the back of the head above the neck, "
    "left hand resting loosely on upper thigh",

    "leaning naturally, left hand resting on the back of the head above the neck, "
    "right hand resting loosely on upper thigh",

    "leaning naturally, right hand resting on the back of the head above the neck, "
    "left hand resting on upper thigh, chin slightly down"
]

BACK_POSES = [
    "standing facing away, right hand resting lightly on the back of the hood, "
    "left hand resting lightly on the back of the head above the neck",

    "standing facing away, left hand resting lightly on the back of the hood, "
    "right hand resting lightly on the back of the head above the neck",

    "standing facing away, both hands resting lightly on the hood from behind, "
    "elbows slightly outward",

    "standing facing away, both hands resting lightly on the back of the head above the neck",

    "walking away, right hand resting lightly on the back of the hood, "
    "left hand resting lightly on the back of the head above the neck",

    "walking away, left hand resting lightly on the back of the hood, "
    "right hand resting lightly on the back of the head above the neck",

    "walking away, both hands lightly touching the hood from behind, head slightly lowered",

    "walking away, both hands resting lightly on the back of the head above the neck"
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
        "Ultra-realistic RAW 9:16 photograph. "
        "STRICT FRONT VIEW CLOSE SHOT ONLY. "
        "Never use back-view composition. "

        "Real photo taken on location. "
        "Sony A7R V, 35mm, f/8, ISO 200. "
        "Eye level. Straight-on. No tilt. "
        "Camera 1.0 meter from subject. "
        "Head to knees framing. Subject fills 80-85 percent of frame. "
        "Subject facing camera. "

        "Subject must physically interact with the environment. "
        "If wall or pillar — shoulder or back must lean against it. "
        "If car — body must stand very close to door or fender. "
        "If railing — body must lean lightly against it. "
        "Visible physical contact with the environment required. "

        "Hood may be up or resting behind the head. "
        "If hand touches hood — fingers must visibly touch fabric. "
        "If hood is down — hand must rest on back of head above neck. "
        "No floating hand. No hand touching air. "
        "No pulling. No stretching hood. "

        "EXTREME MACRO FABRIC DETAIL. "
        "Every cotton fiber visible. Every weave and stitch sharp. "
        "Micro shadows in folds. Highlights on raised fibers. "
        "Fabric real and tactile. Not smooth. Not plastic. "
        "Black denim jeans texture also fully visible. "

        "Everything sharp. No bokeh. No blur. "
        "Background sharp and real. One unified photograph. "

        f"Lighting: {spec['light']}. "
        "No direct sun. No harsh shadows. Soft diffused light only. No flash. "

        "HOODIE: NO FRONT POCKET. NO KANGAROO POCKET. NO POUCH. NO ZIPPER. NO DRAWSTRINGS. "
        "Flat clean front. Only chest logo. "
        "Logo maximum sharpness. Exact from reference. Crisp and readable. "

        "Black wide-leg baggy denim jeans. Very wide at thighs knees calves. "
        "Not slim. Not skinny. Not tapered. "

        "Hands engaged. No hands hanging down. No hands in any pocket. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


# ---------------- BACK PROMPT ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "STRICT BACK VIEW LONG SHOT ONLY. Subject seen from behind. "
        "Never use close front-view scene logic. "

        "Real photo taken on location. "
        "Sony A7R V, 35mm, f/11, ISO 400. "
        "Camera 1.6m height. Straight forward. No high angle. No drone. "

        "Camera 20-25 meters from subject. "
        "Full body head to feet. Feet on ground. "
        "At least 20 percent of frame is ground below feet. "
        "Subject 10-15 percent of frame. "

        "CRITICAL: f/11 aperture. EVERYTHING sharp. "
        "Foreground sharp. Subject sharp. Background sharp. "
        "Zero blur. Zero bokeh. Zero depth falloff. "
        "Every detail from front to back perfectly sharp. "

        f"Lighting: {spec['light']}. "
        "No direct sun. No harsh shadows. No flash. "

        "Black wide-leg baggy jeans. Very wide silhouette. "
        "Not slim. Not skinny. Not tapered. "

        "Black hoodie. No pocket. Hood up. Face hidden. "

        "STRICT HAND RULES: "
        "Hands may ONLY rest lightly on the hood or on the back of the head above the neck. "
        "NEVER let hands hang down freely. "
        "NEVER put hands near any pocket. "
        "NEVER put hands on thighs or hips. "
        "NEVER let arms dangle at the sides. "
        "Both hands must be visibly placed on the hood or on the back of the head. "
        "No pulling hood. No stretching hood. "

        "Subject on pedestrian surface only. No roadway. "

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
        raise Exception(f"Polza non-JSON: {response.text}")

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
        priority_keys = ["output", "result", "url", "image", "images", "file", "src", "data", "media"]
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
    max_wait = 1200
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
                logger.info(f"[POLZA] got url: {url}")
                return url

        except Exception as e:
            if "failed" in str(e).lower():
                raise
            logger.warning(f"[POLZA] poll error job={job_id}: {e}")

    raise Exception(f"Timeout {max_wait}s. Last: {last_data}")


async def download_image(url, path):
    response = await asyncio.to_thread(
        requests.get,
        url,
        timeout=120,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    if response.status_code >= 400:
        raise Exception(f"Download error {response.status_code}: {url}")

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
