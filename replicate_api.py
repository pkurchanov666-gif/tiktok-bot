import os
import time
import random
import requests
import asyncio
import logging

logger = logging.getLogger(__name__)

SAVE_DIR = "generations"
MAX_PROMPT_LENGTH = 4900

# ================= POLZA SETTINGS =================

MODEL_NAME = "black-forest-labs/flux.2-pro"
IMAGE_RESOLUTION = "4K"   # было 1K, теперь 4K
ASPECT_RATIO = "9:16"

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
    "https://i.ibb.co/0R04rmYz/5219908140244082497.jpg",
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
    "https://i.ibb.co/gMqqyZC1/5188269594370577198.jpg",
]

used_backgrounds_front = set()
used_backgrounds_back = set()

# ================= FRONT POSES =================
# ТОЛЬКО для фото СПЕРЕДИ

FRONT_POSES = [
    "natural front-facing editorial pose, torso turned fully toward camera, arms relaxed down by the sides, one leg slightly forward, body lightly leaning against the background structure",
    "front-facing confident pose, torso square to camera, one hand relaxed near upper thigh, the other arm relaxed naturally, lower back leaning lightly against the surface",
    "front-facing relaxed pose, torso fully visible and flat to camera, shoulders relaxed, one leg slightly advanced, subtle contact with the structure behind the body",
    "front-facing fashion pose, chest area fully unobstructed, both arms relaxed near the body, slight lean through lower back and hip into the architectural surface",
]

# ================= BACK POSES =================
# ТОЛЬКО для фото СЗАДИ

BACK_POSES = [
    "walking away, hood UP covering head completely, both arms swinging naturally with stride, relaxed walking pace, natural movement",
    "walking away, hood UP covering head completely, right hand behind head on neck above shoulders, left arm swinging naturally with stride, natural walking motion",
    "walking away, hood UP covering head completely, left hand behind head on neck above shoulders, right arm swinging naturally with stride, natural walking motion",
    "standing facing away, hood UP covering head completely, right hand raised adjusting hood near head, left hand also raised touching hood fabric on other side, active positioning",
    "standing facing away, hood UP covering head completely, both hands raised adjusting hood, fingers touching hood fabric near head and shoulders, engaged posture",
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


def build_specs_sequence():
    # порядок генерации
    return ["back", "front", "back"]


def get_unique_specs():
    specs = []

    used_front_poses = set()
    used_back_poses = set()

    for side in build_specs_sequence():
        if side == "front":
            ref = REF_FRONT
            bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)

            available_poses = [p for p in FRONT_POSES if p not in used_front_poses]
            if not available_poses:
                available_poses = FRONT_POSES
                used_front_poses.clear()

            pose = random.choice(available_poses)
            used_front_poses.add(pose)

        else:
            ref = REF_BACK
            bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)

            available_poses = [p for p in BACK_POSES if p not in used_back_poses]
            if not available_poses:
                available_poses = BACK_POSES
                used_back_poses.clear()

            pose = random.choice(available_poses)
            used_back_poses.add(pose)

        specs.append({
            "side": side,
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": ref,
            "background": bg,
        })

    return specs

# ================= PROMPTS =================

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}"

    prompt = (
        "Ultra-realistic RAW professional fashion editorial, 9:16 vertical composition. "
        "STRICT TWO-REFERENCE GENERATION. "
        "Reference Photo 1 is the subject. "
        "Reference Photo 2 is the background and environment. "

        "CRITICAL REFERENCE LOCK: "
        "Use the exact person from Reference Photo 1. "
        "Use the exact location, architecture, perspective, pavement, framing logic, lighting mood and spatial layout from Reference Photo 2. "
        "Do not redesign the subject. "
        "Do not redesign the environment. "
        "Do not invent a new background. "

        "COMPOSITION: "
        "Strict front-facing close fashion shot. "
        "Frame from head to mid-thigh. "
        "Subject occupies approximately 70 to 75 percent of frame height. "
        "Natural eye-level perspective. "
        "Professional editorial composition. "

        "BODY POSITIONING AND INTERACTION: "
        "The subject from Reference Photo 1 is physically placed inside the exact environment from Reference Photo 2. "
        "The body must interact naturally with the background structure from Reference Photo 2. "
        "The lower back and hip lightly lean against the architectural or structural surface visible in Reference Photo 2. "
        "The torso must be rotated fully front-facing toward the camera. "
        "The chest plane must remain flat, centered, unobstructed and clearly visible. "
        f"Pose: {spec['pose']}. "

        "LOGO PRIORITY - CRITICAL: "
        "The chest logo from Reference Photo 1 must remain exact in size, shape, placement, proportions and visual weight. "
        "The logo must be the sharpest area of the image. "
        "No perspective skew, no warping, no stretching, no blur, no redesign. "
        "The logo must remain fully readable and centered on the chest. "

        "LIGHT MATCHING - CRITICAL: "
        "Match the exact light direction, color temperature, ambience, exposure mood and background lighting from Reference Photo 2. "
        "Use the environmental light of Reference Photo 2 as the main base light. "
        "Add only a subtle controlled professional key light on the chest area to improve logo clarity while preserving realism. "
        "Add realistic contact shadows where the body touches the surface from Reference Photo 2. "
        "Add realistic ground contact shadows under the feet. "
        "Natural bounce light from pavement and nearby surfaces. "
        "No studio flash look. "
        "No mismatched shadows. "
        "No contradictory lighting. "

        "TEXTURE AND MATERIAL PHYSICS: "
        "Preserve original fabric detail from Reference Photo 1. "
        "Visible cotton grain, realistic textile density, natural folds, realistic denim weave, realistic stitching, realistic shadow falloff. "
        "Clear material separation between matte clothing from Reference Photo 1 and environmental surfaces from Reference Photo 2. "
        "No plastic smoothing. "
        "No CGI look. "
        "No artificial oversharpening. "

        "CAMERA AND OPTICS: "
        "Shot on iPhone 17 Pro Max, 24mm equivalent lens, f/1.7 aperture, Smart HDR-5 look. "
        "Subject in critical sharp focus. "
        "Background from Reference Photo 2 remains clearly recognizable and structurally correct. "
        "No scale distortion. "
        "No warped verticals. "

        "FINAL RESULT: "
        "The final image must look like one real professional luxury editorial photograph made in the exact place from Reference Photo 2 "
        "with the exact subject from Reference Photo 1 seamlessly integrated into that environment. "
        "Photorealistic, premium, ultra-detailed, realistic, high-end fashion campaign quality."
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
        "Reference Photo 1 is the subject. "
        "Reference Photo 2 is the background location. "
        "Back view shot integrated into provided background location. "
        "Evening or golden hour time of day. Realistic warm evening atmosphere. "

        "HOOD MANDATORY - CRITICAL: "
        "Hood MUST be UP on head, completely covering head. "
        "Hood fabric clearly visible covering head and upper back. "
        "Face completely hidden, BACK VIEW ONLY. "

        "HAND AND ARM POSITIONING - CRITICAL: "
        "Hands must NEVER touch hips, buttocks, lower back, hip area, back pockets or waist level. "
        "If walking: arms swing naturally OR one hand behind head at neck above shoulders. "
        "If standing: both hands actively adjusting hood near head. "
        f"Pose: {spec['pose']}. "

        "HUMAN SCALE AND PROPORTIONS - CRITICAL: "
        "Subject must be at correct realistic human scale relative to the background architecture. "
        "Not too large. Not too small. "
        "Full body visible from head to feet. "
        "Feet must clearly touch the ground. "

        "BACKGROUND INTEGRATION - CRITICAL: "
        "Use the exact environment from Reference Photo 2. "
        "Match perspective, depth, scale, architecture and atmosphere from Reference Photo 2. "
        "The subject must feel naturally grounded in the scene. "
        "No pasted-on look. No floating. "

        "LIGHT MATCHING - CRITICAL: "
        "Match the exact lighting conditions, color temperature and light direction from Reference Photo 2. "
        "Render realistic evening shadows and ground contact shadows. "
        "No studio flash. No artificial mismatched lighting. "

        "PHOTOGRAPHY QUALITY - CRITICAL: "
        "Sharp focus throughout image. "
        "Realistic seamless integration. "
        "Looks like one real photograph taken at that location. "
        "Not CGI. Not composite. Real photo."
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
        raise Exception("POLZA_API_KEY not found")

    images = [{"type": "url", "data": subject_url}]
    if background_url:
        images.append({"type": "url", "data": background_url})

    payload = {
        "model": MODEL_NAME,
        "input": {
            "prompt": prompt,
            "aspect_ratio": ASPECT_RATIO,
            "image_resolution": IMAGE_RESOLUTION,
            "images": images
        },
        "async": True
    }

    logger.info(
        f"[POLZA] Submit payload -> model={MODEL_NAME}, resolution={IMAGE_RESOLUTION}, "
        f"images_count={len(images)}, has_background={bool(background_url)}"
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
            logger.info(f"[POLZA] Job {job_id}: waited {waited}s, status={status}")

            if status in {"failed", "error", "canceled", "cancelled"}:
                error_msg = str(data.get("error", {}))
                logger.error(f"[POLZA] Job failed: {error_msg}")

                if "BAD_GATEWAY" in error_msg and retry_count < max_retries:
                    logger.info("[POLZA] Retrying after BAD_GATEWAY...")
                    await asyncio.sleep(10)
                    return None

                raise Exception(f"Polza job failed: {data}")

            url = extract_url(data)
            if url:
                logger.info(f"[POLZA] Generated URL: {url}")
                return url

        except Exception as e:
            if "failed" in str(e).lower():
                raise
            logger.warning(f"[POLZA] Poll error: {e}")

    raise Exception(f"Timeout {max_wait}s")


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
        logger.info(f"[GENERATE] Processing spec {i}: {spec['side']}")

        if spec["side"] == "front":
            prompt = build_front_prompt(spec)
        else:
            prompt = build_back_prompt(spec)

        bg_url = spec["background"]

        job_id = None
        for attempt in range(max_job_retries):
            try:
                job_id = await asyncio.to_thread(
                    submit_job,
                    prompt,
                    spec["ref"],
                    bg_url
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

    urls = await asyncio.gather(*[poll_job(job_id) for job_id in job_ids], return_exceptions=True)
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
            logger.info(f"[DOWNLOAD] Saved index {index}")
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
        bg = get_random_background(FRONT_BACKGROUNDS, used_backgrounds_front)

        available_poses = [p for p in FRONT_POSES if p != old_spec.get("pose")]
        if not available_poses:
            available_poses = FRONT_POSES

        pose = random.choice(available_poses)

        new_spec = {
            "side": side,
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": REF_FRONT,
            "background": bg
        }
        prompt = build_front_prompt(new_spec)

    else:
        bg = get_random_background(BACK_BACKGROUNDS, used_backgrounds_back)

        available_poses = [p for p in BACK_POSES if p != old_spec.get("pose")]
        if not available_poses:
            available_poses = BACK_POSES

        pose = random.choice(available_poses)

        new_spec = {
            "side": side,
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": REF_BACK,
            "background": bg
        }
        prompt = build_back_prompt(new_spec)

    try:
        job_id = await asyncio.to_thread(
            submit_job,
            prompt,
            new_spec["ref"],
            new_spec["background"]
        )
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
