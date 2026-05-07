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
        "scene": "standing next to a matte black luxury SUV on a quiet city street at golden hour, "
                 "warm light reflecting on the car surface and wet asphalt",
        "light": "warm golden side light from low sun on the left, "
                 "soft natural shadow falling to the right, "
                 "slight warm reflection bouncing up from wet ground"
    },
    {
        "scene": "standing on a wide empty pedestrian street at blue hour, "
                 "modern glass buildings on both sides, soft city glow ahead",
        "light": "cool natural blue hour ambient light from open sky above, "
                 "subtle warm accent from distant streetlights, "
                 "soft even illumination with no harsh shadows"
    },
    {
        "scene": "standing in front of a large glass office building at dusk, "
                 "warm interior lights glowing through the glass facade behind",
        "light": "warm ambient glow coming through glass behind as soft backlight, "
                 "cool blue dusk sky light as front fill, "
                 "natural rim light on shoulders from building glow"
    },
    {
        "scene": "standing beside a concrete pillar in a modern open plaza at golden hour, "
                 "long shadows across stone pavement, warm late sun visible ahead",
        "light": "warm directional golden hour sunlight from the right side, "
                 "long natural shadow cast to the left on pavement, "
                 "warm ambient fill from sky above"
    },
    {
        "scene": "standing on a wide empty bridge over a calm river at dusk, "
                 "city lights beginning to reflect in the water below, "
                 "soft purple and orange sky on the horizon",
        "light": "soft diffused dusk light from the horizon ahead, "
                 "subtle warm reflections rising from river surface below, "
                 "even cool ambient light from sky above"
    },
    {
        "scene": "standing at the entrance of a modern underground parking ramp, "
                 "geometric ceiling lights overhead, smooth concrete walls on both sides",
        "light": "cool overhead fluorescent lights falling straight down on the subject, "
                 "soft ambient bounce from concrete walls on both sides, "
                 "clean even lighting with soft shadows directly below feet"
    },
    {
        "scene": "standing on an empty rooftop terrace at night, "
                 "illuminated city skyline stretching across the background at horizon level",
        "light": "soft ambient city glow from skyline behind as wide backlight, "
                 "cool dark sky light from above as subtle fill, "
                 "natural nighttime atmosphere with no artificial flash"
    },
    {
        "scene": "standing in a wide concrete tunnel underpass at night, "
                 "warm ceiling lights lining the tunnel symmetrically, "
                 "light pooling naturally on the ground",
        "light": "warm overhead tunnel lights illuminating subject from above and slightly ahead, "
                 "natural soft shadows falling directly below, "
                 "warm ambient bounce from concrete walls"
    },
    {
        "scene": "standing at the entrance of a luxury apartment building at night, "
                 "warm marble lobby visible through glass doors behind, "
                 "clean stone steps below",
        "light": "warm interior light spilling outward through glass as soft backlight, "
                 "cool ambient night air light as front fill, "
                 "gentle natural side shadow from building frame"
    },
    {
        "scene": "standing on a quiet cobblestone alley in a modern city district at night, "
                 "warm light from nearby shops softly illuminating the stone pavement",
        "light": "warm scattered ambient light from shop windows on both sides, "
                 "soft even illumination with no harsh direct light source, "
                 "golden warm tones reflecting naturally on cobblestone below"
    }
]

BACK_SCENES = [
    {
        "scene": "walking slowly away on a wide empty pedestrian street at blue hour, "
                 "modern city buildings lining both sides, soft city lights beginning to glow",
        "light": "cool natural blue hour ambient light from open sky above, "
                 "warm distant streetlight glow ahead in the distance, "
                 "soft natural shadows on the pavement below"
    },
    {
        "scene": "standing still on a wide urban embankment facing a calm river at dusk, "
                 "city skyline glowing softly across the water in the distance",
        "light": "soft warm dusk light from the horizon ahead as front ambient, "
                 "subtle warm reflections from water surface below, "
                 "even cool sky light from above as fill"
    },
    {
        "scene": "walking away through a wide underground parking garage, "
                 "fluorescent ceiling lights overhead, concrete pillars on both sides",
        "light": "cool overhead fluorescent lighting falling evenly on subject from above, "
                 "soft ambient bounce light from concrete floor and walls, "
                 "clean shadows falling directly below the figure"
    },
    {
        "scene": "standing on an empty wide city plaza at golden hour, "
                 "modern architecture surrounding the open space, "
                 "long natural shadows across stone pavement",
        "light": "warm directional golden hour sunlight from the right side, "
                 "long soft natural shadow stretching to the left on pavement, "
                 "warm ambient sky fill from above"
    },
    {
        "scene": "walking away along a long straight city avenue at dusk, "
                 "rows of trees and buildings on both sides creating natural symmetry",
        "light": "soft diffused dusk ambient light from open sky above, "
                 "warm streetlights beginning to glow ahead, "
                 "even natural cinematic lighting with soft shadows"
    },
    {
        "scene": "standing on an empty rooftop terrace at night, "
                 "illuminated city skyline across the full horizon behind, "
                 "rooftop floor surface clearly visible below feet",
        "light": "wide soft backlight from illuminated city skyline behind, "
                 "subtle cool dark sky light from above, "
                 "natural nighttime atmosphere no artificial flash"
    },
    {
        "scene": "walking away through a wide concrete tunnel underpass at night, "
                 "warm ceiling lights lining the tunnel ahead, "
                 "light reflecting naturally on the smooth tunnel floor",
        "light": "warm overhead tunnel ceiling lights illuminating subject evenly from above, "
                 "natural light pools on floor ahead creating depth, "
                 "soft warm ambient bounce from tunnel walls"
    },
    {
        "scene": "standing at the far end of a wide courtyard between modern office buildings at dusk, "
                 "warm building windows glowing around the open space",
        "light": "warm ambient glow from surrounding building windows on all sides, "
                 "soft even diffused dusk light from open sky above, "
                 "gentle natural shadows on the ground below"
    },
    {
        "scene": "walking away on a quiet cobblestone street at night, "
                 "warm light from shops and streetlamps softly illuminating the scene",
        "light": "warm scattered ambient light from street lamps and shop windows, "
                 "soft golden reflections on wet cobblestone below, "
                 "even warm natural atmosphere no flash"
    },
    {
        "scene": "standing on a wide modern bridge over a river at blue hour, "
                 "city lights reflected in calm water below, "
                 "soft purple and orange tones on the horizon ahead",
        "light": "soft diffused blue hour ambient light from open sky above, "
                 "warm reflections from city lights on water below as subtle fill, "
                 "even natural cinematic dusk lighting"
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
    "right hand resting on the back of the hood, facing away"
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


# ---------------- ПРОМПТЫ ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Looks exactly like a real photo taken by a photographer on location. "
        "Sony A7R V, 35mm lens, f/8 aperture. "
        "Camera at eye level. Straight-on angle. "
        "No tilt. No high angle. No low angle. "
        "Camera distance 1.5 meters from subject. "

        "Framing from top of head to just below the knees. "
        "Subject occupies 65 to 70 percent of vertical frame height. "

        "The subject is fully part of the real environment. "
        "The person and the background are one single unified photograph. "
        "Not isolated. Not composited. Not cut out. "
        "Background is fully sharp, detailed, naturally rendered. "
        "Looks like a real location, not a backdrop. "
        "Deep depth of field. No bokeh. No blur anywhere. "

        f"Lighting: {spec['light']}. "
        "Light source is physically real and consistent across the entire image. "
        "The light falls on the subject from the exact same source as the environment. "
        "Shadows on the subject match shadows in the scene perfectly. "
        "Light wraps naturally around the figure. "
        "No studio flash. No artificial light added separately. "
        "No overexposed face. No flat lighting. "
        "Skin tones and fabric tones react naturally to the light source. "

        "Hoodie from reference image exactly. "
        "STRICT: no kangaroo pocket. No front pouch. No zipper. No drawstrings. "
        "Front chest logo preserved exactly — same size, same position, same design. "

        "Loose straight wide-leg black denim jeans. "
        "Baggy silhouette. Not slim. Not skinny. Not tapered. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 photograph. "
        "Looks exactly like a real photo taken by a photographer standing on location. "
        "Sony A7R V, 35mm lens, f/8 aperture. "

        "Camera held by a standing photographer at human eye level. "
        "Camera height exactly 1.6 meters from ground. "
        "Camera pointing straight forward, perfectly parallel to ground. "
        "STRICT: no high angle. No top-down. No aerial. "
        "No drone. No elevated position. No tilt downward. "
        "No surveillance angle. No bird eye view. "

        "Camera distance 6 to 8 meters from subject. "
        "Full body from top of head to feet completely visible. "
        "Feet flat on ground, fully visible in frame. "
        "Ground below feet visible — at least 10 percent of frame below feet. "
        "Do not crop at ankles. Do not crop at shins. Do not crop at knees. "
        "Subject occupies 28 to 35 percent of vertical frame height. "

        "The subject naturally belongs to the scene. "
        "Background is sharp, detailed, fully rendered like a real location. "
        "Deep depth of field. Everything in focus. No blur. "

        f"Lighting: {spec['light']}. "
        "Light source is physically real and consistent across the entire image. "
        "Light falls on the subject from the exact same source as the environment. "
        "Shadows on subject match shadows in the scene perfectly. "
        "No studio flash. No artificial separate light. "
        "Natural realistic light behavior across fabric and ground. "

        "Black hoodie, no pocket. "
        "Loose wide straight black jeans. "
        "Hood up. Face completely hidden. Body seen entirely from behind. "

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
