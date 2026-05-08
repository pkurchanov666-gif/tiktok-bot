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
        "scene": "standing beside a wide concrete pillar in a clean underground parking garage, "
                 "smooth concrete floor, minimal empty space around, calm realistic setting",
        "light": "soft overhead parking light, even realistic illumination, no harsh shadows"
    },
    {
        "scene": "standing in a clean corner of an underground parking garage, "
                 "concrete wall on one side, pillar on the other, empty floor around",
        "light": "cool overhead parking light, soft bounce from concrete walls, natural even light"
    },
    {
        "scene": "standing on an open-air parking level with clean concrete floor and low barriers, "
                 "minimal open space around, simple realistic urban setting",
        "light": "soft overcast daylight, no direct sunlight, even natural light"
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
        "scene": "standing beside clean metal railings of a modern pedestrian bridge, "
                 "concrete bridge surface underfoot, simple minimal surroundings",
        "light": "soft overcast daylight, no harsh contrast, natural even light"
    },
    {
        "scene": "standing close to a smooth dark concrete wall in a modern urban setting, "
                 "calm minimal background, no distractions",
        "light": "soft diffused daylight, gentle shadow transition, natural realistic light"
    },
    {
        "scene": "standing close to a smooth dark stone wall, "
                 "clean surface with subtle texture, minimal surroundings, quiet aesthetic setting",
        "light": "soft diffused natural light, even illumination across the wall and subject"
    },
    {
        "scene": "standing in a modern open concrete passage with a clean wall close to the body, "
                 "architectural ceiling above, minimal realistic urban space",
        "light": "soft ambient light filtering from above, gentle bounce from concrete surfaces"
    },
    {
        "scene": "standing on an open rooftop parking level, "
                 "clean concrete floor, low barriers, calm open space around",
        "light": "soft overcast daylight, no direct sun, natural even illumination"
    }
]

# ---------------- ФОНЫ СЗАДИ ----------------

BACK_SCENES = [
    {
        "scene": "standing far away in a massive clean underground parking garage, "
                 "concrete pillars creating deep perspective, empty floor, person small in wide corridor",
        "light": "soft even overhead parking light, gentle bounce from concrete surfaces, realistic neutral illumination"
    },
    {
        "scene": "standing far away on a wide empty open-air parking lot, "
                 "clean asphalt stretching far in all directions, person tiny in open space",
        "light": "soft natural overcast daylight, no harsh shadows, even realistic light"
    },
    {
        "scene": "standing far away on an open rooftop parking level, "
                 "clean concrete floor, low barriers, wide empty space around, person small in frame",
        "light": "soft natural overcast daylight, calm even illumination across entire scene"
    },
    {
        "scene": "standing far away on an empty modern pedestrian bridge, "
                 "clean railings on both sides, bridge stretching far ahead, person small in wide frame",
        "light": "soft diffused daylight, no direct sun, no harsh shadows, natural even light"
    },
    {
        "scene": "standing far away in a clean open-air multi-level parking structure, "
                 "long concrete ramps, repeated horizontal lines, empty parking lanes, "
                 "person small in deep perspective",
        "light": "soft neutral daylight, gentle concrete reflections, even realistic illumination"
    },
    {
        "scene": "standing far away with back to camera beside a parked Ferrari in a clean open urban setting, "
                 "only part of the rear quarter, wheel and body of the car visible, "
                 "car remains secondary, person small in the frame",
        "light": "soft natural overcast daylight, no direct sun, "
                 "gentle even illumination across subject, car and ground"
    },
    {
        "scene": "standing far away on a long straight empty road, "
                 "simple realistic urban surroundings, wide open space, person tiny in frame",
        "light": "soft overcast daylight, cool natural tones, no direct sunlight"
    },
    {
        "scene": "standing far away in a wide empty concrete courtyard, "
                 "minimal surroundings, large clean ground plane, person small in open space",
        "light": "soft diffused daylight, even realistic illumination"
    },
    {
        "scene": "standing far away on a wide empty access road leading into a parking complex, "
                 "clean asphalt, low concrete edges, long straight perspective, person small in the distance",
        "light": "soft neutral daylight, even natural illumination, no harsh contrast"
    },
    {
        "scene": "walking upward on a wide clean concrete staircase in a modern urban setting, "
                 "seen fully from behind, strong architectural lines, person small in the frame, "
                 "stairs rising upward with calm minimal surroundings",
        "light": "soft diffused daylight, even realistic illumination across staircase, "
                 "no harsh shadows, no direct sunlight"
    }
]

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "right hand gripping the hood edge near temple, left hand in front jeans pocket, weight on right leg",
    "both hands adjusting the hood from the front, chin slightly down, elbows slightly outward",
    "right hand pulling the hood lower over the forehead, left hand gripping the side hem of the hoodie",
    "left hand pulling the hood edge slightly forward, right hand in front jeans pocket, body turned slightly left",
    "both hands holding both hood edges near the jawline, shoulders slightly raised",
    "right hand on hood near temple, left hand resting flat on upper thigh, relaxed stance"
]

BACK_POSES = [
    "standing facing away, right hand holding the back edge of the hood, left arm relaxed along outer thigh",
    "standing facing away, left hand holding the back edge of the hood, right arm relaxed along outer thigh",
    "standing facing away, both hands holding the hood from behind, elbows slightly outward",
    "walking away, right hand holding the back edge of the hood, left arm moving naturally with stride",
    "walking away, left hand holding the back edge of the hood, right arm moving naturally with stride",
    "walking away, both hands briefly adjusting the hood from behind, head slightly lowered",
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
        "Not cut out. Not composited. Not isolated. "

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

        "Hands actively engaged. Not hanging freely at sides. "
        "No hands in back pockets. No hands in hoodie pocket. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


# ---------------- ПРОМПТ СЗАДИ ----------------

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

        "No passive pose. "
        "No hands in back pockets of jeans. "
        "Hands must interact with the hood or rest behind the head on the nape only. "
        "If walking, one arm may move naturally with stride. "

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
