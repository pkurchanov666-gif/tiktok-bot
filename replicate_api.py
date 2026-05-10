import os
import time
import random
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

SAVE_DIR = "generations"
MAX_PROMPT_LENGTH = 4900

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

used_backgrounds_global = set()

# ---------------- FRONT SCENES ----------------

FRONT_SCENES = [
    {
        "scene": "leaning against dark Porsche in underground garage, car door and fender very close to body, polished concrete floor, soft LED lights, other cars blurred far away, evening atmosphere",
        "light": "soft ambient garage lighting, golden warm tones, even illumination"
    },
    {
        "scene": "standing with body very close to black Lamborghini Urus, almost touching the car, only part of hood visible in frame, modern business street behind in evening dusk, clean granite pavement, city lights beginning to glow",
        "light": "golden hour evening light, warm amber tones, soft natural glow transitioning to dusk"
    },
    {
        "scene": "leaning against dark glass building facade, body pressed close to glass, contemporary architecture right behind, evening city reflections in glass, urban environment",
        "light": "soft evening diffused light, warm golden reflections from glass, ambient city glow"
    },
    {
        "scene": "standing body-close to black Mercedes-AMG GT, car door very near, only small part of car visible, marble columns and modern entrance barely visible, evening dusk setting, luxury location",
        "light": "soft golden hour evening light, warm natural illumination, gentle shadows"
    },
    {
        "scene": "leaning close against modern glass railing, railing tight against body, city view far behind, evening cityscape with glowing lights in background, rooftop or modern building",
        "light": "soft golden hour evening light, warm natural glow, ambient city lights in distance"
    },
    {
        "scene": "standing body-close to black Audi A8 parked on quiet street, almost touching car door, only part of door and fender in frame, elegant house facade and plants blurred behind, evening atmosphere, street lamps beginning to illuminate",
        "light": "soft evening daylight transitioning to dusk, warm golden tones, gentle ambient glow"
    },
    {
        "scene": "leaning tight against dark stone wall in modern residential courtyard, wall close behind, body pressed against it, minimalist architecture partially visible, evening setting with soft lighting, urban courtyard",
        "light": "soft warm evening light, natural golden glow, ambient architectural lighting"
    },
    {
        "scene": "leaning tight against black luxury SUV in private garage, body very close to car surface, only part of SUV in frame, epoxy floor close beneath feet, evening atmosphere with warm lighting, clean modern garage",
        "light": "soft indirect LED evening lighting, warm golden tones, subtle highlights on car and fabric"
    },
    {
        "scene": "standing on rooftop parking right next to parked car, body very close to vehicle, only small portion visible, concrete and white parking lines at feet, open evening sky above with sunset colors, urban rooftop",
        "light": "soft golden hour evening light, warm sunset tones, natural evening atmosphere"
    }
]

# ---------------- ПОЗЫ ----------------

FRONT_POSES = [
    "leaning naturally, right fingertips resting lightly on hood fabric near temple, left hand resting loosely on upper thigh, relaxed elbows, hood down",
    "leaning naturally, both hands resting lightly on both sides of hood from the front, chin slightly down, elbows relaxed, shoulders against surface, hood down",
    "leaning naturally, left fingertips resting lightly on hood fabric near cheek, right arm relaxed along outer thigh, natural posture, hood down",
    "leaning naturally, both hands resting lightly near hood opening without pulling the fabric, shoulders relaxed, confident stance, hood down",
    "leaning naturally, right hand resting lightly on hood fabric near temple, left hand resting flat on upper thigh, balanced posture, hood down",
    "leaning naturally, right hand resting on back of head, left arm relaxed along outer thigh, comfortable position, hood down",
    "leaning naturally, left hand resting on back of head, right arm relaxed along outer thigh, natural lean, hood down",
    "leaning naturally, right hand resting on back of head, left hand resting on upper thigh, chin slightly down, relaxed stance, hood down"
]

BACK_POSES = [
    "walking away, hood UP covering head completely, both arms swinging naturally with stride, relaxed walking pace, natural movement",
    "walking away, hood UP covering head completely, right hand behind head on neck above shoulders, left arm swinging naturally with stride, natural walking motion",
    "walking away, hood UP covering head completely, left hand behind head on neck above shoulders, right arm swinging naturally with stride, natural walking motion",
    "standing facing away, hood UP covering head completely, right hand raised adjusting hood near head, left hand also raised touching hood fabric on other side, active positioning",
    "standing facing away, hood UP covering head completely, both hands raised adjusting hood, fingers touching hood fabric near head and shoulders, engaged posture"
]


# ============ FUNCTIONS ============

def get_random_background():
    global used_backgrounds_global
    available_bgs = [b for b in BACK_BACKGROUNDS if b not in used_backgrounds_global]
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
            scene_data = {"scene": "", "light": "soft warm evening light"}
            bg = get_random_background()

        available_poses = [p for p in poses if p not in used_poses]
        if not available_poses:
            available_poses = poses
        
        pose = random.choice(available_poses)
        used_poses.add(pose)

        specs.append({
            "side": side,
            "scene": scene_data.get("scene", ""),
            "light": scene_data.get("light", "warm light"),
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": ref,
            "background": bg
        })

    return specs


# ============ PROMPTS ============

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}"
    
    prompt = (
        "Ultra-realistic RAW 9:16 professional photography. STRICT FRONT VIEW CLOSE SHOT ONLY. "
        "EVENING TIME - Golden hour or early dusk atmosphere. Sony A7R V camera, 35mm lens, f/4 aperture, ISO 400. "
        "Camera positioned at eye level, 1.2 meters distance from subject. Framing spans from head to mid-thigh. "
        "Subject occupies 70-75 percent of frame. Subject facing camera directly, centered composition. "
        
        "HOOD POSITION AND STYLING: Hood is DOWN resting on shoulders and back of subject. "
        "Head and face clearly visible matching reference style. Hood fabric clearly visible behind head and draped on shoulders. "
        "Premium fabric appearance with natural draping. Hood edges clearly defined. "
        
        "EVENING LIGHTING ATMOSPHERE - CRITICAL: Warm golden hour or early dusk lighting throughout. "
        "Soft amber and golden tones dominating entire image. Natural evening glow with warm color temperature. "
        "Gentle shadows appropriate for evening time, no harsh contrast. Ambient city lights or architectural lighting softly visible in background. "
        "No harsh midday sun. No bright daylight. Pure evening atmosphere. Warm light bathes subject and environment equally. "
        
        "CHEST LOGO - CRITICAL REQUIREMENT: Chest logo must be EXTREMELY SHARP and PERFECTLY CLEAR. "
        "Logo is focal point of image with maximum sharpness throughout. Exact size and position matching reference. "
        "Logo crisp, clear, fully readable. Not blurred, not distorted. Logo colors and details match reference exactly. "
        "Logo well-lit by evening light, clearly visible and prominent. Fine details of logo visible. "
        
        "HOODIE SPECIFICATIONS AND QUALITY: Premium quality black hoodie with completely flat, clean front. "
        "No front pocket visible, no kangaroo pouch, no zipper visible, no drawstrings visible. "
        "Only chest logo visible on front surface. Premium fabric with subtle texture visible. "
        "Natural fabric draping visible. Clean construction evident. "
        
        "FOCUS AND SHARPNESS - CRITICAL: Sharp focus throughout entire image. "
        "Subject and background equally sharp and detailed. No blur, no bokeh effects. "
        "One unified professional photograph. Everything in focus. Every detail visible and sharp. "
        
        "SUBJECT ENVIRONMENT INTERACTION: Subject must physically interact with environment naturally. "
        "Visible physical contact with surface: wall, car door, or railing. Contact point clearly visible. "
        "Subject authentically part of location, not floating, not cut out. Grounded in environment. "
        
        "JEANS - FABRIC DETAIL: Black wide-leg denim jeans with heavy texture clearly visible and sharp. "
        "Denim weave pattern visible. Stitching details visible. Natural fabric folds visible. "
        "Premium denim quality evident through fabric texture. "
        
        "HANDS AND POSTURE - CRITICAL: Hands actively engaged and clearly visible in frame. "
        "If touching hoodie: fingers clearly visible on fabric, natural contact. "
        "If positioned on head: hand visible, fingers well-defined. Natural confident posture throughout. "
        "Body language relaxed and comfortable. Professional fashion shoot posture. "
        
        "BACKGROUND ENVIRONMENT - SHARP: Background sharp and detailed, not blurred. "
        "Architecture, pavement, car details all clearly visible and sharp. "
        "Evening atmosphere in background: warm lights, dusk sky, golden tones. "
        "Environmental details support evening setting. Background complements subject. "
        f"Scene: {spec['scene']}. "
        
        f"Lighting: {spec['light']}. Warm evening light, soft natural glow. No harsh shadows. No flash used. "
        "Golden hour or dusk color temperature. Light enhances logo visibility and detail throughout image. "
        "Professional lighting setup creating premium appearance. "
        
        f"Pose: {spec['pose']}. "
        
        "TIME OF DAY AND ATMOSPHERE: Evening, golden hour or early dusk setting. Warm amber tones. "
        "Soft evening glow throughout. Natural evening atmosphere. Time is critical evening period. "
        
        "FINAL RENDER REQUIREMENTS: Generate ultra-realistic professional evening fashion photograph. "
        "Everything sharp, everything real, photorealistic. Premium quality lighting and composition. "
        "Professional fashion magazine quality. Perfect for commercial use. "
    )
    
    prompt += uid
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        logger.warning(f"[PROMPT] FRONT too long: {len(prompt)} > {MAX_PROMPT_LENGTH}")
        prompt = prompt[:MAX_PROMPT_LENGTH]
    
    logger.info(f"[PROMPT] FRONT: {len(prompt)}/{MAX_PROMPT_LENGTH} chars")
    return prompt


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}"
    
    prompt = (
        "Ultra-realistic RAW 9:16 professional environmental photograph. "
        "Back view shot integrated into provided background location. "
        "Evening or golden hour time of day. Realistic warm evening atmosphere. "
        
        "HOOD MANDATORY - CRITICAL: Hood MUST be UP on head, completely covering head. "
        "This is MANDATORY requirement. Hood covering head from back view. "
        "Hood fabric clearly visible covering head and upper back. "
        "Face completely hidden, BACK VIEW ONLY. NO exceptions - hood is ALWAYS UP. "
        
        "HAND AND ARM POSITIONING - CRITICAL: "
        "FORBIDDEN ZONES - hands must NEVER touch: hips, buttocks, lower back, hip area, back pockets, waist level, anywhere near lower torso. "
        "ALLOWED when WALKING: arms swing naturally at sides with motion. "
        "ALLOWED when STANDING: both hands actively adjusting hood near head. "
        "NO idle standing with hands hanging free. NEVER touching lower body or hip area. "
        
        "HUMAN SCALE AND PROPORTIONS - CRITICAL: Subject MUST be at CORRECT HUMAN SCALE. "
        "Subject height proportional to standard doors (2.1 meters), windows (1.5 meters), railings (1.2 meters), ground features. "
        "Normal adult human (1.75 meters tall). NOT giant filling frame. NOT tiny dwarf. HUMAN SCALE correct. "
        "Head approximately 1/7 of total body height. Torso approximately 1/3 of body. Legs approximately 1/2 of body. "
        "Proportions must match real human anatomy exactly. Real-world scale maintained throughout. "
        
        "BACKGROUND INTEGRATION - CRITICAL: Subject naturally and realistically placed in exact location from background reference. "
        "Subject authentically PART of environment, not floating, not composited. "
        "Match ALL lighting, perspective, depth and atmospheric conditions from background. "
        
        "SUBJECT POSITIONING: Place in CENTER-MID area of frame, naturally integrated. "
        "Subject scale 10-15 percent of frame height (correct human size). "
        "Full body visible from head to feet, standing or walking naturally. "
        "Feet MUST clearly touch ground surface visible in background. "
        "Subject must cast REALISTIC SHADOWS matching background's light direction and time of day. "
        "Perspective and depth MUST match background photograph exactly. "
        
        "SUBJECT APPEARANCE AND CLOTHING: Black hoodie with HOOD UP completely covering head. "
        "Face completely hidden, BACK VIEW ONLY. Hood clearly visible on head from behind. "
        "Black wide-leg baggy denim jeans, heavy texture clearly visible. "
        "Arms and hands positioned according to activity: "
        "If WALKING: arms swing naturally OR one hand behind head at neck above shoulders. "
        "If STANDING: both hands actively adjusting hood. "
        "ABSOLUTELY NO hands on hips, lower back, or buttocks area. "
        "ABSOLUTELY NO standing with idle hands. Natural confident posture. "
        
        "EVENING LIGHTING INTEGRATION - CRITICAL: This is EVENING or GOLDEN HOUR photograph - warm evening light. "
        "Match exact lighting conditions from background photograph precisely. "
        "Subject lit CONSISTENTLY with background environment. "
        "Shadows, highlights and COLOR TEMPERATURE match background exactly. "
        "Light source direction MUST match background's light angle. "
        "EVENING LIGHT creates LONGER SHADOWS - render these REALISTICALLY on ground. "
        "Color temperature: WARM GOLDEN/AMBER TONES for evening atmosphere. "
        "No artificial lighting, no flash, no studio setup. "
        "Light behaves realistically across subject, ground and surroundings. "
        
        "PHOTOGRAPHY QUALITY - CRITICAL: Sharp focus throughout entire image. "
        "Subject and background equally sharp and detailed. No blur, no bokeh, no selective focus. "
        "ONE unified realistic photograph. Ultra-realistic seamless integration, NOT composited or artificial. "
        "Looks like real photograph taken at location, NOT CGI or edited composite. "
        
        f"Pose: {spec['pose']}. "
        
        "Generate natural realistic evening photograph where subject is authentically integrated into background location at CORRECT HUMAN SCALE with realistic proportions, "
        "HOOD UP on head (MANDATORY), hands positioned correctly (adjusting hood when standing, or swinging when walking), "
        "realistic evening lighting and shadows. Result must look like single real photograph taken at that location in evening. "
        "NOT composite. NOT manipulation. REAL PHOTOGRAPH. Professional quality rendering."
    )
    
    prompt += uid
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        logger.warning(f"[PROMPT] BACK too long: {len(prompt)} > {MAX_PROMPT_LENGTH}")
        prompt = prompt[:MAX_PROMPT_LENGTH]
    
    logger.info(f"[PROMPT] BACK: {len(prompt)}/{MAX_PROMPT_LENGTH} chars")
    return prompt


# ============ POLZA API ============

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
        raise Exception(f"Non-JSON response: {response.text}")

    logger.info(f"[POLZA] Submit response: {data}")

    job_id = data.get("id") or data.get("task_id")
    if not job_id:
        raise Exception(f"No job ID in response: {data}")

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
                logger.warning(f"[POLZA] Non-JSON: {response.text[:200]}")
                continue

            status = str(data.get("status", "")).lower()

            logger.info(f"[POLZA] Job {job_id}: waited {waited}s, status {status}")

            if status in {"failed", "error", "canceled", "cancelled"}:
                error_msg = str(data.get("error", {}))
                logger.error(f"[POLZA] Job failed: {error_msg}")
                
                if "BAD_GATEWAY" in error_msg and retry_count < max_retries:
                    logger.info(f"[POLZA] Retrying job...")
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


# ============ GENERATION ============

async def generate_all_photos():
    specs = get_unique_specs()
    logger.info(f"[GENERATE] Starting {len(specs)} photos: {[s['side'] for s in specs]}")
    
    job_ids = []
    max_job_retries = 3

    for i, spec in enumerate(specs):
        logger.info(f"[GENERATE] Processing spec {i}: {spec['side']}")
        
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
                    logger.info(f"[GENERATE] Spec {i} submitted: {job_id}")
                    break
            except Exception as e:
                logger.warning(f"[SUBMIT] Spec {i} attempt {attempt + 1}: {e}")
                if attempt < max_job_retries - 1:
                    await asyncio.sleep(5)
        
        if not job_id:
            logger.error(f"[SUBMIT] Failed for spec {i}")
            continue
        
        job_ids.append(job_id)
        if i < len(specs) - 1:
            await asyncio.sleep(3)

    logger.info(f"[GENERATE] Submitted {len(job_ids)}/{len(specs)} jobs")

    urls = await asyncio.gather(*[poll_job(job_id) for job_id in job_ids], return_exceptions=True)
    
    logger.info(f"[GENERATE] Received {len(urls)} results")

    paths = []
    for index, url in enumerate(urls):
        if isinstance(url, Exception):
            logger.error(f"[DOWNLOAD] Index {index}: {url}")
            continue
        if not url:
            logger.warning(f"[DOWNLOAD] No URL for index {index}")
            continue
        
        path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_{index}.png")
        try:
            await download_image(url, path)
            paths.append(path)
            logger.info(f"[DOWNLOAD] Saved index {index}")
        except Exception as e:
            logger.error(f"[DOWNLOAD] Index {index}: {e}")

    logger.info(f"[GENERATE] Final: {len(paths)}/{len(specs)} photos saved")
    return paths, specs, list(urls)


async def regenerate_photo(index, current_specs):
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
        scene_data = {"scene": "", "light": "soft warm evening light"}
        bg = get_random_background()

    available_poses = [p for p in poses if p != old_spec.get("pose")]
    if not available_poses:
        available_poses = poses
    
    pose = random.choice(available_poses)

    new_spec = {
        "side": side,
        "scene": scene_data.get("scene", ""),
        "light": scene_data.get("light", "warm light"),
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
