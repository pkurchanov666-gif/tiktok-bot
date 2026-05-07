import os
import time
import random
import requests
import asyncio

SAVE_DIR = "generations"

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

FRONT_SCENES = [
    {
        "scene": "standing beside a wide light-grey concrete pillar in a clean modern parking structure, "
                 "smooth concrete floor, minimal architecture, calm empty space",
        "light": "soft cool overhead diffused light, no direct sun, no harsh shadows, "
                 "gentle even illumination across fabric"
    },
    {
        "scene": "standing close to a tall glass wall of a modern office building, "
                 "soft reflections in glass, steel frame visible, clean pavement underfoot",
        "light": "soft natural overcast daylight reflected from glass, "
                 "no direct sun, gentle even side light"
    },
    {
        "scene": "standing at the entrance of a clean underground parking garage, "
                 "smooth concrete walls, overhead lights, architectural lines behind",
        "light": "cool overhead parking light, soft bounce from concrete walls, "
                 "no harsh contrast, even downward illumination"
    },
    {
        "scene": "standing beside a modern glass and metal elevator portal, "
                 "brushed steel frame, glass panels, smooth stone floor",
        "light": "soft even interior ambient light from above, "
                 "subtle reflection from polished surfaces, no direct source"
    },
    {
        "scene": "standing close to a smooth dark grey stone wall, "
                 "clean surface, subtle texture, calm minimal background",
        "light": "soft overcast natural light from open sky, "
                 "no direct sun, gentle diffused illumination"
    },
    {
        "scene": "standing beside clean metal railings of a modern pedestrian bridge, "
                 "concrete and steel railing close to body, bridge surface underfoot",
        "light": "soft overcast daylight from above, "
                 "completely even diffused light, no sun, no shadows"
    },
    {
        "scene": "standing in a clean corner of a modern parking garage, "
                 "concrete pillar one side, smooth wall other side, clean floor",
        "light": "cool overhead parking light, soft ambient bounce, "
                 "no harsh contrast, consistent illumination"
    },
    {
        "scene": "standing beside a matte black Lamborghini Urus on a clean quiet street, "
                 "part of fender and door visible, car is secondary object",
        "light": "soft overcast daylight from above, no direct sun, "
                 "subtle matte reflection from car surface"
    },
    {
        "scene": "standing beside the open driver door of a matte black Lamborghini Urus, "
                 "dark interior softly visible, door and part of body close to subject",
        "light": "soft ambient overcast light from above, no direct sun, "
                 "subtle warm tone from car interior"
    },
    {
        "scene": "standing beside a smooth concrete wall in a modern pedestrian passage, "
                 "concrete surface close to body, overhead ceiling, calm minimal space",
        "light": "soft even diffused light through passage opening, "
                 "gentle bounce from concrete, no direct source"
    }
]

BACK_SCENES = [
    {
        "scene": "standing far away on a wide empty parking lot near a business center, "
                 "clean asphalt with lines stretching far, overcast sky, "
                 "person tiny in vast space",
        "light": "soft overcast daylight from above, no sun, no shadows, even diffused light"
    },
    {
        "scene": "standing far away on a wide sidewalk along a long concrete wall, "
                 "overcast morning, clean long perspective, person small",
        "light": "soft overcast morning light, no direct sun, gentle even illumination"
    },
    {
        "scene": "standing far away in a massive underground parking garage, "
                 "concrete pillars deep perspective, overhead lights, person small in corridor",
        "light": "cool overhead fluorescent lights, soft bounce from concrete, "
                 "no contrast, clean consistent light"
    },
    {
        "scene": "standing far away on an empty pedestrian bridge, "
                 "clean railings both sides, overcast sky, person small on wide bridge",
        "light": "soft overcast diffused daylight, no sun, no shadows, even light"
    },
    {
        "scene": "standing far away on a wide empty street in financial district, "
                 "glass and concrete buildings both sides, clean pavement, no people, "
                 "person tiny in quiet street",
        "light": "soft overcast evening light, no direct sun, gentle diffused illumination"
    },
    {
        "scene": "standing far away in a wide courtyard between modern office buildings, "
                 "buildings both sides, wide stone pavement, person small in open space",
        "light": "soft overcast daylight from open sky, gentle bounce from facades, "
                 "no sun, even clean light"
    },
    {
        "scene": "standing far away on a long straight empty city road at early morning, "
                 "road stretching very far, buildings far on sides, person tiny",
        "light": "cool early morning overcast light, no sun, soft cold tones, even diffused light"
    },
    {
        "scene": "standing far away on an open rooftop parking level, "
                 "clean concrete floor, low barriers, grey city on horizon, person small",
        "light": "soft overcast daylight from grey sky, no sun, no shadows, even diffused light"
    },
    {
        "scene": "standing far away at end of a wide modern covered walkway, "
                 "concrete ceiling, pillars on sides, walkway stretching far, person small",
        "light": "soft overhead light through walkway opening, gentle concrete bounce, even light"
    }
]

FRONT_POSES = [
    "right hand gripping hood edge near temple, left hand in front jeans pocket",
    "both hands adjusting hood pulling it forward over forehead",
    "right hand pulling hood down, left hand gripping hoodie hem at side",
    "left hand pulling hood edge forward, right hand in front jeans pocket",
    "both hands holding hood edges near jawline, chin slightly down",
    "right hand on hood near temple, left hand resting on thigh"
]

BACK_POSES = [
    "right hand holding back edge of hood, left hand in front jeans pocket",
    "walking away, right hand pulling hood backward, left hand in front jeans pocket",
    "both hands adjusting hood from behind",
    "walking away, left hand holding back of hood, right hand in front jeans pocket",
    "right hand gripping back of hood, left hand on hip",
    "walking away, right hand gripping hood edge from behind, left hand on hip",
    "left hand holding hood from behind, right hand on hip",
    "walking away slowly, both hands adjusting hood from behind"
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


# ---------------- ПРОМПТЫ ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Real photo taken on location by a professional photographer. "
        "Sony A7R V, 35mm, f/8, ISO 200. "
        "Camera at eye level. Straight-on. No tilt. "
        "Camera exactly 1.0 meter from subject. "
        "Framing from head to knees. Subject fills 80-85 percent of frame. "

        "EXTREME FABRIC DETAIL. Macro-level realism. "
        "Every cotton fiber of the hoodie visible and sharp. "
        "Every weave, stitch, micro wrinkle rendered with extreme clarity. "
        "Light physically interacts with fabric: "
        "micro shadows in folds, subtle highlights on raised fibers. "
        "Fabric is real and tactile. Not smooth. Not plastic. Not flat. "
        "Denim weave of jeans also fully visible and sharp. "

        "Deep depth of field. Everything sharp. No bokeh. No blur. "
        "Background sharp and real. One unified photograph. "

        f"Lighting: {spec['light']}. "
        "No direct sunlight. No harsh shadows. No strong contrast. "
        "Soft natural diffused light only. No flash. No studio light. "

        "HOODIE RULES — ABSOLUTE: "
        "ZERO POCKET ON FRONT. NO KANGAROO POCKET. NO POUCH. NO ZIPPER. NO DRAWSTRINGS. "
        "Completely flat clean front. Only chest logo. "
        "Logo: maximum sharpness, exact size and position from reference. "
        "Logo crisp and fully readable. Not blurred. Not distorted. "

        "MANDATORY baggy wide-leg black denim jeans. "
        "Very wide at thighs, knees, calves. Heavy denim texture visible. "
        "Not slim. Not skinny. Not tapered. "

        "Hands actively engaged. Not hanging freely at sides. No hands in back pockets. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Real photo taken on location. "
        "Sony A7R V, 35mm, f/8, ISO 400. "
        "Camera at 1.6m height. Straight forward. Parallel to ground. "
        "No high angle. No top-down. No drone. No tilt. "

        "Camera 20 to 25 meters from subject. "
        "Full body visible head to feet. Feet on ground. "
        "At least 20 percent of frame is ground below feet. "
        "Do not crop at ankles or shins. "
        "Subject is 10-15 percent of frame height. "
        "Person is small but readable in large environment. "

        "EVERYTHING IN FOCUS. f/8. No blur. No bokeh. "
        "Foreground, subject, background all sharp. "

        f"Lighting: {spec['light']}. "
        "No direct sunlight. No harsh shadows. Soft diffused light only. No flash. "

        "MANDATORY baggy wide-leg black denim jeans. "
        "Wide silhouette visible from 20 meters. "
        "Wide at thighs, knees, calves. Not slim. Not tapered. "

        "Black hoodie. No pocket. Hood up. Face hidden. Seen from behind. "

        "Hands not hanging freely. No hands in back pockets of jeans. "
        "Hands on hood or in front pockets only. "

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
