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
        "scene": "standing on a clean open-air parking level with dark asphalt and white parking lines, "
                 "wide empty space around, low barriers in the distance, calm realistic setting",
        "light": "soft overcast daylight, natural even illumination, no harsh shadows"
    },
    {
        "scene": "standing beside a matte black Lamborghini Urus parked naturally, "
                 "only part of the front fender, wheel arch and door visible close to the subject, "
                 "car remains secondary in the composition",
        "light": "soft natural daylight, subtle reflection from matte car body, even realistic light"
    },
    {
        "scene": "standing beside the open driver door of a matte black Lamborghini Urus, "
                 "dark car interior softly visible, only the door and part of the body close to the subject",
        "light": "soft ambient daylight, subtle interior shadow, balanced natural illumination"
    },
    {
        "scene": "standing beside clean metal railings of a modern pedestrian bridge walkway, "
                 "open sky around, smooth bridge surface underfoot, simple minimal surroundings",
        "light": "soft diffused daylight, no harsh contrast, natural even light"
    },
    {
        "scene": "standing beside a smooth dark matte wall in a quiet modern urban setting, "
                 "clean surface, minimal surroundings, calm aesthetic atmosphere",
        "light": "soft diffused natural light, smooth even illumination across wall and subject"
    },
    {
        "scene": "standing beside a dark car body parked in a quiet open parking area, "
                 "subtle reflections on the paint, wide empty asphalt around, realistic minimal setting",
        "light": "soft daylight with gentle reflections from the car surface, natural balanced light"
    },
    {
        "scene": "standing near the side railing of a quiet riverside pedestrian walkway, "
                 "metal railing beside the body, open air, calm water in the distance, minimal surroundings",
        "light": "soft diffused daylight, clean natural light, no harsh shadows"
    },
    {
        "scene": "standing beside a smooth dark stone wall near an open parking area, "
                 "clean surface with subtle texture, dark asphalt underfoot, minimal background",
        "light": "soft natural diffused light, even illumination with gentle shadow transition"
    }
]

# ---------------- BACK SCENES ----------------

BACK_SCENES = [
    {
        "scene": "standing far away on a wide empty open-air parking lot, "
                 "clean dark asphalt stretching far in all directions, person tiny in open space",
        "light": "soft natural overcast daylight, no harsh shadows, even realistic light"
    },
    {
        "scene": "standing far away on an open rooftop parking level, "
                 "dark asphalt surface, low barriers, wide empty space around, person small in frame",
        "light": "soft natural daylight, calm even illumination across entire scene"
    },
    {
        "scene": "standing far away on an empty modern pedestrian bridge walkway, "
                 "clean metal railings on both sides, open sky around, person small in wide frame",
        "light": "soft diffused daylight, no direct sun, no harsh shadows, natural even light"
    },
    {
        "scene": "standing far away in a clean open-air multi-level parking structure, "
                 "long open ramps, repeated horizontal lines, empty parking lanes, person small in deep perspective",
        "light": "soft neutral daylight, gentle reflections, even realistic illumination"
    },
    {
        "scene": "standing far away with back to camera beside a parked Ferrari in a clean open parking setting, "
                 "only part of the rear quarter, wheel and body of the car visible, "
                 "car remains secondary, person small in the frame",
        "light": "soft natural overcast daylight, no direct sun, gentle even illumination across subject, car and ground"
    },
    {
        "scene": "standing far away in a wide empty asphalt courtyard area, "
                 "minimal surroundings, large dark ground plane, person small in open space",
        "light": "soft diffused daylight, even realistic illumination"
    },
    {
        "scene": "standing far away in a wide covered walkway with simple columns and open sides, "
                 "long perspective depth, person small at the far end",
        "light": "soft overhead ambient light, gentle bounce from surrounding surfaces, no harsh contrast"
    },
    {
        "scene": "standing far away beside a long dark retaining wall in an open parking area, "
                 "wide asphalt surface, minimal surroundings, person small in a quiet realistic setting",
        "light": "soft overcast daylight, smooth even light across wall and ground, no direct sun"
    },
    {
        "scene": "walking upward on a wide clean staircase in an open urban setting, "
                 "seen fully from behind, strong lines, person small in frame, stairs rising upward calmly",
        "light": "soft diffused daylight, even realistic illumination across staircase, no harsh shadows"
    },
    {
        "scene": "standing far away on a quiet riverside pedestrian walkway, "
                 "metal railing along the side, open air and water in the distance, person small in a calm open setting",
        "light": "soft natural daylight, balanced even illumination, no direct harsh sun"
    }
]

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "right fingertips resting lightly on the hood fabric near the temple, left hand in front jeans pocket, weight on right leg",
    "both hands resting lightly on both sides of the hood from the front, chin slightly down, elbows relaxed",
    "left fingertips resting lightly on the hood fabric near the cheek, right hand in front jeans pocket, body turned slightly left",
    "both hands resting lightly near the hood opening without pulling the fabric, shoulders relaxed",
    "right hand resting lightly on the hood fabric near the temple, left hand resting flat on upper thigh, relaxed stance",
    "right hand resting behind the head on the nape, left hand in front jeans pocket, relaxed stance",
    "left hand resting behind the head on the nape, right hand in front jeans pocket, body turned slightly left",
    "right hand resting behind the head on the nape, left hand resting on upper thigh, chin slightly down"
]

BACK_POSES = [
    "standing facing away, right hand resting lightly on the back of the hood, left arm relaxed along outer thigh",
    "standing facing away, left hand resting lightly on the back of the hood, right arm relaxed along outer thigh",
    "standing facing away, both hands resting lightly on the hood from behind, elbows slightly outward",
    "walking away, right hand resting lightly on the back of the hood, left arm moving naturally with stride",
    "walking away, left hand resting lightly on the back of the hood, right arm moving naturally with stride",
    "walking away, both hands lightly touching the hood from behind, head slightly lowered",
    "standing facing away, right hand resting behind the head on the nape, left arm relaxed along outer thigh",
    "standing facing away, left hand resting behind the head on the nape, right arm relaxed along outer thigh",
    "walking away, right hand resting behind the head on the nape, left arm moving naturally with stride",
    "walking away, left hand resting behind the head on the nape, right arm moving naturally with stride"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


# ---------------- SPEC ----------------

def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX

    if side == "front":
        scene_data = random.choice(FRONT_SCENES)
        pose = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
        ref = REF_FRONT
    else:
        scene_data = random.choice(BACK_SCENES)
        pose = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
        ref = REF_BACK

    return {
        "side": side,
        "scene": scene_data["scene"],
        "light": scene_data["light"],
        "pose": pose,
        "seed": random.randint(100000, 999999),
        "ref": ref
    }


def get_unique_specs():
    return [
        get_next_spec("back"),
        get_next_spec("front"),
        get_next_spec("back")
    ]


# ---------------- FRONT PROMPT ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "STRICT FRONT VIEW CLOSE SHOT ONLY. "
        "This image is only for a front-facing close fashion shot. "
        "Never use back-view composition. Never use far-distance back-view scene logic. "
        "Never use wide rear-view environments such as distant bridge walkway, staircase ascent, "
        "large long-shot parking panorama, wide courtyard or any scene intended for a rear environmental shot. "

        "Real photo taken on location by a professional photographer. "
        "Sony A7R V, 35mm, f/8, ISO 200. "
        "Camera at eye level. Straight-on. No tilt. "
        "Camera exactly 1.0 meter from subject. "
        "Framing from head to knees. Subject fills 80-85 percent of frame. "
        "Subject is facing the camera. "

        "The hood may be worn up or may rest naturally behind the head. "
        "If a hand interacts with the hood, the fingers must visibly touch the fabric. "
        "If the hood is down, the hand must rest naturally on the nape or behind the head. "
        "No floating hand near the head. No hand touching air. "
        "Do not pull the hood. Do not stretch the hood. "
        "No visible fabric tension caused by the hand. "

        "EXTREME FABRIC DETAIL. Macro-level realism. "
        "Photograph the hoodie fabric almost like a macro fashion shot. "
        "Every cotton fiber visible and sharp. "
        "Every weave, stitch, micro wrinkle rendered with extreme clarity. "
        "Light physically interacts with fabric: micro shadows in folds, subtle highlights on raised fibers. "
        "Fabric is real and tactile. Not smooth. Not plastic. Not flat. "
        "Denim weave of the jeans also fully visible and sharp. "

        "Deep depth of field. Everything sharp. No bokeh. No blur. "
        "Background sharp and real. One unified photograph. "
        "Not cut out. Not composited. Not isolated. "

        f"Lighting: {spec['light']}. "
        "No direct sunlight. No harsh shadows. No strong contrast. "
        "Soft natural diffused light only. No flash. No studio light. "

        "ABSOLUTE STRICT HOODIE RULES: "
        "THE HOODIE HAS NO FRONT POCKET. "
        "NO KANGAROO POCKET. NO FRONT POUCH. NO POCKET OF ANY KIND ON THE FRONT. "
        "NO ZIPPER. NO DRAWSTRINGS. "
        "Completely flat clean front. Only the chest logo. "
        "Logo must be maximum sharpness, exact size and exact position from reference. "
        "Logo must be crisp and fully readable. Not blurred. Not distorted. "

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
        "Never use close-up wall portrait composition, close car-door portrait setup, "
        "close vehicle-side fashion shot, or any scene intended for a front-facing close image. "

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
        "They do not grip the edge. They do not pull the hood. They do not stretch the hood. "
        "The hood keeps its natural relaxed shape and position. "
        "No visible fabric tension caused by the hands. "

        "No passive pose. "
        "No hands in back pockets of jeans. "
        "Hands must rest lightly on the hood or rest behind the head on the nape only. "
        "If walking, one arm may move naturally with stride. "

        "Never place the subject on a car traffic lane or roadway. "
        "Use only pedestrian surfaces, parking surfaces, staircase, courtyard, covered walkway, "
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

    logger.info(f"[POLZA] submit response: {data}")

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
                logger.warning(f"[POLZA] non-JSON response: {response.text[:300]}")
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
            logger.warning(f"[POLZA] poll error for job {job_id}: {e}")

    raise Exception(f"Generation timeout after {max_wait}s. Last response: {last_data}")


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
    spec = get_next_spec(side)

    prompt = build_front_prompt(spec) if side == "front" else build_back_prompt(spec)
    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_regen.png")
    await download_image(url, path)

    return path, spec, url
