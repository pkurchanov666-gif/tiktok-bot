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

# ---------------- 25 ФОНОВ ДЛЯ BACK ФОТО ----------------

BACK_BACKGROUNDS = [
    "https://i.ibb.co/Q202Tjs/5188269594370577196.jpg",
    "https://i.ibb.co/bMFggbS5/5188269594370577197.jpg",
    "https://i.ibb.co/gMqqyZC1/5188269594370577198.jpg",
    "https://i.ibb.co/vCrrMv6B/5188269594370577199.jpg",
    "https://i.ibb.co/wNpL22K1/5188269594370577200.jpg",
    "https://i.ibb.co/MkK2LmcJ/5188269594370577201.jpg",
    "https://i.ibb.co/tTp0ZZjH/5188269594370577202.jpg",
    "https://i.ibb.co/ZznnWzL8/5188269594370577203.jpg",
    "https://i.ibb.co/ksZ5F1PG/5188269594370577204.jpg",
    "https://i.ibb.co/5g3Cmmys/5188269594370577205.jpg",
    "https://i.ibb.co/35L07V91/5188269594370577206.jpg",
    "https://i.ibb.co/5x6GhY2T/5188269594370577207.jpg",
    "https://i.ibb.co/pvT20qmb/5188269594370577208.jpg",
    "https://i.ibb.co/SDFDpTXH/5188269594370577209.jpg",
    "https://i.ibb.co/FkTQGZYj/5188269594370577173.jpg",
    "https://i.ibb.co/233bJXqc/5188269594370577176.jpg",
    "https://i.ibb.co/cKLPQcw1/5188269594370577174.jpg",
    "https://i.ibb.co/C3c4dxN6/5188269594370577175.jpg",
    "https://i.ibb.co/JjsyBCxw/5188269594370577177.jpg",
    "https://i.ibb.co/DPgbpSGm/5188269594370577178.jpg",
    "https://i.ibb.co/Z6TdkrCY/5188269594370577179.jpg",
    "https://i.ibb.co/8LZDkMZc/5188269594370577180.jpg",
    "https://i.ibb.co/DFqg1Gg/5188269594370577181.jpg",
    "https://i.ibb.co/5WMJcgYN/5188269594370577182.jpg",
    "https://i.ibb.co/jvNW8tD5/5188269594370577183.jpg"
]

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

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "leaning naturally, right hand resting on upper thigh, "
    "left hand resting on lower back",

    "leaning naturally, both hands resting on thighs, "
    "chin slightly down, elbows relaxed",

    "leaning naturally, left hand resting on upper thigh, "
    "right hand resting on lower back",

    "leaning naturally, right hand resting on hip, "
    "left hand resting on upper thigh",

    "leaning naturally, right hand in relaxed position along outer thigh, "
    "left hand resting on hip",

    "leaning naturally, left hand in relaxed position along outer thigh, "
    "right hand resting on hip",

    "leaning naturally, right hand resting on hip, "
    "left hand resting on upper thigh, chin slightly down",

    "leaning naturally, both hands resting firmly on thighs, "
    "shoulders confident, chin level"
]

BACK_POSES = [
    "standing facing away, hood up covering head, right hand resting on outer thigh, "
    "left arm hanging freely at side",

    "standing facing away, hood up covering head, left hand resting on outer thigh, "
    "right arm hanging freely at side",

    "standing facing away, hood up covering head, both hands resting on outer thighs, "
    "confident athletic posture",

    "walking away, hood up covering head, both arms swinging naturally with stride, "
    "relaxed walking pace",

    "walking away, hood up covering head, right hand behind head on back of neck above shoulders, "
    "left arm swinging freely with stride",

    "walking away, hood up covering head, left hand behind head on back of neck above shoulders, "
    "right arm swinging freely with stride"
]


# ---------------- SPEC ----------------

def get_unique_specs():
    specs = []
    used_poses = set()
    used_backgrounds = set()
    sides = ["back", "front", "back"]

    for side in sides:
        if side == "front":
            scenes = FRONT_SCENES
            poses = FRONT_POSES
            ref = REF_FRONT
            bg = None
            scene_data = random.choice(scenes)
        else:
            poses = BACK_POSES
            ref = REF_BACK
            scene_data = {"scene": "", "light": "soft natural daylight"}
            
            # Выбираем RANDOM фон для BACK фото
            available_bgs = [b for b in BACK_BACKGROUNDS if b not in used_backgrounds]
            if not available_bgs:
                available_bgs = BACK_BACKGROUNDS
            bg = random.choice(available_bgs)
            used_backgrounds.add(bg)

        available_poses = [p for p in poses if p not in used_poses]
        if not available_poses:
            available_poses = poses
        
        pose = random.choice(available_poses)
        used_poses.add(pose)

        specs.append({
            "side": side,
            "scene": scene_data.get("scene", ""),
            "light": scene_data.get("light", "soft natural daylight"),
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": ref,
            "background": bg
        })

    return specs


# ---------------- FRONT PROMPT ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 professional fashion photograph. "
        "STRICT FRONT VIEW CLOSE SHOT ONLY. "
        "Sony A7R V, 35mm lens, f/4, ISO 200. "
        "Camera at eye level, 1.5 meters from subject. "
        "Framing from head to knees. Subject 70-75 percent of frame. "
        "Subject facing camera directly. "

        "CRITICAL - CHEST LOGO RENDERING: "
        "Chest logo must be EXTREMELY SHARP and PERFECTLY CLEAR. "
        "Logo is the focal point of the hoodie. "
        "Logo rendering: maximum sharpness, exact size and position from reference image. "
        "Logo must be crisp, clear, fully readable with no blur or distortion. "
        "Logo color and details must match reference image exactly. "
        "Light reflects perfectly on logo, enhancing visibility and definition. "
        "Logo edges are sharp and well-defined. "

        "HOODIE SPECIFICATIONS: "
        "Premium black hoodie, completely flat clean front. "
        "No front pocket, no kangaroo pouch, no zipper, no drawstrings. "
        "Only the chest logo visible on front. "

        "Sharp focus throughout - subject and background equally sharp. "
        "No blur, no bokeh. One unified photograph. "

        "Subject leans or stands against environment naturally. "
        "Visible physical contact with surface: wall, car, or railing. "
        "NOT floating. NOT cut out. Part of the location. "

        "Black wide-leg denim, heavy texture visible. "

        "Hands visible, actively engaged with thighs or hips. "
        "Hands rest naturally on thighs or hip. "
        "Natural confident posture. "

        "Background sharp and detailed. NOT blurred. "
        "Architecture, pavement, car details all clearly visible. "

        f"Lighting: {spec['light']}. "
        "Soft natural light, no harsh shadows, no flash. "
        "Light enhances logo visibility and detail. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "

        "Generate an ultra-realistic professional fashion photograph. "
        "Everything sharp. Everything real. Professional quality."
    ) + uid


# ---------------- BACK PROMPT ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 professional environmental photograph. "
        "Back view shot integrated into the provided background location. "
        "Evening or golden hour time of day. Realistic warm evening atmosphere. "

        "CRITICAL INSTRUCTION - SCALE AND HUMAN PROPORTIONS: "
        "The subject MUST be placed at CORRECT HUMAN SCALE. "
        "Subject height must be proportional to: "
        "- Standard door height = 2.1 meters "
        "- Standard window height = 1.5 meters "
        "- Standard railing height = 1.2 meters "
        "- Standard bench height = 0.5 meters "
        "- Ground features and step dimensions "
        "Subject must appear to be a NORMAL ADULT HUMAN (1.75 meters tall). "
        "NOT a giant filling the frame. NOT a tiny dwarf. HUMAN SCALE. "
        "Head approximately 1/7 of total body height. "
        "Torso approximately 1/3 of body. Legs approximately 1/2 of body. "
        "Proportions must match real human anatomy exactly. "

        "CRITICAL INSTRUCTION - BACKGROUND INTEGRATION: "
        "The subject must be naturally and realistically placed within the exact location "
        "shown in the provided background reference image. "
        "Subject is authentically PART of this environment, not floating, not composited. "
        "Match ALL lighting, perspective, depth and atmospheric conditions from background. "

        "Subject Positioning: "
        "Place subject in CENTER-MID area of frame, naturally integrated. "
        "Subject scale: 10-15 percent of frame height (correct human size, not tiny, not giant). "
        "Full body visible from head to feet, standing or walking naturally. "
        "Feet MUST clearly touch the ground surface visible in background. "
        "Subject must cast REALISTIC SHADOWS matching background's light direction and time of day. "
        "Perspective and depth MUST match background photograph exactly. "

        "Subject Appearance: "
        "Black hoodie with hood UP covering head completely. "
        "Face completely hidden, BACK VIEW ONLY. "
        "Black wide-leg baggy denim jeans, heavy texture visible. "
        "Hands visible: either at sides, on thighs, or behind head above neck. "
        "ABSOLUTELY NO hands in pockets, NO hidden arms, NO denim pockets. "
        "Natural confident posture appropriate for location and movement. "

        "Lighting Integration - EVENING/GOLDEN HOUR: "
        "This is an EVENING or GOLDEN HOUR photograph - warm evening light. "
        "Match exact lighting conditions from background photograph. "
        "Subject must be lit CONSISTENTLY with background environment. "
        "Shadows, highlights and COLOR TEMPERATURE must match background exactly. "
        "Light source direction MUST match background's light angle. "
        "EVENING LIGHT creates LONGER SHADOWS - render these REALISTICALLY on ground. "
        "Color temperature: WARM GOLDEN/AMBER TONES for evening atmosphere. "
        "No artificial lighting. No flash. No studio setup. "
        "Light behaves realistically across subject, ground and surroundings. "

        "Photography Quality: "
        "Sharp focus throughout entire image. "
        "Subject and background equally sharp and detailed. "
        "No blur. No bokeh. No selective focus. "
        "ONE unified realistic photograph. "
        "Ultra-realistic seamless integration, NOT composited or artificial. "
        "Looks like real photograph taken at location, NOT CGI or edited composite. "

        "HUMAN SCALE VERIFICATION CHECKLIST: "
        "[ ] Subject height proportional to doors, windows, railings? YES "
        "[ ] Subject appears NORMAL ADULT SIZE? YES "
        "[ ] NOT scaled as giant? YES "
        "[ ] NOT scaled as tiny figure? YES "
        "[ ] Head to body proportions correct? YES "
        "[ ] Feet clearly on ground? YES "
        "[ ] Realistic human anatomy? YES "

        f"Pose: {spec['pose']}. "

        "Generate a natural realistic evening photograph where the subject is authentically "
        "integrated into the exact location shown in the provided background image, "
        "at CORRECT HUMAN SCALE with realistic proportions, "
        "with realistic evening lighting and shadows. "
        "Result must look like a single real photograph taken at that location in the evening. "
        "NOT a composite. NOT digital manipulation. REAL PHOTOGRAPH."
    ) + uid


# ---------------- POLZA ----------------

def submit_job(prompt, image_url, background_url=None):
    polza_key = os.getenv("POLZA_API_KEY")

    images = [{"type": "url", "data": image_url}]
    if background_url:
        images.append({"type": "url", "data": background_url})

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
                "images": images
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


async def poll_job(job_id, retry_count=0, max_retries=3):
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
                f"[POLZA] job={job_id} waited={waited}s status={status}"
            )

            if status in {"failed", "error", "canceled", "cancelled"}:
                error_msg = str(data.get("error", {}))
                logger.error(f"[POLZA] Job failed: {error_msg}")
                
                if "BAD_GATEWAY" in error_msg and retry_count < max_retries:
                    logger.info(f"[POLZA] Retrying...")
                    await asyncio.sleep(10)
                    return None
                
                raise Exception(f"Polza job failed: {data}")

            url = extract_url(data)
            if url:
                logger.info(f"[POLZA] Generated: {url}")
                return url

        except Exception as e:
            if "failed" in str(e).lower():
                raise
            logger.warning(f"[POLZA] Poll error: {e}")

    raise Exception(f"Timeout {max_wait}s")


async def download_image(url, path):
    response = await asyncio.to_thread(requests.get, url, timeout=60)
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(response.content)


# ---------------- GENERATION ----------------

async def generate_all_photos():
    specs = get_unique_specs()
    job_ids = []
    max_job_retries = 3

    for i, spec in enumerate(specs):
        if spec["side"] == "front":
            prompt = build_front_prompt(spec)
            bg_url = None
        else:
            prompt = build_back_prompt(spec)
            bg_url = spec["background"]
        
        job_id = None
        for attempt in range(max_job_retries):
            try:
                job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"], bg_url)
                if job_id:
                    break
            except Exception as e:
                logger.warning(f"[SUBMIT] Attempt {attempt + 1} failed: {e}")
                if attempt < max_job_retries - 1:
                    await asyncio.sleep(5)
        
        if not job_id:
            logger.error(f"[SUBMIT] Failed for spec {i}")
            continue
        
        job_ids.append(job_id)
        if i < len(specs) - 1:
            await asyncio.sleep(3)

    urls = await asyncio.gather(*[poll_job(job_id) for job_id in job_ids], return_exceptions=True)

    paths = []
    for index, url in enumerate(urls):
        if isinstance(url, Exception):
            logger.error(f"[DOWNLOAD] Failed for index {index}: {url}")
            continue
        if not url:
            logger.warning(f"[DOWNLOAD] No URL for index {index}")
            continue
        
        path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_{index}.png")
        try:
            await download_image(url, path)
            paths.append(path)
        except Exception as e:
            logger.error(f"[DOWNLOAD] Failed: {e}")

    return paths, specs, list(urls)


async def regenerate_photo(index, current_specs):
    """Регенерирует фото с новым фоном (для BACK) или новой сценой (для FRONT)"""
    
    logger.info(f"[REGEN] Photo {index}")
    
    if index < 0 or index >= len(current_specs):
        raise Exception(f"Invalid index {index}")
    
    old_spec = current_specs[index]
    side = old_spec["side"]

    if side == "front":
        scenes = FRONT_SCENES
        poses = FRONT_POSES
        ref = REF_FRONT
        bg = None
        scene_data = random.choice(scenes)
    else:
        poses = BACK_POSES
        ref = REF_BACK
        scene_data = {"scene": "", "light": "soft natural daylight"}
        
        # Выбираем НОВЫЙ фон (не старый)
        available_bgs = [b for b in BACK_BACKGROUNDS if b != old_spec.get("background")]
        if not available_bgs:
            available_bgs = BACK_BACKGROUNDS
        bg = random.choice(available_bgs)

    available_poses = [p for p in poses if p != old_spec.get("pose")]
    if not available_poses:
        available_poses = poses
    pose = random.choice(available_poses)

    new_spec = {
        "side": side,
        "scene": scene_data.get("scene", ""),
        "light": scene_data.get("light", "soft natural daylight"),
        "pose": pose,
        "seed": random.randint(100000, 999999),
        "ref": ref,
        "background": bg
    }

    if side == "front":
        prompt = build_front_prompt(new_spec)
        bg_url = None
    else:
        prompt = build_back_prompt(new_spec)
        bg_url = bg

    try:
        job_id = await asyncio.to_thread(submit_job, prompt, new_spec["ref"], bg_url)
        logger.info(f"[REGEN] Job: {job_id}")
    except Exception as e:
        logger.error(f"[REGEN] Submit failed: {e}")
        raise

    try:
        url = await poll_job(job_id)
        if not url:
            raise Exception("No URL")
    except Exception as e:
        logger.error(f"[REGEN] Poll failed: {e}")
        raise

    path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_regen_{index}.png")
    try:
        await download_image(url, path)
    except Exception as e:
        logger.error(f"[REGEN] Download failed: {e}")
        raise

    current_specs[index] = new_spec
    
    return path, new_spec, url
