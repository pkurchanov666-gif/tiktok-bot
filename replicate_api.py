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
        "Ultra-realistic RAW 9:16 photograph. "
        "STRICT FRONT VIEW CLOSE SHOT ONLY. "
        "This image is only for a front-facing close fashion shot. "
        "Never use back-view composition. Never use far-distance back-view scene logic. "

        "Real photo taken on location by a professional photographer. "
        "Sony A7R V, 35mm lens, f/8, ISO 200. "
        "Camera at eye level. Straight-on. No tilt. "
        "Camera exactly 1.0 meter from subject. "
        "Framing from head to knees. Subject fills 80 to 85 percent of frame. "
        "Subject is facing the camera. "

        "The subject must physically interact with the environment object described in the scene. "
        "If the scene contains a wall, pillar or facade, the shoulder or upper back must visibly lean against it. "
        "If the scene contains a car, the body must stand naturally very close to the car door or fender. "
        "If the scene contains railings, the body must lean lightly against them. "
        "Visible physical contact with the environment is required. "
        "The subject must feel anchored in the scene, not floating, not cut out, not composited. "

        "The hood may be worn up or may rest naturally behind the head. "
        "If a hand interacts with the hood, the fingers must visibly touch the fabric. "
        "If the hood is down, the hand must rest naturally on the back of the head, not on the neck. "
        "No floating hand near the head. No hand touching air. "
        "Do not pull the hood. Do not stretch the hood. "
        "No visible fabric tension caused by the hand. "

        "EXTREME MACRO-LEVEL FABRIC DETAIL. "
        "Photograph the hoodie fabric like a macro fashion editorial shot. "
        "Every cotton fiber visible and sharp. "
        "Every weave, stitch, seam and micro wrinkle rendered with extreme clarity. "
        "Light physically interacts with the fabric surface: "
        "micro shadows in folds, subtle highlights on raised fibers, realistic cotton texture. "
        "The fabric must feel tactile, real, premium, natural. "
        "Not smooth. Not plastic. Not flat. "
        "Black denim jeans must also show realistic denim texture, visible weave, folds and thickness. "

        "Deep depth of field. Everything sharp. No bokeh. No blur. "
        "Background sharp and real. One unified photograph. "
        "The environment must look like a real photograph, not CGI, not a backdrop. "

        f"Lighting: {spec['light']}. "
        "No direct sunlight. No harsh shadows. No strong contrast. "
        "Soft natural diffused light only. "
        "Light must behave realistically across the surface the subject leans against, "
        "hoodie fabric and jeans. No flash. No studio light. "

        "ABSOLUTE STRICT HOODIE RULES: "
        "THE HOODIE HAS NO FRONT POCKET. "
        "NO KANGAROO POCKET. NO FRONT POUCH. NO POCKET OF ANY KIND ON THE FRONT. "
        "NO ZIPPER. NO DRAWSTRINGS. "
        "Completely flat clean front. Only the chest logo. "
        "Logo must be maximum sharpness, exact size and exact position from reference. "
        "Logo must be crisp, clear and fully readable. Not blurred. Not distorted. "

        "MANDATORY black wide-leg baggy denim jeans. "
        "The jeans must be black. "
        "Very wide at thighs, knees and calves. "
        "Heavy black denim texture visible. "
        "Not slim. Not skinny. Not tapered. "

        "Hands actively engaged. Not hanging freely at sides. "
        "No hands in back pockets. No hands in hoodie pocket. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


# ---------------- BACK PROMPT ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "STRICT BACK VIEW LONG SHOT ONLY. "
        "This image is only for a rear-view environmental shot. "
        "The subject is seen fully from behind. "
        "Never use close front-view scene logic. "
        "Never use close-up wall portrait, close car-door portrait, "
        "or any scene intended for a front-facing close image. "

        "Real photo taken on location. "
        "Sony A7R V, 35mm, f/8, ISO 400. "
        "Camera at 1.6m height. Straight forward. Parallel to ground. "
        "No high angle. No top-down. No drone. No tilt. "

        "Camera 20 to 25 meters from subject. "
        "Full body visible head to feet. Feet on ground. "
        "At least 20 percent of frame is ground below feet. "
        "Do not crop at ankles or shins. "
        "Subject is 10-15 percent of frame height. "
        "Person is small but clearly readable in a large environment. "
        "Environment dominates the frame. "

        "EVERYTHING IN FOCUS. f/8. No blur. No bokeh. "
        "Foreground, subject, background all sharp. "

        f"Lighting: {spec['light']}. "
        "No direct sunlight. No harsh shadows. Soft diffused light only. No flash. "

        "MANDATORY black wide-leg baggy denim jeans. "
        "The jeans must be black. "
        "Wide silhouette visible from long distance. "
        "Wide at thighs, knees and calves. "
        "Heavy black denim. Not slim. Not skinny. Not tapered. "

        "Black hoodie. No pocket. Hood up. Face hidden. Seen from behind only. "

        "If hands interact with the hood, they only rest lightly on the fabric surface. "
        "They do not grip the edge. They do not pull the hood. "
        "The hood keeps its natural relaxed shape. "
        "No visible fabric tension caused by the hands. "

        "No passive pose. "
        "No hands in back pockets of jeans. "
        "Hands must rest lightly on the hood or rest on the back of the head above the neck only. "
        "If walking, one arm may move naturally with stride. "

        "Never place the subject on a car traffic lane or roadway. "
        "Use only pedestrian surfaces, parking surfaces, staircase, promenade, covered walkway, "
        "or bridge walkway. "

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
