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

# ---------------- 20 ФОНОВ ДЛЯ BACK ФОТО ----------------

BACK_BACKGROUNDS = [
    "https://i.ibb.co/ZznnWzL8/5188269594370577203.jpg",
    "https://i.ibb.co/ksZ5F1PG/5188269594370577204.jpg",
    "https://i.ibb.co/35L07V91/5188269594370577206.jpg",
    "https://i.ibb.co/5x6GhY2T/5188269594370577207.jpg",
    "https://i.ibb.co/pvT20qmb/5188269594370577208.jpg",
    "https://i.ibb.co/XrSnJK6x/5188269594370577210.jpg",
    "https://i.ibb.co/FkTQGZYj/5188269594370577173.jpg",
    "https://i.ibb.co/233bJXqc/5188269594370577176.jpg",
    "https://i.ibb.co/cKLPQcw1/5188269594370577174.jpg",
    "https://i.ibb.co/JjsyBCxw/5188269594370577177.jpg",
    "https://i.ibb.co/DPgbpSGm/5188269594370577178.jpg",
    "https://i.ibb.co/Z6TdkrCY/5188269594370577179.jpg",
    "https://i.ibb.co/8LZDkMZc/5188269594370577180.jpg",
    "https://i.ibb.co/DFqg1Gg/5188269594370577181.jpg",
    "https://i.ibb.co/jvNW8tD5/5188269594370577183.jpg",
    "https://i.ibb.co/kVhXCppK/5188269594370577184.jpg",
    "https://i.ibb.co/LXTr6Hn7/5188269594370577185.jpg",
    "https://i.ibb.co/TDqy7wjw/5188269594370577186.jpg",
    "https://i.ibb.co/bMFggbS5/5188269594370577197.jpg",
    "https://i.ibb.co/gMqqyZC1/5188269594370577198.jpg"
]

# ГЛОБАЛЬНЫЙ ТРЕКЕР ИСПОЛЬЗОВАННЫХ ФОНОВ
used_backgrounds_global = set()

# ---------------- FRONT SCENES ----------------

FRONT_SCENES = [
    {
        "scene": "leaning against a dark Porsche parked in a clean underground garage, "
                 "car door and fender very close to body, polished concrete floor, "
                 "soft LED lights, other cars blurred far away, evening atmosphere",
        "light": "soft warm evening garage lighting, ambient LED glow, golden warm tones, no harsh shadows"
    },
    {
        "scene": "standing with body very close to a black Lamborghini Urus, "
                 "almost touching the car, only part of hood visible in frame, "
                 "modern business street behind in evening dusk, clean granite pavement, "
                 "city lights beginning to glow",
        "light": "golden hour evening light, warm amber tones, soft natural glow transitioning to dusk"
    },
    {
        "scene": "leaning against a dark glass building facade, "
                 "body pressed close to glass, contemporary architecture right behind, "
                 "evening city reflections in glass",
        "light": "soft evening diffused light, warm golden reflections from glass, ambient city glow"
    },
    {
        "scene": "standing body-close to a black Mercedes-AMG GT, "
                 "car door very near, only small part of car visible, "
                 "marble columns and modern entrance barely visible, evening dusk setting",
        "light": "soft golden hour evening light, warm natural illumination, gentle shadows"
    },
    {
        "scene": "leaning close against modern glass railing, "
                 "railing tight against body, city view far behind, "
                 "evening cityscape with glowing lights in background",
        "light": "soft golden hour evening light, warm natural glow, ambient city lights in distance"
    },
    {
        "scene": "standing body-close to a black Audi A8 parked on quiet street, "
                 "almost touching car door, only part of door and fender in frame, "
                 "elegant house facade and plants blurred behind, evening atmosphere, "
                 "street lamps beginning to illuminate",
        "light": "soft evening daylight transitioning to dusk, warm golden tones, gentle ambient glow"
    },
    {
        "scene": "leaning tight against dark stone wall in modern residential courtyard, "
                 "wall close behind, body pressed against it, "
                 "minimalist architecture partially visible, evening setting with soft lighting",
        "light": "soft warm evening light, natural golden glow, ambient architectural lighting"
    },
    {
        "scene": "leaning tight against a black luxury SUV in private garage, "
                 "body very close to car surface, only part of SUV in frame, "
                 "epoxy floor close beneath feet, evening atmosphere with warm lighting",
        "light": "soft indirect LED evening lighting, warm golden tones, subtle highlights on car and fabric"
    },
    {
        "scene": "standing on rooftop parking right next to a parked car, "
                 "body very close to vehicle, only small portion visible, "
                 "concrete and white parking lines at feet, open evening sky above with sunset colors",
        "light": "soft golden hour evening light, warm sunset tones, natural evening atmosphere"
    }
]

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "leaning naturally, right fingertips resting lightly on the hood fabric near the temple, "
    "left hand resting loosely on upper thigh, hood down",

    "leaning naturally, both hands resting lightly on both sides of the hood from the front, "
    "chin slightly down, elbows relaxed, hood down",

    "leaning naturally, left fingertips resting lightly on the hood fabric near the cheek, "
    "right arm relaxed along outer thigh, hood down",

    "leaning naturally, both hands resting lightly near the hood opening without pulling the fabric, "
    "shoulders relaxed, hood down",

    "leaning naturally, right hand resting lightly on the hood fabric near the temple, "
    "left hand resting flat on upper thigh, hood down",

    "leaning naturally, right hand resting on the back of the head, "
    "left arm relaxed along outer thigh, hood down",

    "leaning naturally, left hand resting on the back of the head, "
    "right arm relaxed along outer thigh, hood down",

    "leaning naturally, right hand resting on the back of the head, "
    "left hand resting on upper thigh, chin slightly down, hood down"
]

BACK_POSES = [
    "walking away, hood UP completely covering head, "
    "right hand behind head touching back of neck ABOVE shoulders, "
    "left arm swinging naturally with stride at side of body",

    "walking away, hood UP completely covering head, "
    "left hand behind head touching back of neck ABOVE shoulders, "
    "right arm swinging naturally with stride at side of body",
    
    "standing facing away, hood UP completely covering head, "
    "right hand raised to adjust hood near head, "
    "left hand raised near hood fabric on other side",
    
    "standing facing away, hood UP completely covering head, "
    "left hand raised to adjust hood near head, "
    "right hand touching hood fabric near shoulder area"
]


# ---------------- SPEC ----------------

def get_random_background():
    """Выбирает случайный фон, исключая уже использованные"""
    global used_backgrounds_global
    
    available_bgs = [b for b in BACK_BACKGROUNDS if b not in used_backgrounds_global]
    
    # Если все фоны использованы, сбрасываем счетчик и начинаем заново
    if not available_bgs:
        used_backgrounds_global.clear()
        available_bgs = BACK_BACKGROUNDS
    
    bg = random.choice(available_bgs)
    used_backgrounds_global.add(bg)
    return bg


def get_unique_specs():
    specs = []
    used_poses = set()
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
            
            # Выбираем случайный фон (не повторяющийся)
            bg = get_random_background()

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
        "Ultra-realistic RAW 9:16 photograph. "
        "STRICT FRONT VIEW CLOSE SHOT ONLY. "
        "EVENING TIME - Golden hour or dusk atmosphere. "
        "Sony A7R V, 35mm lens, f/4, ISO 400. "
        "Camera at eye level, 1.2 meters from subject. "
        "Framing from head to mid-thigh. Subject 70-75 percent of frame. "
        "Subject facing camera directly. "

        "HOOD POSITION FOR FRONT VIEW: "
        "Hood is DOWN. Hood rests on shoulders and back. "
        "Head and face visible (face hidden as per reference style). "
        "Hood fabric visible behind head and on shoulders. "

        "EVENING LIGHTING ATMOSPHERE: "
        "Warm golden hour or early dusk lighting. "
        "Soft amber and golden tones throughout the image. "
        "Natural evening glow, warm color temperature. "
        "Gentle shadows appropriate for evening time. "
        "Ambient city lights or architectural lighting softly visible in background. "
        "No harsh midday sun. No bright daylight. Evening atmosphere only. "

        "CRITICAL - CHEST LOGO RENDERING: "
        "Chest logo must be EXTREMELY SHARP and PERFECTLY CLEAR. "
        "Logo is the focal point. Maximum sharpness, exact size and position from reference. "
        "Logo crisp, clear, fully readable. Not blurred. Not distorted. "
        "Logo color and details match reference image exactly. "
        "Logo well-lit by evening light, clearly visible. "

        "HOODIE SPECIFICATIONS: "
        "Premium black hoodie, completely flat clean front. "
        "No front pocket. No kangaroo pouch. No zipper. No drawstrings. "
        "Only the chest logo visible on front. "

        "Sharp focus throughout - subject and background equally sharp. "
        "No blur. No bokeh. One unified photograph. "

        "Subject must physically interact with environment naturally. "
        "Visible physical contact with surface: wall, car, or railing. "
        "Not floating. Not cut out. Part of the location. "

        "Black wide-leg denim jeans, heavy texture visible and sharp. "

        "Hands actively engaged. Visible in frame. "
        "If touching hoodie: fingers visible on fabric. "
        "If on head: hand visible, fingers defined. "
        "Natural confident posture. "

        "Background sharp and detailed. Not blurred. "
        "Architecture, pavement, car details all clearly visible and sharp. "
        "Evening atmosphere in background - warm lights, dusk sky, golden tones. "

        f"Lighting: {spec['light']}. "
        "Warm evening light. Soft natural glow. No harsh shadows. No flash. "
        "Golden hour or dusk color temperature. "
        "Light enhances logo visibility and detail. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "

        "TIME OF DAY: Evening, golden hour or early dusk. "
        "Warm amber tones. Soft evening glow. Natural evening atmosphere. "

        "Generate ultra-realistic professional evening fashion photograph. "
        "Everything sharp. Everything real. Evening atmosphere. Premium quality."
    ) + uid


# ---------------- BACK PROMPT ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic RAW 9:16 professional environmental photograph. "
        "Back view shot integrated into the provided background location. "
        "Evening or golden hour time of day. Realistic warm evening atmosphere. "

        "CRITICAL - HOOD MUST BE UP: "
        "Hood MUST be UP on head, completely covering the head. "
        "This is MANDATORY. Hood covering head from back view. "
        "Hood fabric clearly visible covering head and upper back. "
        "NO exceptions - hood is ALWAYS UP for back view shots. "

        "CRITICAL - ARM AND HAND POSITIONING RULES: "
        "FORBIDDEN ZONES - hands must NEVER be positioned: "
        "- On hips or hip area "
        "- On buttocks or lower back "
        "- In back pockets "
        "- Behind back at waist level "
        "- Anywhere near lower torso from behind "
        "- Hanging loosely doing nothing "
        
        "ALLOWED hand positions ONLY: "
        "- Behind head touching NECK area ABOVE shoulders "
        "- Actively adjusting hood near head/upper back area "
        "- Both hands must be ENGAGED in activity "
        "- NEVER idle or hanging free "
        "- NEVER touching lower body or hip area "

        "CRITICAL INSTRUCTION - SCALE AND HUMAN PROPORTIONS: "
        "The subject MUST be placed at CORRECT HUMAN SCALE. "
        "Subject height must be proportional to: "
        "- Standard door height = 2.1 meters "
        "- Standard window height = 1.5 meters "
        "- Standard railing height = 1.2 meters "
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
        "Black hoodie with HOOD UP - HOOD COMPLETELY COVERING HEAD. "
        "Face completely hidden, BACK VIEW ONLY. "
        "Hood must be clearly visible on head from behind. "
        "Black wide-leg baggy denim jeans, heavy texture visible. "
        "Arms and hands ACTIVELY positioned - behind head/neck or adjusting hood. "
        "ABSOLUTELY NO hands on hips, lower back, or buttocks area. "
        "ABSOLUTELY NO idle hands hanging free. "
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

        "HUMAN SCALE VERIFICATION: "
        "Subject height proportional to doors, windows, railings? YES. "
        "Subject appears NORMAL ADULT SIZE? YES. "
        "NOT scaled as giant? YES. NOT scaled as tiny figure? YES. "
        "Head to body proportions correct? YES. Feet clearly on ground? YES. "
        "Realistic human anatomy? YES. "
        "HOOD IS UP ON HEAD? YES - MANDATORY. "
        "Hands NOT on hips/buttocks/lower back? YES - MANDATORY. "
        "Hands actively engaged, not idle? YES - MANDATORY. "

        f"Pose: {spec['pose']}. "

        "REMINDER: Hood MUST be UP covering head completely. "
        "REMINDER: Hands must be ACTIVELY engaged - behind head/neck or adjusting hood. "
        "REMINDER: NO idle hands. NO hands on hips/lower body. "

        "Generate a natural realistic evening photograph where the subject is authentically "
        "integrated into the exact location shown in the provided background image, "
        "at CORRECT HUMAN SCALE with realistic proportions, "
        "with HOOD UP on head, "
        "with hands ACTIVELY engaged (behind head or adjusting hood), "
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
        
        # Выбираем новый случайный фон (не повторяющийся)
        bg = get_random_background()

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
