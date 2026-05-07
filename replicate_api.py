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
    {
        "scene": "standing next to a matte black luxury SUV on a quiet empty city street at golden hour, "
                 "warm light reflecting on the car surface and wet asphalt below, "
                 "clean urban architecture visible in the background",
        "light": "warm golden side light from low sun on the left, "
                 "soft natural shadow falling to the right, "
                 "slight warm reflection bouncing up from wet ground, "
                 "light catches the fabric texture of the hoodie naturally"
    },
    {
        "scene": "standing on a wide empty pedestrian street at blue hour, "
                 "modern glass buildings lining both sides, "
                 "clean stone pavement below, soft city glow ahead",
        "light": "cool natural blue hour ambient light from open sky above, "
                 "subtle warm accent from distant streetlights ahead, "
                 "soft even illumination revealing fabric texture clearly, "
                 "no harsh shadows, natural light wrapping around the figure"
    },
    {
        "scene": "standing on a wide modern bridge with clean concrete railings at dusk, "
                 "calm river below, city skyline glowing softly on the horizon",
        "light": "soft diffused dusk light from horizon ahead, "
                 "subtle warm city glow reflecting from water below, "
                 "even cool ambient light from open sky above, "
                 "light falls naturally on fabric showing full texture detail"
    },
    {
        "scene": "standing in a clean open-air multi-level parking structure at night, "
                 "city lights visible through the open concrete barriers behind, "
                 "smooth concrete floor below",
        "light": "cool overhead parking lights falling straight down on the subject, "
                 "soft ambient bounce from concrete walls and floor, "
                 "warm city glow coming through barriers from behind, "
                 "overhead light reveals hoodie fabric weave and texture sharply"
    },
    {
        "scene": "standing on a clean empty city plaza at golden hour, "
                 "large modern building facade behind, "
                 "wide stone pavement stretching to both sides",
        "light": "warm directional golden hour sunlight from the right, "
                 "long natural shadow cast to the left on stone pavement, "
                 "warm light raking across hoodie fabric revealing full texture, "
                 "warm ambient sky fill from above"
    },
    {
        "scene": "standing on a wide empty urban embankment at blue hour, "
                 "calm river visible to the side, "
                 "clean modern city architecture behind",
        "light": "cool blue hour ambient light from open sky above, "
                 "subtle warm reflections from water surface, "
                 "soft even natural illumination across fabric and scene, "
                 "gentle light showing cotton hoodie texture clearly"
    },
    {
        "scene": "standing in a wide clean concrete tunnel underpass at night, "
                 "warm ceiling lights lining the tunnel symmetrically above, "
                 "smooth tunnel floor below reflecting light",
        "light": "warm overhead tunnel lights illuminating subject from directly above, "
                 "natural soft shadows falling below, "
                 "overhead light hitting hoodie fabric at an angle revealing texture weave, "
                 "warm ambient bounce from concrete walls"
    },
    {
        "scene": "standing on a clean empty rooftop parking level at night, "
                 "city skyline stretching across the full background at horizon level, "
                 "smooth rooftop floor clearly visible below feet",
        "light": "soft wide ambient backlight from illuminated city skyline behind, "
                 "cool dark sky light from above as subtle fill on fabric, "
                 "rim lighting on shoulders from city glow behind, "
                 "natural nighttime atmosphere"
    }
]

BACK_SCENES = [
    {
        "scene": "standing still on a wide empty city street at blue hour, "
                 "modern buildings lining both sides creating strong perspective depth, "
                 "clean stone pavement stretching far ahead, "
                 "person is a small clear silhouette deep in the wide urban space",
        "light": "cool natural blue hour ambient light from open sky above, "
                 "warm distant streetlight glow far ahead, "
                 "soft natural shadows on the wide pavement below"
    },
    {
        "scene": "walking away across a wide modern bridge at dusk, "
                 "clean concrete railings on both sides, "
                 "calm river and city skyline visible far beyond, "
                 "person small and naturally placed in the wide open bridge space",
        "light": "soft diffused dusk ambient light from open sky above, "
                 "subtle warm city glow from horizon far ahead, "
                 "gentle reflections from water surface below"
    },
    {
        "scene": "standing in a vast open-air parking lot at night, "
                 "clean asphalt stretching far in all directions, "
                 "city lights glowing beyond the parking perimeter far away, "
                 "person small and clearly readable in the vast empty space",
        "light": "cool overhead parking lot lights falling evenly from above, "
                 "soft ambient bounce from wide asphalt surface, "
                 "warm city glow from far beyond the parking perimeter"
    },
    {
        "scene": "walking away along a wide empty urban embankment at golden hour, "
                 "calm river stretching far on one side, "
                 "clean city architecture far on the other, "
                 "person naturally small in the vast wide open embankment space",
        "light": "warm golden hour sunlight from the right side, "
                 "long natural shadows stretching far to the left, "
                 "soft warm reflection from the river surface"
    },
    {
        "scene": "standing in a massive underground parking garage at night, "
                 "concrete pillars lining both sides creating strong perspective depth far ahead, "
                 "fluorescent ceiling lights stretching far into the distance, "
                 "person small and clearly visible deep in the wide garage corridor",
        "light": "cool overhead fluorescent lights falling evenly from above, "
                 "soft ambient bounce from concrete floor and walls, "
                 "clean even lighting with soft shadows below feet"
    },
    {
        "scene": "walking away along a long straight empty city avenue at dusk, "
                 "rows of trees and modern buildings creating natural symmetry far on both sides, "
                 "person small and naturally placed far down the wide long avenue",
        "light": "soft diffused dusk ambient light from open sky above, "
                 "warm streetlights beginning to glow far ahead in the distance, "
                 "even natural cinematic lighting"
    },
    {
        "scene": "standing on a wide open rooftop terrace at night, "
                 "full illuminated city skyline stretching across the entire background at horizon level far behind, "
                 "clean rooftop floor surface visible below feet and all around the figure, "
                 "person small against the vast wide city backdrop",
        "light": "wide soft ambient backlight from the full illuminated city skyline far behind, "
                 "cool dark sky from above as subtle fill, "
                 "natural nighttime cinematic atmosphere"
    },
    {
        "scene": "walking away through a vast clean concrete plaza between tall modern office towers, "
                 "towers rising very high on both sides far above, "
                 "wide open stone pavement stretching all around, "
                 "person small and naturally integrated in the massive open urban space",
        "light": "soft even overcast daylight from open sky above, "
                 "subtle ambient bounce from stone pavement and tall tower facades, "
                 "clean natural diffused lighting with soft shadows"
    }
]

FRONT_POSES = [
    "right hand gripping the hood near the temple, left hand in jeans pocket",
    "both hands adjusting the hood from the front",
    "right hand pulling hood slightly forward, chin slightly down"
]

BACK_POSES = [
    "standing completely still, arms relaxed at sides, facing away",
    "slowly walking away from camera, natural stride",
    "right hand resting loosely on the back of the hood, facing away"
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

    used_scenes = set()
    specs = []
    sides = ["back", "front", "back"]

    for side in sides:
        attempts = 0
        chosen = None

        while attempts < 30:
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

            scene_key = scene_data["scene"][:60]

            if scene_key not in used_scenes:
                used_scenes.add(scene_key)
                chosen = {
                    "side": side,
                    "scene": scene_data["scene"],
                    "light": scene_data["light"],
                    "pose": pose,
                    "seed": random.randint(100000, 999999),
                    "ref": ref
                }
                break

            attempts += 1

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
        "Looks exactly like a real photo taken by a photographer on location. "
        "Shot on Sony A7R V, 35mm lens, f/8 aperture, ISO 400. "
        "Camera at eye level. Straight-on angle. No tilt. No high angle. No low angle. "
        "Camera distance exactly 1.0 meter from subject. "
        "Framing from top of head to exactly the knees. "
        "Cut off exactly at the knees — not higher, not lower. "
        "Subject occupies 80 to 85 percent of the vertical frame height. "

        # Единство с фоном
        "The subject is a natural part of the real scene. "
        "Subject and background are one single unified photograph. "
        "Not isolated. Not composited. Not cut out from background. "
        "Background is sharp, fully detailed, naturally rendered like a real location. "
        "Deep depth of field. No bokeh. No blur anywhere in the image. "

        # Свет — максимально реалистичный
        f"Lighting: {spec['light']}. "
        "Lighting is physically accurate and fully consistent across the entire image. "
        "The exact same light source illuminates both the subject and the environment. "
        "Shadows on the subject match the shadows in the surrounding scene perfectly. "
        "Light wraps naturally around the figure and the fabric. "
        "No studio flash. No artificial separate light source. "
        "No flat lighting. Natural realistic light behavior. "

        # Текстура ткани — максимальная детализация
        "The hoodie fabric texture must be rendered with extreme photorealistic detail. "
        "Every fiber, weave and stitch of the cotton fabric is clearly visible. "
        "The fabric has natural micro-texture, subtle wrinkles and folds from real wear. "
        "Light interacts physically with the fabric surface — "
        "showing subtle sheen on raised fibers, soft shadows in fabric valleys. "
        "The cotton material looks tactile and real — you can almost feel the texture. "
        "No smooth plastic-looking fabric. No flat fabric rendering. "
        "Maximum fabric realism as if shot with a macro lens on the clothing. "

        # Джинсы — обязательно широкие
        "MANDATORY: extremely wide-leg loose straight black denim jeans. "
        "The jeans must have a very clearly baggy and wide silhouette. "
        "Wide around the entire leg — thighs, knees and calves all equally wide. "
        "Heavy denim fabric with visible denim texture and natural folds at the ankles. "
        "Not slim fit. Not skinny. Not tapered. Not straight regular fit. "
        "Visibly and unmistakably wide-leg baggy jeans. "

        # Худи — детальная прорисовка лого
        "Hoodie taken exactly from reference image. "
        "STRICT RULES FOR HOODIE: "
        "absolutely no kangaroo pocket, no front pouch, no zipper, no drawstrings visible. "
        "The front chest logo must be rendered with maximum sharpness and detail. "
        "Logo size, position, font, design must match the reference exactly. "
        "Logo must be clearly readable and sharp in the final image. "
        "Do not blur, distort, resize or reinterpret the logo in any way. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Looks exactly like a real photo taken by a photographer standing on location. "
        "Sony A7R V, 35mm lens, f/8 aperture. "

        # Камера строго горизонтально
        "Camera held at normal human eye level by a standing photographer. "
        "Camera height exactly 1.6 meters from ground. "
        "Camera pointing straight forward, perfectly parallel to the ground. "
        "STRICT: no high angle. No top-down. No aerial. "
        "No drone. No elevated position. No tilt downward. "
        "No surveillance angle. No bird eye view. No rooftop angle. "

        # Далеко
        "Camera distance 12 to 15 meters from subject. "
        "Full body from top of head to feet completely visible. "
        "Feet flat on the ground, fully visible in frame. "
        "Ground clearly visible below feet — "
        "at least 15 percent of frame height below the feet. "
        "Do not crop at ankles. Do not crop at shins. Do not crop at knees. "
        "Subject occupies only 15 to 20 percent of the vertical frame height. "
        "The person is a small but clearly readable figure in a large environment. "
        "The surrounding environment dominates the frame. "

        "Background is sharp, fully detailed, naturally rendered. "
        "Deep depth of field. Everything in focus. No blur. "

        # Свет
        f"Lighting: {spec['light']}. "
        "Lighting is physically accurate and consistent across the full image. "
        "The same light source illuminates both the subject and the environment. "
        "Shadows on the subject match the shadows in the scene perfectly. "
        "No studio flash. No artificial separate light. "

        # Джинсы — обязательно широкие
        "MANDATORY: extremely wide-leg loose straight black denim jeans. "
        "Very clearly baggy and wide silhouette visible even from distance. "
        "Wide around thighs, knees and calves equally. "
        "Not slim. Not skinny. Not tapered. Visibly wide-leg. "

        "Black hoodie with no pocket. "
        "Loose wide straight black jeans. "
        "Hood up. Face completely hidden. "
        "Entire body seen from behind. No face visible. "

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
    specs = get_unique_specs()

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
