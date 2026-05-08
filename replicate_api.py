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
        "scene": "leaning against a matte black Porsche 911 parked in a premium underground garage, "
                 "polished epoxy floor with reflections, soft LED ceiling lights, "
                 "other luxury cars blurred in background, expensive modern parking",
        "light": "soft ambient LED garage lighting, even illumination across subject and environment, no harsh shadows"
    },
    {
        "scene": "standing very close beside a white Lamborghini Urus on a business district street, "
                 "modern glass office buildings nearby, clean granite pavement, premium valet zone",
        "light": "soft natural daylight, subtle reflections from car surface, balanced professional light"
    },
    {
        "scene": "leaning shoulder against a dark glass facade of a modern luxury apartment building, "
                 "contemporary architecture with steel and glass, minimalist design, "
                 "expensive lobby entrance nearby",
        "light": "soft diffused daylight, gentle reflections from glass, clean modern light across subject and facade"
    },
    {
        "scene": "standing beside a black Mercedes-AMG GT parked near a premium office building entrance, "
                 "glass doors with polished marble columns, modern corporate architecture",
        "light": "soft natural daylight, subtle reflections from building and car, balanced light"
    },
    {
        "scene": "leaning against the railing of a luxury apartment building rooftop terrace, "
                 "city skyline view in background, modern glass railing, premium setting",
        "light": "soft golden hour light, warm natural illumination, gentle city glow"
    },
    {
        "scene": "standing beside a black Audi A8 parked on a street in an elite residential neighborhood, "
                 "leaning lightly against the car door, elegant modern house facade behind, "
                 "manicured bushes and clean asphalt street, quiet premium atmosphere",
        "light": "soft natural daylight, even illumination across car, subject and street"
    },
    {
        "scene": "leaning against a dark stone wall in the courtyard of a modern luxury residential complex, "
                 "contemporary minimalist architecture, geometric landscaping, premium pavement",
        "light": "soft natural daylight, clean even light across stone wall, fabric and surroundings"
    },
    {
        "scene": "standing near the entrance of a premium business center or fitness club, "
                 "black granite facade, glass doors with steel handles, modern clean design",
        "light": "soft diffused daylight, gentle reflections from polished stone and glass"
    },
    {
        "scene": "leaning with one shoulder against a Rolls-Royce Cullinan in a private luxury garage, "
                 "matte black or dark blue premium SUV, spotless epoxy floor, ambient soft lighting",
        "light": "soft indirect LED lighting, subtle highlights on vehicle and subject, premium garage illumination"
    },
    {
        "scene": "standing on a clean parking rooftop of a modern business center, "
                 "white parking lines on concrete, McLaren 720S or Ferrari F8 parked nearby, "
                 "clean urban environment, open sky above",
        "light": "soft natural daylight, slight overcast for even lighting across entire rooftop"
    }
]

# ---------------- BACK SCENES ----------------

BACK_SCENES = [
    {
        "scene": "walking away through an underground parking garage of a luxury residential complex, "
                 "rows of premium cars on both sides, polished floor, LED ceiling lights, "
                 "person small in frame, expensive parking atmosphere",
        "light": "soft ambient LED garage lighting, even illumination across parking level and subject"
    },
    {
        "scene": "standing far away in the courtyard of a modern luxury apartment complex, "
                 "contemporary glass and steel architecture, geometric landscaping, "
                 "modern sculpture or fountain, premium paving, person small in elegant setting",
        "light": "soft natural daylight, balanced even light across entire courtyard and subject"
    },
    {
        "scene": "walking away on a wide plaza in front of a modern business center, "
                 "glass office towers, polished granite pavement, modern urban furniture, "
                 "expensive cars nearby, person small in corporate success environment",
        "light": "soft diffused daylight, clean modern city lighting, even illumination across plaza"
    },
    {
        "scene": "standing far away on the elevated driveway of a five-star hotel entrance, "
                 "valet parking zone with luxury cars, hotel facade with glass and stone, "
                 "elegant landscaping, person small in upscale hospitality setting",
        "light": "soft natural daylight with warm hotel entrance lighting, balanced illumination"
    },
    {
        "scene": "walking up a wide modern stone staircase in a premium shopping district, "
                 "clean steps, steel and glass railings, luxury brand store windows visible, "
                 "affluent shoppers in background, person small climbing stairs",
        "light": "soft even daylight, gentle reflections from storefronts, clean upscale retail light"
    },
    {
        "scene": "standing far away on a wide pedestrian shopping street in the city center, "
                 "modern office buildings and luxury shops in front, expensive cars parked on sides, "
                 "clean asphalt pavement, businesspeople walking in background, person small in frame",
        "light": "soft overcast daylight, even illumination across street, buildings and subject"
    },
    {
        "scene": "walking away through the private driveway of a gated residential community, "
                 "security booth far behind, manicured gardens, modern minimalist houses, "
                 "premium pavement, person small in exclusive neighborhood",
        "light": "soft natural daylight, clean even illumination, elite gated community atmosphere"
    },
    {
        "scene": "standing far away in a modern corporate campus courtyard, "
                 "glass office buildings, water feature or contemporary sculpture, clean walkways, "
                 "young professionals in background, person small in ambitious work environment",
        "light": "soft diffused daylight, balanced modern campus lighting across entire frame"
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


# ---------------- FRONT PROMPT (УЛУЧШЕННЫЙ) ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 professional fashion photograph. "
        "FRONT FACING EDITORIAL SHOT. "
        "Sony A7R V, 35mm lens, f/5.6, ISO 200. "
        "Camera at eye level, 1.2 meters from subject. "
        "Framing from head to mid-thigh. Subject occupies 60-70 percent of frame. "
        "Subject centered and facing camera directly. "

        "CRITICAL - SHARP FOCUS THROUGHOUT: "
        "Everything in sharp focus. f/5.6 depth of field. "
        "Subject, immediate surroundings, and background ALL equally sharp and detailed. "
        "No blur. No bokeh. No selective focus. "
        "The photograph is ONE unified sharp image. "
        "Background is NOT soft - it is part of the scene and equally detailed. "

        "SUBJECT INTEGRATION: "
        "Subject must be physically integrated into the environment. "
        "Visible physical contact required: "
        "- If leaning on wall/pillar: shoulder and upper back clearly touching surface "
        "- If beside car: body very close, car door/fender clearly visible and sharp "
        "- If near railing: hand or body touching metal/glass, contact point sharp "
        "Subject is NOT floating. NOT composited. Authentically part of location. "

        "HOODIE AND CLOTHING: "
        "Photograph with professional fashion editorial clarity. "
        "Cotton fibers visible and sharp. Weave texture, stitching clearly defined. "
        "Light interacts realistically with fabric: micro-shadows in folds, "
        "subtle highlights on raised areas. Fabric feels tactile, premium, natural. "
        "NOT plastic. NOT smooth. Real premium cotton. "

        "HOODIE SPECIFICATIONS - MANDATORY: "
        "No front pocket. No kangaroo pouch. No zipper. Completely flat clean front. "
        "Only chest logo visible - maximum sharpness, exact size and position from reference. "
        "Logo crisp, clear, fully readable. Not blurred. Not distorted. "

        "JEANS - MANDATORY: "
        "Black wide-leg baggy denim. Very wide at thighs, knees, calves. "
        "Black denim texture fully visible. Heavy fabric, clear weave, realistic thickness. "
        "Not slim. Not skinny. Not tapered. "

        "BACKGROUND DETAIL - CRITICAL: "
        "Background is SHARP and DETAILED. Not soft. Not blurred. "
        "Every architectural element sharp: stone texture, car paint, glass reflections, "
        "pavement lines, building facades all clearly visible and detailed. "
        "Background colors rich and natural. Not washed out. Not faded. "
        "Lighting is consistent across subject and background. "

        "LIGHTING: "
        f"{spec['light']}. "
        "No direct sunlight. No harsh shadows. Soft diffused natural light. "
        "Light bathes both subject and surroundings evenly. "
        "No flash. No studio lights. Realistic outdoor/indoor natural lighting. "
        "Shadows are soft with gradual transitions. "

        "HANDS AND POSE: "
        "Hands must be actively engaged. Visible in frame. Not hanging at sides. "
        "If touching hood fabric: fingers clearly visible pressing/resting on fabric. "
        "If on head: hand clearly visible, fingers defined. "
        "No hands in pockets. "

        f"SCENE: {spec['scene']}. "
        f"POSE: {spec['pose']}. "

        "This is premium fashion editorial photography. "
        "Professional quality. Sharp. Detailed. Integrated. Realistic. "
        "Subject and environment equally sharp and real. "
    ) + uid


# ---------------- BACK PROMPT (УЛУЧШЕННЫЙ) ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 professional environmental photograph. "
        "BACK VIEW LONG SHOT. "
        "Sony A7R V, 35mm, f/5.6, ISO 400. "
        "Camera at 1.6m height, straight forward, parallel to ground. "
        "No high angle. No top-down. No drone. No tilt. "

        "COMPOSITION: "
        "Camera 18-22 meters from subject. "
        "Full body visible head to feet. Feet clearly on ground. "
        "At least 25 percent of frame is ground/pavement below feet. "
        "Subject is 12-18 percent of frame height. "
        "Person is clearly visible but small in large environmental scene. "
        "Environment dominates but subject is clear focal point. "

        "SHARP FOCUS - CRITICAL: "
        "Everything in sharp focus. f/5.6 depth of field. "
        "Foreground, subject, background ALL equally sharp and detailed. "
        "No blur. No bokeh. No selective focus. "
        "Every detail crisp: pavement texture, building facades, car details, "
        "architectural elements, landscaping - all sharp and detailed. "
        "This is ONE unified photograph. Not composite. Not layered. "

        "SUBJECT INTEGRATION: "
        "Subject authentically part of the environment. "
        "Not floating. Not cut out. Walking or standing naturally in location. "
        "If walking: natural stride, body position realistic for movement. "
        "If standing: weight distributed naturally on ground. "

        "HOODIE AND JEANS: "
        "Black hoodie, hood UP, face completely hidden. Seen from behind only. "
        "If hands touch hood: light contact only, no pulling, no tension. "
        "Hands rest naturally on fabric or back of head above neck. "
        "Black wide-leg baggy denim visible from distance. "
        "Wide silhouette clear. Denim texture visible even from distance. "
        "Not slim. Not tapered. Heavy black fabric. "

        "BACKGROUND DETAIL - CRITICAL: "
        "Background is SHARP and DETAILED. Not soft. Not blurred. "
        "Architectural elements: sharp building lines, texture details, clearly visible. "
        "Pavement/ground: texture visible, lines sharp, realistic surface. "
        "Vehicles parked nearby: details sharp, paint/finish clear. "
        "Urban furniture, landscaping, signage: all sharp and detailed. "
        "Colors natural and rich. Not washed out. "

        "LIGHTING: "
        f"{spec['light']}. "
        "No direct harsh sunlight. No heavy shadows. Soft diffused light. "
        "Light falls evenly across entire frame: subject, ground, buildings equally lit. "
        "Shadows are soft with gradual transitions. "
        "No flash. No studio setup. Natural outdoor/architectural lighting. "
        "Light is consistent and realistic. "

        "SCENE RULES: "
        "Only pedestrian zones: streets, plazas, parking lots, staircases, "
        "promenades, covered walkways, bridges. "
        "Never on car traffic lanes or dangerous areas. "
        "Scene must be accessible and realistic for a person to be in. "

        "HANDS AND POSE: "
        "Hands must be visible and active. "
        "If resting on hood: visible contact with fabric. "
        "If at back of head: clearly visible above neck, defined fingers. "
        "If walking: one arm may move naturally with stride. "

        f"SCENE: {spec['scene']}. "
        f"POSE: {spec['pose']}. "

        "This is premium environmental fashion photography. "
        "Sharp. Detailed. Integrated. Professional. Realistic. "
        "Subject and environment equally sharp and real. "
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
