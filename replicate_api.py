import os
import time
import random
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

SAVE_DIR = "generations"
MAX_PROMPT_LENGTH = 4900

# ================= REFS =================

REF_FRONT = "https://i.ibb.co/0RWjBVdH/5215527801883138653.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# ================= FRONT BACKGROUNDS =================

FRONT_BACKGROUNDS = [
    "https://i.ibb.co/FLv2PmSR/5219908140244082508.jpg",
    "https://i.ibb.co/GQHjbgKs/5219908140244082507.jpg",
    "https://i.ibb.co/5hNTm0hN/5219908140244082506.jpg",
    "https://i.ibb.co/qYv31dPf/5219908140244082505.jpg",
    "https://i.ibb.co/YTtrLZGQ/5219908140244082504.jpg",
    "https://i.ibb.co/nsGfwWyW/5219908140244082501.jpg",
    "https://i.ibb.co/zTFL1PDC/5219908140244082499.jpg",
    "https://i.ibb.co/8DLPndjC/5219908140244082500.jpg",
    "https://i.ibb.co/HL426hmw/5219908140244082502.jpg",
    "https://i.ibb.co/JjQ1yJmp/5219908140244082503.jpg",
    "https://i.ibb.co/7tTD8rLt/5219908140244082498.jpg",
    "https://i.ibb.co/0R04rmYz/5219908140244082497.jpg"
]

# ================= BACK BACKGROUNDS =================

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

used_backgrounds_front = set()
used_backgrounds_back = set()

# ================= POSES =================

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

# ================= HELPERS =================

def get_random_background(bg_list, used_set):
    available_bgs = [b for b in bg_list if b not in used_set]
    if not available_bgs:
        used_set.clear()
        available_bgs = bg_list
    bg = random.choice(available_bgs)
    used_set.add(bg)
    return bg


def get_unique_specs():
    specs = []
    used_poses = set()
    sides = ["back", "front", "back"]

    for side in sides:
        if side == "front":
            poses = FRONT_POSES
            ref = REF_FRONT
            bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)
            light = ""
            scene = ""
        else:
            poses = BACK_POSES
            ref = REF_BACK
            bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)
            light = "soft warm evening light"
            scene = ""

        available_poses = [p for p in poses if p not in used_poses]
        if not available_poses:
            available_poses = poses

        pose = random.choice(available_poses)
        used_poses.add(pose)

        specs.append({
            "side": side,
            "scene": scene,
            "light": light,
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": ref,
            "background": bg
        })

    return specs


# ================= PROMPTS =================

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}"

    prompt = (
        "Ultra-realistic RAW professional fashion editorial, 9:16 vertical composition. "
        "CRITICAL REFERENCE LOCK: use the EXACT subject from Reference Photo 1 and the EXACT environment from Reference Photo 2. "
        "Do not redesign the subject. Do not redesign the background. "
        "Reference Photo 1 defines the exact face, body proportions, clothing, fabric, chest logo, and overall styling. "
        "Reference Photo 2 defines the exact environment, architecture, pavement, perspective, framing logic, lighting mood, and spatial layout. "

        "COMPOSITION AND FRAMING: "
        "Strict FRONT-facing close fashion shot only. "
        "Frame from head to mid-thigh. "
        "Subject occupies around 70 to 75 percent of the frame height. "
        "Natural eye-level camera angle. "
        "Premium editorial composition with strong realism and no artificial look. "

        "POSITIONING AND INTERACTION: "
        "The subject from Reference Photo 1 is physically placed into the exact location from Reference Photo 2. "
        "He is leaning his lower back and hip naturally against the architectural or structural surface visible in Reference Photo 2. "
        "The torso is rotated 100 percent front-facing toward the camera. "
        "The chest surface remains perfectly flat and unobstructed so the chest logo from Reference Photo 1 stays perfectly readable. "
        "Natural weight distribution, realistic body pressure, realistic contact point, realistic compression shadow where the body touches the surface from Reference Photo 2. "
        "No floating effect. No pasted-on look. No cutout feeling. "

        "LOGO PRIORITY - CRITICAL: "
        "The chest logo from Reference Photo 1 must remain exact in size, geometry, placement, proportions, and visual weight. "
        "The logo must be the sharpest and clearest area in the image. "
        "No perspective distortion, no warping, no stretching, no blur, no slanting, no logo redesign. "
        "Logo must remain perfectly flat, centered, and fully readable. "

        "LIGHT MATCHING - PROFESSIONAL EDITORIAL: "
        "Match the exact lighting direction, color temperature, exposure mood, and ambient atmosphere from Reference Photo 2. "
        "Use the environment lighting from Reference Photo 2 as the main lighting base. "
        "Add only a subtle controlled professional key light on the chest area to improve logo clarity while preserving total realism. "
        "If justified by the environment, add a subtle rim separation light to separate the silhouette from the background without breaking realism. "
        "Accurate ground bounce light from pavement and architectural surfaces. "
        "Accurate contact shadows under the feet and at every touch point between the subject and the environment. "
        "No fake flash look. No studio over-lighting. No mismatched shadows. No conflicting color cast. "

        "TEXTURE AND MATERIAL PHYSICS: "
        "Preserve original material realism from Reference Photo 1. "
        "Visible cotton grain, realistic fabric density, natural folds, premium textile definition, realistic denim weave, realistic stitching, realistic shadow falloff across folds. "
        "Preserve separation between matte fabric surfaces from Reference Photo 1 and the architectural or reflective surfaces from Reference Photo 2. "
        "Natural skin texture with no plastic smoothing. "
        "No artificial oversharpening. No CGI feel. "

        "DEPTH, OPTICS, AND CAMERA PHYSICS: "
        "Shot on iPhone 17 Pro Max, 24mm equivalent lens, f/1.7 aperture, advanced Smart HDR-5 computational photography look. "
        "Subject in critical sharp focus. "
        "Background from Reference Photo 2 remains clearly recognizable and structurally accurate, with only slight natural lens falloff if needed. "
        "Correct perspective scale relative to the environment. "
        "No warped vertical lines, no stretched body parts, no scale distortion. "

        "FINAL RESULT: "
        "The final image must look like one real luxury editorial photograph captured in the exact place shown in Reference Photo 2, "
        "with the exact person and exact clothing from Reference Photo 1 seamlessly integrated into that scene. "
        "Photorealistic, premium, commercial, ultra-detailed, realistic, luxury streetwear campaign quality. "

        f"Pose instructions: {spec['pose']}. "
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


# ================= POLZA API =================

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


# ================= GENERATION =================

async def generate_all_photos():
    specs = get_unique_specs()
    logger.info(f"[GENERATE] Starting {len(specs)} photos: {[s['side'] for s in specs]}")

    job_ids = []
    max_job_retries = 3

    for i, spec in enumerate(specs):
        logger.info(f"[GENERATE] Processing spec {i}: {spec['side']}")

        if spec["side"] == "front":
            prompt = build_front_prompt(spec)
            bg_url = spec["background"]
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
        poses = FRONT_POSES
        ref = REF_FRONT
        bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)
        scene_data = {"scene": "", "light": ""}
    else:
        poses = BACK_POSES
        ref = REF_BACK
        bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)
        scene_data = {"scene": "", "light": "soft warm evening light"}

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
        bg_url = bg
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
