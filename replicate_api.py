import os
import time
import random
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

SAVE_DIR = "generations"
MAX_PROMPT_LENGTH = 4900

# ================= MODEL SETTINGS =================

MODEL_NAME = "google/gemini-3.1-flash-image-preview"
IMAGE_RESOLUTION = "4K"
ASPECT_RATIO = "9:16"
OUTPUT_FORMAT = "png"

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

# ================= FRONT POSES =================

FRONT_POSES = [
    "leaning naturally, right fingertips resting lightly on hood fabric near temple, left hand resting loosely on upper thigh, relaxed elbows, torso 100% front-facing to camera",
    "leaning naturally, both hands resting lightly on both sides of hood, chin slightly down, torso 100% front-facing, shoulders relaxed against surface",
    "leaning naturally, left fingertips resting lightly on hood fabric near cheek, right arm relaxed along outer thigh, torso 100% front-facing to camera",
    "leaning naturally, right hand resting flat on upper thigh, left arm relaxed at side, balanced posture, torso 100% front-facing to camera",
    "leaning naturally, right hand resting on back of head, left arm relaxed along outer thigh, torso 100% front-facing to camera",
    "leaning naturally, left hand resting on back of head, right arm relaxed along outer thigh, torso 100% front-facing to camera",
    "leaning naturally, both hands relaxed near hood opening, shoulders against surface, torso 100% front-facing to camera",
    "leaning naturally, right hand resting on back of head, left hand resting on upper thigh, chin slightly down, torso 100% front-facing to camera"
]

# ================= BACK POSES =================

BACK_POSES = [
    "walking away, hood UP covering head completely, both arms swinging naturally with stride, relaxed walking pace, back view only",
    "walking away, hood UP covering head completely, right hand behind head on neck above shoulders, left arm swinging naturally, back view only",
    "walking away, hood UP covering head completely, left hand behind head on neck above shoulders, right arm swinging naturally, back view only",
    "standing facing away, hood UP covering head completely, right hand raised adjusting hood near head, left hand touching hood fabric, back view only",
    "standing facing away, hood UP covering head completely, both hands raised adjusting hood, fingers touching hood fabric near head, back view only"
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
    sides = ["back", "front", "back"]

    used_front_poses = set()
    used_back_poses = set()

    for side in sides:
        if side == "front":
            ref = REF_FRONT
            bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)
            pose_list = FRONT_POSES
            used_poses = used_front_poses
        else:
            ref = REF_BACK
            bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)
            pose_list = BACK_POSES
            used_poses = used_back_poses

        available_poses = [p for p in pose_list if p not in used_poses]
        if not available_poses:
            available_poses = pose_list
            used_poses.clear()

        pose = random.choice(available_poses)
        used_poses.add(pose)

        specs.append({
            "side": side,
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
        "ACT AS A PROFESSIONAL FASHION PHOTOGRAPHER. HIGH-END EDITORIAL STYLE. "
        "STRICT TWO-REFERENCE SYSTEM: "
        "IMAGE 1 is the MASTER SUBJECT REFERENCE - use the exact person, face, clothing, chest logo, fabric texture and body proportions from IMAGE 1. "
        "IMAGE 2 is the MASTER ENVIRONMENT REFERENCE - use the exact architecture, background, pavement, spatial layout, perspective and lighting from IMAGE 2. "
        "DO NOT redesign the subject. DO NOT invent a new background. "

        "COMPOSITION: "
        "9:16 vertical portrait. "
        "Subject fills 70 to 75 percent of the frame vertically. "
        "Framing from head to mid-thigh. "
        "Natural eye-level perspective. "

        "CRITICAL BODY RULE: "
        "The torso must be rotated 100 percent front-facing toward the camera. "
        "The chest must remain perfectly flat and fully visible. "
        "The chest logo from IMAGE 1 must be razor-sharp, undistorted, centered, and perfectly readable. "
        "No perspective warping on the logo. No blur. No redesign. "

        "PHYSICAL INTERACTION: "
        "The subject from IMAGE 1 is physically placed inside the environment from IMAGE 2. "
        "The lower back and hip lean naturally against the architectural surface from IMAGE 2. "
        "Realistic contact shadows and ambient occlusion where the body touches the surface. "
        "Realistic ground contact shadows under the feet. "
        "No floating. No cutout look. No pasted-on effect. "
        f"Pose: {spec['pose']}. "

        "LIGHTING: "
        "Match the exact light direction, color temperature and ambient mood from IMAGE 2. "
        "Add a subtle controlled key light focused on the chest to enhance logo clarity. "
        "Natural bounce light from pavement and nearby surfaces. "
        "No studio flash. No mismatched shadows. "

        "TEXTURE AND OPTICS: "
        "iPhone 17 Pro Max, 24mm lens, f/1.7, Smart HDR-5, 4K resolution. "
        "Ultra-detailed fabric micro-texture from IMAGE 1. "
        "Realistic cotton grain, denim weave, natural folds, premium stitching. "
        "No plastic skin. No CGI look. No artificial oversharpening. "

        "FINAL RESULT: "
        "One seamless photorealistic luxury editorial photograph. "
        "The subject from IMAGE 1 naturally integrated into the environment from IMAGE 2. "
        "Magazine quality. Premium streetwear campaign aesthetic."
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
        "IMAGE 1 is the SUBJECT REFERENCE. "
        "IMAGE 2 is the BACKGROUND REFERENCE. "
        "Integrate the subject from IMAGE 1 into the exact location from IMAGE 2. "

        "HOOD MANDATORY - CRITICAL: "
        "Hood MUST be UP on head, completely covering head. "
        "Hood fabric clearly visible covering head and upper back. "
        "Face completely hidden. BACK VIEW ONLY. No exceptions. "

        "HAND AND ARM POSITIONING - CRITICAL: "
        "Hands must NEVER touch hips, buttocks, lower back, hip area or waist level. "
        "If walking: arms swing naturally OR one hand behind head at neck. "
        "If standing: both hands actively adjusting hood near head. "
        f"Pose: {spec['pose']}. "

        "HUMAN SCALE - CRITICAL: "
        "Subject at correct realistic human scale relative to the background from IMAGE 2. "
        "Full body visible from head to feet. "
        "Feet must clearly touch the ground surface from IMAGE 2. "

        "BACKGROUND INTEGRATION - CRITICAL: "
        "Use the exact environment from IMAGE 2. "
        "Match perspective, depth, scale and atmosphere from IMAGE 2 precisely. "
        "Subject must feel naturally grounded in the scene. "
        "No floating. No pasted-on look. "

        "LIGHTING - CRITICAL: "
        "Match exact lighting conditions, color temperature and light direction from IMAGE 2. "
        "Render realistic evening or golden hour atmosphere. "
        "Realistic ground contact shadows under the feet. "
        "No studio flash. No artificial lighting. "

        "QUALITY: "
        "4K resolution. Sharp focus throughout. "
        "One unified realistic photograph. "
        "Not CGI. Not composite. Looks like a real photo taken at that location."
    )

    prompt += uid

    if len(prompt) > MAX_PROMPT_LENGTH:
        logger.warning(f"[PROMPT] BACK too long: {len(prompt)} > {MAX_PROMPT_LENGTH}")
        prompt = prompt[:MAX_PROMPT_LENGTH]

    logger.info(f"[PROMPT] BACK: {len(prompt)}/{MAX_PROMPT_LENGTH} chars")
    return prompt


# ================= POLZA API =================

def submit_job(prompt, subject_url, background_url=None):
    polza_key = os.getenv("POLZA_API_KEY")
    if not polza_key:
        raise Exception("POLZA_API_KEY not set")

    images = [{"type": "url", "data": subject_url}]
    if background_url:
        images.append({"type": "url", "data": background_url})

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "aspect_ratio": ASPECT_RATIO,
            "image_resolution": IMAGE_RESOLUTION,
            "output_format": OUTPUT_FORMAT,
            "images": images
        },
        "async": True
    }

    logger.info(
        f"[POLZA] Submit -> model={MODEL_NAME} | resolution={IMAGE_RESOLUTION} | "
        f"images_count={len(images)} | has_background={bool(background_url)}"
    )

    response = requests.post(
        "https://polza.ai/api/v1/media",
        headers={
            "Authorization": f"Bearer {polza_key}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
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


async def poll_job(job_id):
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
            logger.info(f"[POLZA] Job {job_id}: waited={waited}s status={status}")

            if status in {"failed", "error", "canceled", "cancelled"}:
                error_msg = str(data.get("error", {}))
                logger.error(f"[POLZA] Job failed: {error_msg}")
                raise Exception(f"Polza job failed: {data}")

            url = extract_url(data)
            if url:
                logger.info(f"[POLZA] Result URL: {url}")
                return url

        except Exception as e:
            if "failed" in str(e).lower():
                raise
            logger.warning(f"[POLZA] Poll error: {e}")

    raise Exception(f"Timeout after {max_wait}s")


async def download_image(url, path):
    response = await asyncio.to_thread(requests.get, url, timeout=120)
    response.raise_for_status()
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
        logger.info(f"[GENERATE] Spec {i}: side={spec['side']} bg={spec['background']}")

        prompt = build_front_prompt(spec) if spec["side"] == "front" else build_back_prompt(spec)
        bg_url = spec["background"]

        job_id = None
        for attempt in range(max_job_retries):
            try:
                job_id = await asyncio.to_thread(
                    submit_job, prompt, spec["ref"], bg_url
                )
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

    urls = await asyncio.gather(
        *[poll_job(job_id) for job_id in job_ids],
        return_exceptions=True
    )

    paths = []
    final_urls = []

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
            final_urls.append(url)
            logger.info(f"[DOWNLOAD] Saved index {index}: {path}")
        except Exception as e:
            logger.error(f"[DOWNLOAD] Index {index}: {e}")

    logger.info(f"[GENERATE] Done: {len(paths)}/{len(specs)} photos saved")
    return paths, specs, final_urls


async def regenerate_photo(index, current_specs):
    logger.info(f"[REGEN] Photo {index}")

    if index < 0 or index >= len(current_specs):
        raise Exception(f"Invalid index {index}")

    old_spec = current_specs[index]
    side = old_spec["side"]

    if side == "front":
        ref = REF_FRONT
        bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)
        available_poses = [p for p in FRONT_POSES if p != old_spec.get("pose")]
        if not available_poses:
            available_poses = FRONT_POSES
    else:
        ref = REF_BACK
        bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)
        available_poses = [p for p in BACK_POSES if p != old_spec.get("pose")]
        if not available_poses:
            available_poses = BACK_POSES

    pose = random.choice(available_poses)

    new_spec = {
        "side": side,
        "pose": pose,
        "seed": random.randint(100000, 999999),
        "ref": ref,
        "background": bg
    }

    prompt = build_front_prompt(new_spec) if side == "front" else build_back_prompt(new_spec)

    try:
        job_id = await asyncio.to_thread(submit_job, prompt, ref, bg)
        logger.info(f"[REGEN] Job submitted: {job_id}")
    except Exception as e:
        logger.error(f"[REGEN] Submit failed: {e}")
        raise

    try:
        url = await poll_job(job_id)
        if not url:
            raise Exception("No URL returned")
    except Exception as e:
        logger.error(f"[REGEN] Poll failed: {e}")
        raise

    path = os.path.join(SAVE_DIR, f"ai_regen_{int(time.time() * 1000)}_{index}.png")
    try:
        await download_image(url, path)
        logger.info(f"[REGEN] Saved: {path}")
    except Exception as e:
        logger.error(f"[REGEN] Download failed: {e}")
        raise

    current_specs[index] = new_spec
    return path, new_spec, url
