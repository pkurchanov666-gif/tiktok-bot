import os
import time
import random
import requests
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

SAVE_DIR = "generations"
MAX_PROMPT_LENGTH = 2700

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
    used_front_poses = set()
    used_back_poses = set()
    sides = ["back", "front", "back"]

    for side in sides:
        if side == "front":
            ref = REF_FRONT
            bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)
            available_poses = [p for p in FRONT_POSES if p not in used_front_poses]
            if not available_poses:
                used_front_poses.clear()
                available_poses = FRONT_POSES
            pose = random.choice(available_poses)
            used_front_poses.add(pose)
        else:
            ref = REF_BACK
            bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)
            available_poses = [p for p in BACK_POSES if p not in used_back_poses]
            if not available_poses:
                used_back_poses.clear()
                available_poses = BACK_POSES
            pose = random.choice(available_poses)
            used_back_poses.add(pose)

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
        "Ultra-realistic RAW 9:16 professional fashion photograph. "
        "Front view. Evening atmosphere. "

        "REFERENCES: "
        "IMAGE 1 is the subject. Use exact person, face, clothing, logo from IMAGE 1. "
        "IMAGE 2 is the background. Place subject into exact location from IMAGE 2. "
        "Do not redesign subject. Do not invent background. "

        "FRONT VIEW: "
        "Torso 100% front-facing to camera. "
        "Chest flat and fully visible. No side angles. "
        "Face visible exactly as IMAGE 1. "

        "LOGO: "
        "Chest logo from IMAGE 1 preserved exactly. "
        "Same size, position, proportions. Razor-sharp. No blur. No distortion. "
        "Key light on chest to enhance logo visibility. "

        "POSITIONING: "
        "Subject centered. Head to mid-thigh framing. "
        "Leaning against surface from IMAGE 2. "
        "Realistic contact shadows. Ground shadows. No floating. "
        f"Pose: {spec['pose']}. "

        "LIGHTING: "
        "Match exact lighting from IMAGE 2. "
        "Warm golden evening tones. Long shadows on ground. "
        "No studio flash. No mismatched shadows. "

        "HOODIE: "
        "Black hoodie as in IMAGE 1. Hood DOWN. Face visible. "
        "NO pocket. NO zipper. Smooth fabric. "

        "JEANS: "
        "Wide baggy black denim as in IMAGE 1. Heavy texture visible. "

        "QUALITY: "
        "4K. Sharp focus. Seamless integration. "
        "Real photograph. Not composite. Not CGI."
    )

    prompt += uid

    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = prompt[:MAX_PROMPT_LENGTH]

    logger.info(f"[PROMPT] FRONT: {len(prompt)} chars")
    return prompt


def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}"

    prompt = (
        "Ultra-realistic RAW 9:16 professional environmental photograph. "
        "Back view. Evening atmosphere. "

        "REFERENCES: "
        "IMAGE 1 is the subject. IMAGE 2 is the background location. "
        "Place subject from IMAGE 1 into exact location from IMAGE 2. "

        "HOOD MANDATORY: "
        "Hood MUST be UP covering head completely. No exceptions. "
        "Face completely hidden. Back view only. "

        "HANDS: "
        "NEVER touch hips, buttocks, lower back, waist. "
        "If walking: arms swing naturally. "
        "If standing: both hands adjusting hood near head. "

        "SCALE: "
        "Correct human scale relative to IMAGE 2 architecture. "
        "Normal adult 1.75m tall. Full body visible head to feet. "
        "Feet touching ground. Realistic shadows on ground. "

        "BACKGROUND: "
        "Exact location from IMAGE 2. Match perspective, depth, scale. "
        "Subject authentically part of environment. Not floating. "

        "LIGHTING: "
        "Match exact lighting from IMAGE 2. "
        "Warm golden evening tones. Long realistic shadows. "
        "No studio flash. No artificial lighting. "

        "CLOTHING: "
        "Black hoodie hood UP. Black wide baggy denim jeans. "
        "Heavy fabric texture visible. "

        "QUALITY: "
        "4K. Sharp focus throughout. Seamless integration. "
        "Real photograph at that location. Not CGI. Not composite. "

        f"Pose: {spec['pose']}."
    )

    prompt += uid

    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = prompt[:MAX_PROMPT_LENGTH]

    logger.info(f"[PROMPT] BACK: {len(prompt)} chars")
    return prompt


# ================= POLZA API =================

def submit_job(prompt, image_url, background_url=None):
    polza_key = os.getenv("POLZA_API_KEY")
    if not polza_key:
        raise Exception("POLZA_API_KEY not set")

    images = [{"type": "url", "data": image_url}]
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
        f"[POLZA] Submit -> model={MODEL_NAME} | "
        f"resolution={IMAGE_RESOLUTION} | "
        f"images_count={len(images)} | "
        f"image_1={images[0]['data']} | "
        f"image_2={images[1]['data'] if len(images) > 1 else 'НЕТ ФОНА'}"
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


async def poll_job(job_id, retry_count=0, max_retries=3):
    polza_key = os.getenv("POLZA_API_KEY")
    max_wait = 2400
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
                timeout=60
            )

            try:
                data = response.json()
            except Exception:
                logger.warning(f"[POLZA] Non-JSON: {response.text[:200]}")
                continue

            status = str(data.get("status", "")).lower()
            logger.info(f"[POLZA] Job {job_id}: waited {waited}s, status={status}")

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
    os.makedirs(SAVE_DIR, exist_ok=True)

    async with httpx.AsyncClient(timeout=600.0) as client:
        async with client.stream("GET", url) as response:
            if response.status_code != 200:
                raise Exception(f"Download error: {response.status_code}")

            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    logger.info(f"[DOWNLOAD] Saved: {path} ({size_mb:.1f} MB)")


# ================= GENERATION =================

async def generate_all_photos():
    specs = get_unique_specs()
    logger.info(f"[GENERATE] Starting {len(specs)} photos: {[s['side'] for s in specs]}")

    job_ids = []
    max_job_retries = 3

    for i, spec in enumerate(specs):
        logger.info(
            f"[GENERATE] Spec {i}: side={spec['side']} | "
            f"ref={spec['ref']} | bg={spec['background']}"
        )

        if spec["side"] == "front":
            prompt = build_front_prompt(spec)
        else:
            prompt = build_back_prompt(spec)

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

    logger.info(f"[GENERATE] Received {len(urls)} results")

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
        except Exception as e:
            logger.error(f"[DOWNLOAD] Index {index}: {e}")

    logger.info(f"[GENERATE] Final: {len(paths)}/{len(specs)} photos saved")
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
        pose = random.choice(available_poses)
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

    if side == "front":
        prompt = build_front_prompt(new_spec)
    else:
        prompt = build_back_prompt(new_spec)

    try:
        job_id = await asyncio.to_thread(submit_job, prompt, new_spec["ref"], bg)
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
