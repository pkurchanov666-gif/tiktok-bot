import os
import time
import random
import requests
import asyncio

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# ---------------- ФОНЫ СПЕРЕДИ ----------------

FRONT_SCENES = [
    {
        "scene": "standing beside a wide light-grey concrete pillar in a clean modern parking structure, "
                 "smooth concrete floor, minimal architecture around, calm empty space",
        "light": "cool even overhead light falling from above, "
                 "soft shadow to one side of the pillar, "
                 "light hitting hoodie fabric at slight angle revealing full texture"
    },
    {
        "scene": "standing close to a tall glass wall of a modern office building, "
                 "soft reflections in the glass, steel frame visible, "
                 "clean pavement underfoot",
        "light": "soft natural daylight reflected from glass surface, "
                 "gentle side fill from open sky, "
                 "even realistic light showing every fiber of the hoodie cotton"
    },
    {
        "scene": "standing at the entrance ramp of a clean underground parking garage, "
                 "smooth concrete walls on both sides, overhead lights above, "
                 "architectural lines leading inward behind",
        "light": "cool overhead parking light from directly above, "
                 "soft bounce from concrete walls, "
                 "clean downward light revealing hoodie weave and stitching detail"
    },
    {
        "scene": "standing beside a modern glass and metal elevator portal in a clean building area, "
                 "brushed steel frame, glass panels, smooth stone floor",
        "light": "soft even interior ambient light from above, "
                 "subtle reflection from polished floor and metal surfaces, "
                 "balanced light showing extreme fabric texture detail"
    },
    {
        "scene": "standing close to a smooth dark grey stone wall in a modern urban setting, "
                 "clean surface with subtle stone texture, no distractions, calm minimal background",
        "light": "soft natural side light from open sky on the left, "
                 "gentle shadow on the wall behind, "
                 "light raking across hoodie surface showing every cotton fiber"
    },
    {
        "scene": "standing beside clean metal railings of a modern pedestrian bridge, "
                 "concrete and steel railing close to body, bridge surface underfoot",
        "light": "soft overcast daylight from above, "
                 "no harsh shadows, even diffused illumination, "
                 "perfect light for maximum fabric texture visibility"
    },
    {
        "scene": "standing in a clean corner of a modern parking garage, "
                 "concrete pillar on one side, smooth wall on the other, "
                 "overhead light, clean floor, calm empty space",
        "light": "cool overhead parking light falling straight down, "
                 "soft shadow in the corner behind, "
                 "sharp overhead light catching every weave and fold of the hoodie"
    },
    {
        "scene": "standing beside a matte black Lamborghini Urus parked on a clean quiet street, "
                 "only part of the front fender, headlight and door visible close to the subject, "
                 "car is secondary object in the composition",
        "light": "soft natural daylight from the side, "
                 "subtle reflection from the matte car surface, "
                 "even realistic light revealing full hoodie texture and sharp logo"
    },
    {
        "scene": "standing beside the open driver door of a matte black Lamborghini Urus, "
                 "dark premium interior softly visible inside the car, "
                 "only the door and part of the car body visible close to the subject, "
                 "car remains natural and secondary in the frame",
        "light": "soft ambient daylight from above and side, "
                 "subtle warm tone from car interior, "
                 "natural balanced light showing fabric detail and clear readable logo"
    },
    {
        "scene": "standing beside a smooth concrete wall in a modern open pedestrian passage, "
                 "clean concrete surface close to the body, overhead architectural ceiling, "
                 "calm minimal urban space around",
        "light": "soft even light from above through the passage opening, "
                 "gentle ambient bounce from concrete surfaces, "
                 "diffused realistic light perfect for showing cotton texture in extreme detail"
    }
]

# ---------------- ФОНЫ СЗАДИ ----------------

BACK_SCENES = [
    {
        "scene": "standing far away on a wide empty parking lot near a business center, "
                 "clean asphalt with parking lines stretching far in all directions, "
                 "overcast grey sky, person is tiny figure in vast empty space",
        "light": "soft overcast daylight from grey sky above, "
                 "no harsh shadows, even diffused light across entire wide scene"
    },
    {
        "scene": "standing far away on a wide clean sidewalk along a long dark concrete wall, "
                 "morning sun casting long shadow on pavement, "
                 "person small in long straight perspective",
        "light": "natural morning side sunlight from the right, "
                 "long realistic shadow to the left, "
                 "clean directional light across entire scene"
    },
    {
        "scene": "standing far away in a massive clean underground parking garage, "
                 "concrete pillars creating deep perspective far ahead, "
                 "overhead lights stretching into distance, "
                 "person small deep in wide corridor",
        "light": "cool overhead fluorescent lights even across entire garage, "
                 "soft bounce from concrete floor and walls, "
                 "clean consistent light far into distance"
    },
    {
        "scene": "standing far away on an empty modern pedestrian bridge, "
                 "clean railings on both sides, overcast sky, "
                 "bridge stretching far ahead, person small on the wide bridge",
        "light": "soft overcast diffused daylight from above, "
                 "no harsh shadows, even light across entire bridge surface"
    },
    {
        "scene": "standing far away on a wide empty street in a financial district, "
                 "glass and concrete office buildings far on both sides, "
                 "clean pavement, no people, no cars, evening light, "
                 "person tiny in wide quiet street",
        "light": "warm late afternoon side light from the right, "
                 "soft long shadows on pavement, "
                 "natural realistic evening light across entire scene"
    },
    {
        "scene": "standing far away in a wide clean courtyard between modern office buildings, "
                 "buildings on both sides, open sky above, "
                 "wide stone pavement all around, "
                 "person small in the middle of open space",
        "light": "soft natural daylight from open sky above, "
                 "gentle ambient bounce from building facades, "
                 "even clean realistic light"
    },
    {
        "scene": "standing far away on a long straight clean empty city road at early morning, "
                 "empty road stretching very far ahead, "
                 "buildings far on both sides, cold morning atmosphere, "
                 "person tiny far down the long road",
        "light": "cool early morning ambient light from grey sky, "
                 "soft cold tones, no harsh shadows, "
                 "even diffused realistic light across full scene"
    },
    {
        "scene": "standing far away on an open rooftop parking level, "
                 "clean concrete floor, low barriers at edges, "
                 "grey city visible on horizon, overcast sky, "
                 "person small on wide open rooftop",
        "light": "soft overcast daylight from grey sky above, "
                 "even diffused light, no harsh shadows, "
                 "consistent realistic light across entire rooftop"
    },
    {
        "scene": "standing far away at the end of a wide modern covered walkway, "
                 "concrete ceiling above, pillars on sides, "
                 "walkway stretching far ahead, person small at the far end",
        "light": "soft overhead light filtering through walkway opening, "
                 "gentle bounce from concrete surfaces, "
                 "even realistic light down entire walkway length"
    }
]

# ---------------- ПОЗЫ БЕЗ СКУКИ ----------------

FRONT_POSES = [
    "right hand gripping hood edge near temple pulling it tighter, left hand in jeans pocket",
    "both hands adjusting hood from front pulling it forward over forehead",
    "right hand pulling hood down low, left hand gripping hoodie hem at the side",
    "right hand on hood near temple, left hand touching chest logo area lightly",
    "left hand pulling hood edge forward, right hand hooked into jeans pocket",
    "both hands holding both hood edges near the jawline, chin slightly down"
]

BACK_POSES = [
    "standing facing away, right hand holding the back edge of the hood, left hand in jeans pocket",
    "walking away, right hand pulling the hood slightly backward, left hand in jeans pocket",
    "standing facing away, both hands adjusting the hood from behind",
    "walking away slowly, left hand holding the back of the hood, right hand in jeans pocket",
    "standing facing away, right hand on hood, left hand touching the side seam of the jeans",
    "walking away, right hand gripping the hood edge, left hand touching waistband",
    "standing facing away, left hand holding the hood from behind, right hand hooked in pocket",
    "walking away slowly, both hands briefly adjusting the hood from behind"
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
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX

    used = set()
    specs = []
    sides = ["back", "front", "back"]

    for side in sides:
        chosen = None

        for _ in range(30):
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

            key = scene_data["scene"][:40]
            if key not in used:
                used.add(key)
                chosen = {
                    "side": side,
                    "scene": scene_data["scene"],
                    "light": scene_data["light"],
                    "pose": pose,
                    "seed": random.randint(100000, 999999),
                    "ref": ref
                }
                break

        if chosen is None:
            chosen = {
                "side": side,
                "scene": scene_data["scene"],
                "light": scene_data["light"],
                "pose": pose,
                "seed": random.randint(100000, 999999),
                "ref": ref
            }

        specs.append(chosen)

    return specs


# ---------------- ПРОМПТ СПЕРЕДИ ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Real photo by a professional photographer on location. "
        "Sony A7R V, 35mm, f/8, ISO 200. "
        "Eye level. Straight-on. No tilt. No angle. "
        "Camera 1.0 meter from subject. "
        "Framing head to knees exactly. Subject fills 80-85 percent of frame. "

        "EXTREME MACRO-LEVEL FABRIC DETAIL. "
        "Every single cotton fiber of the hoodie is visible and sharp. "
        "Every weave pattern, stitch line, micro wrinkle rendered in extreme clarity. "
        "Light interacts physically with fabric: "
        "micro shadows in every fold, highlights on raised fibers, natural cotton sheen. "
        "Fabric looks real and tactile. Not plastic. Not smooth. Not flat. "
        "Denim jeans also extreme detail — every denim thread visible. "

        "Deep depth of field. f/8. Everything sharp. No bokeh. No blur. "
        "Background sharp and real. Subject and background are one unified photo. "
        "Not cut out. Not composited. Not isolated. "

        f"Lighting: {spec['light']}. "
        "Physically accurate. Same source lights subject and environment. "
        "Shadows match scene perfectly. Light wraps naturally around figure and fabric. "
        "No flash. No studio light. No artificial light. "

        "ABSOLUTE STRICT HOODIE RULES: "
        "NO KANGAROO POCKET. NO FRONT POUCH OF ANY KIND. NO ZIPPER. NO DRAWSTRINGS. "
        "Clean flat front with nothing except the chest logo. "
        "If reference has no pocket — final image must have no pocket. "
        "Logo rendered with MAXIMUM sharpness and detail. "
        "Exact size, position, font, design from reference. "
        "Logo is crisp, clear, fully readable. Not blurred. Not distorted. Not resized. "

        "MANDATORY: extremely wide-leg baggy black denim jeans. "
        "Very wide silhouette at thighs, knees, calves equally. "
        "Heavy denim with visible texture and natural folds. "
        "Not slim. Not skinny. Not tapered. Not regular fit. "
        "Clearly and unmistakably baggy wide-leg jeans. "

        "No passive pose. Both hands must be actively engaged. "
        "Do not let both arms hang freely at sides. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


# ---------------- ПРОМПТ СЗАДИ ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Real photo by a photographer standing on location. "
        "Sony A7R V, 35mm, f/8, ISO 400. "
        "Camera at 1.6m height. Pointed straight forward. Parallel to ground. "
        "STRICT: no high angle. No top-down. No aerial. No drone. No elevated. No tilt. "

        "Camera 20 to 25 meters from subject. Very far away. "
        "Full body head to feet visible. Feet flat on ground. "
        "Ground below feet visible — at least 20 percent of frame is ground below feet. "
        "Do NOT crop at ankles. Do NOT crop at shins. Do NOT crop at knees. "
        "Subject occupies only 10-15 percent of vertical frame height. "
        "Tiny but clearly readable person in vast environment. "
        "Environment dominates the entire photo. "

        "EVERYTHING IN FOCUS. Deep depth of field f/8. "
        "No bokeh. No blur anywhere. No shallow depth of field. "
        "Foreground sharp. Subject sharp. Background sharp. Everything sharp. "
        "Background is a real location — fully detailed and rendered. "

        f"Lighting: {spec['light']}. "
        "Physically accurate across entire image. "
        "Same light source on subject and environment. "
        "Shadows match perfectly. No flash. No artificial light. "

        "MANDATORY: extremely wide-leg baggy black denim jeans. "
        "Wide silhouette clearly visible even from 20 meters distance. "
        "Wide at thighs, knees and calves. Heavy denim. "
        "Not slim. Not skinny. Not tapered. Clearly baggy. "

        "Black hoodie. No pocket. Hood up. Face completely hidden. "
        "Entire body seen from behind. No face visible at any angle. "

        "No passive pose. Do not let both arms hang freely down at sides. "
        "At least one hand must interact with the hood or be in jeans pocket. "

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
    max_wait = 600
    interval = 5
    waited = 0

    while waited < max_wait:
        await asyncio.sleep(interval)
        waited += interval

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
