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
        "scene": "standing very close to black granite entrance of modern business center, "
                 "body near glass door, only part of door and handles visible, "
                 "interior barely seen through glass",
        "light": "soft diffused daylight, gentle reflections from granite and glass"
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

# ---------------- BACK SCENES (НАБЕРЕЖНАЯ И СОВРЕМЕННЫЕ ЗДАНИЯ) ----------------

BACK_SCENES = [
    {
        "scene": "walking along modern waterfront promenade, "
                 "person small in frame, contemporary residential tower with sharp glass facades, "
                 "sleek metal railings along promenade, polished stone pavement with visible texture, "
                 "water view on one side, modern architecture on other side, clean minimalist design",
        "light": "soft natural daylight, sharp detailed light across entire waterfront"
    },
    {
        "scene": "walking on waterfront plaza near modern residential building, "
                 "person small in frame, contemporary tower with sharp window grid pattern, "
                 "clean stone pavement with visible lines, modern metal railings, "
                 "water and sky visible, contemporary design aesthetic",
        "light": "soft diffused daylight, sharp detailed illumination across plaza and building"
    },
    {
        "scene": "walking along modern waterfront promenade beside tall glass building, "
                 "person small in frame, sleek contemporary residential tower with sharp reflections, "
                 "polished pavement stretches along water, metal railings with sharp details, "
                 "water view and urban architecture, modern minimalist setting",
        "light": "soft natural daylight, sharp detailed light across waterfront"
    },
    {
        "scene": "walking on pedestrian passage along modern building facade, "
                 "person small in frame, contemporary glass and steel building with sharp window details, "
                 "clean polished pavement with visible texture, metal railings clearly visible, "
                 "modern minimalist architecture, urban professional setting",
        "light": "soft diffused daylight, sharp detailed illumination across passage"
    },
    {
        "scene": "walking along waterfront next to contemporary residential tower, "
                 "person small in frame, modern building with sharp architectural details, "
                 "sleek metal railings separate waterfront, polished stone ground with texture, "
                 "water reflections and clean urban design, contemporary aesthetic",
        "light": "soft natural daylight, sharp detailed light across waterfront area"
    },
    {
        "scene": "walking on modern plaza beside tall contemporary office building, "
                 "person small in frame, glass facade with sharp window reflections, "
                 "clean pavement stretches with visible lines and texture, metal railings sharp, "
                 "contemporary urban architecture, minimalist design",
        "light": "soft natural daylight, sharp detailed illumination across plaza"
    },
    {
        "scene": "walking along elevated waterfront promenade beside modern tower, "
                 "person small in frame, contemporary residential building with sharp wall panels, "
                 "polished pavement with clear texture, modern metal railings with reflections, "
                 "water view and sky, clean professional urban setting",
        "light": "soft diffused daylight, sharp detailed light across waterfront"
    },
    {
        "scene": "walking on pedestrian area along contemporary glass building, "
                 "person small in frame, sleek modern architecture with sharp facade details, "
                 "polished ground pavement with visible texture, clean urban design, "
                 "metal railings and architectural elements sharp and defined, waterfront view",
        "light": "soft natural daylight, sharp detailed illumination across entire area"
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

    "leaning naturally, both hands resting on thighs, "
    "shoulders relaxed and confident",

    "leaning naturally, right hand resting on hip, "
    "left hand resting on upper thigh",

    "leaning naturally, right hand in relaxed position along outer thigh, "
    "left hand resting on hip",

    "leaning naturally, left hand in relaxed position along outer thigh, "
    "right hand resting on hip",

    "leaning naturally, right hand resting on hip, "
    "left hand resting on upper thigh, chin slightly down"
]

BACK_POSES = [
    "standing facing away, both hands resting at sides naturally, "
    "arms relaxed",

    "standing facing away, right hand resting on outer thigh, "
    "left arm relaxed at side",

    "standing facing away, left hand resting on outer thigh, "
    "right arm relaxed at side",

    "walking away, both arms moving naturally with stride, "
    "shoulders relaxed",

    "walking away, right arm swinging naturally with stride, "
    "left arm at side",

    "walking away, left arm swinging naturally with stride, "
    "right arm at side",

    "standing facing away, both hands resting on outer thighs, "
    "posture confident and relaxed",

    "standing facing away, hands at sides naturally, "
    "shoulders back slightly",

    "walking away, both arms in natural movement with stride, "
    "head facing forward",

    "walking away with slight turn, arms moving naturally, "
    "relaxed confident posture"
]


# ---------------- SPEC ----------------

def get_unique_specs():
    specs = []
    used_scenes = set()
    used_poses = set()
    sides = ["back", "front", "back"]

    for side in sides:
        if side == "front":
            scenes = FRONT_SCENES
            poses = FRONT_POSES
            ref = REF_FRONT
        else:
            scenes = BACK_SCENES
            poses = BACK_POSES
            ref = REF_BACK

        available_scenes = [s for s in scenes if s["scene"][:50] not in used_scenes]
        if not available_scenes:
            available_scenes = scenes
        scene_data = random.choice(available_scenes)
        used_scenes.add(scene_data["scene"][:50])

        available_poses = [p for p in poses if p not in used_poses]
        if not available_poses:
            available_poses = poses
        pose = random.choice(available_poses)
        used_poses.add(pose)

        specs.append({
            "side": side,
            "scene": scene_data["scene"],
            "light": scene_data["light"],
            "pose": pose,
            "seed": random.randint(100000, 999999),
            "ref": ref
        })

    return specs


# ---------------- FRONT PROMPT ----------------

def build_front_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic 9:16 professional fashion photograph. "
        "Front facing shot. "
        "Sony A7R V, 35mm lens, f/4, ISO 200. "
        "Camera at eye level, 1.5 meters from subject. "
        "Framing from head to knees. Subject 70-75 percent of frame. "

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
        "No front pocket, no kangaroo pouch, no zipper. "
        "Only the chest logo visible on front. "

        "Sharp focus throughout - subject and background equally sharp. "
        "No blur, no bokeh. One unified photograph. "

        "Subject leans or stands against environment naturally. "
        "Visible contact with surface: wall, car, or railing. "
        "Not floating. Part of the location. "

        "Black wide-leg denim, heavy texture visible. "

        "Hands visible, not touching hood or face. "
        "Hands rest naturally on thighs or at sides. "
        "Natural confident posture. "

        "Background sharp and detailed. Not blurred. "
        "Architecture, pavement, car details all clear. "

        f"Lighting: {spec['light']}. "
        "Soft natural light, no harsh shadows, no flash. "
        "Light enhances logo visibility and detail. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "
    ) + uid


# ---------------- BACK PROMPT ----------------

def build_back_prompt(spec):
    uid = f" UID:{spec['seed']}-{random.random()}"

    return (
        "Ultra-realistic 9:16 professional photograph. "
        "Back view shot on modern waterfront and contemporary buildings. "
        "Sony A7R V, 35mm, f/4, ISO 400. "
        "Camera at 1.6m height, straight forward, parallel to ground. "

        "Camera 25-30 meters from subject. "
        "Full body visible, feet on ground. "
        "Ground visible 30 percent of frame below feet. "
        "Subject 8-12 percent of frame height - small but clear. "
        "Environment dominates, subject is focal point. "

        "SHARP FOCUS THROUGHOUT: "
        "Sharp focus everywhere - foreground, subject, background all equally sharp. "
        "f/4 depth of field ensures everything is in perfect focus. "
        "No blur, no bokeh, no soft areas. Unified sharp photograph. "

        "BACKGROUND DETAIL: "
        "Every element must be sharp and detailed: "
        "- Building facades: sharp glass windows with reflections, wall panels clearly visible "
        "- Pavement: polished stone or concrete with visible texture and lines "
        "- Railings: metal railings with sharp reflections and architectural details "
        "- Water feature: waterfront, water reflections, edge definition all sharp "
        "- Architecture: contemporary design elements, lines and details crisp "
        "- Sky: natural atmospheric detail sharp "

        "Subject: black hoodie, hood down, back view. "
        "Black wide-leg denim with visible texture. "
        "Hands relaxed at sides or on thighs. "

        f"Lighting: {spec['light']}. "
        "Soft natural light, even across entire scene, no harsh shadows. "
        "Light illuminates every detail equally. "

        "Setting: Modern waterfront promenade or contemporary building plaza. "
        "Sleek contemporary architecture with glass and steel. "
        "Clean urban aesthetic, professional environment. "

        f"Scene: {spec['scene']}. "
        f"Pose: {spec['pose']}. "

        "Professional environmental photography. "
        "Background rendered with extreme clarity and definition. "
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
                f"[POLZA] job={job_id} waited={waited}s status={status} keys={list(data.keys())}"
            )

            if status in {"failed", "error", "canceled", "cancelled"}:
                error_msg = str(data.get("error", {}))
                logger.error(f"[POLZA] Job failed: {error_msg}")
                
                if "BAD_GATEWAY" in error_msg and retry_count < max_retries:
                    logger.info(f"[POLZA] Retrying job (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(10)
                    return None
                
                raise Exception(f"Polza job failed: {data}")

            url = extract_url(data)
            if url:
                logger.info(f"[POLZA] url: {url}")
                return url

        except Exception as e:
            if "failed" in str(e).lower():
                raise
            logger.warning(f"[POLZA] poll error job={job_id}: {e}")

    raise Exception(f"Timeout {max_wait}s. Last: {last_data}")


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
        prompt = build_front_prompt(spec) if spec["side"] == "front" else build_back_prompt(spec)
        
        job_id = None
        for attempt in range(max_job_retries):
            try:
                job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
                if job_id:
                    break
            except Exception as e:
                logger.warning(f"[SUBMIT] Attempt {attempt + 1} failed: {e}")
                if attempt < max_job_retries - 1:
                    await asyncio.sleep(5)
        
        if not job_id:
            logger.error(f"[SUBMIT] Failed to submit job for spec {i} after {max_job_retries} attempts")
            continue
        
        job_ids.append(job_id)
        if i < len(specs) - 1:
            await asyncio.sleep(5)

    urls = await asyncio.gather(*[poll_job(job_id) for job_id in job_ids], return_exceptions=True)

    paths = []
    for index, url in enumerate(urls):
        if isinstance(url, Exception):
            logger.error(f"[DOWNLOAD] Failed to get URL for index {index}: {url}")
            continue
        if not url:
            logger.warning(f"[DOWNLOAD] No URL for index {index}")
            continue
        
        path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_{index}.png")
        try:
            await download_image(url, path)
            paths.append(path)
        except Exception as e:
            logger.error(f"[DOWNLOAD] Failed to download image {index}: {e}")

    return paths, specs, list(urls)


async def regenerate_photo(index, current_specs):
    """Регенерирует фото с тем же персонажем, но другой сценой/позой"""
    
    old_spec = current_specs[index]
    side = old_spec["side"]
    old_scene = old_spec.get("scene", "")[:50]
    old_pose = old_spec.get("pose", "")

    if side == "front":
        scenes = FRONT_SCENES
        poses = FRONT_POSES
        ref = REF_FRONT
    else:
        scenes = BACK_SCENES
        poses = BACK_POSES
        ref = REF_BACK

    # Выбираем другую сцену
    available_scenes = [s for s in scenes if s["scene"][:50] != old_scene]
    if not available_scenes:
        available_scenes = scenes
    scene_data = random.choice(available_scenes)

    # Выбираем другую позу
    available_poses = [p for p in poses if p != old_pose]
    if not available_poses:
        available_poses = poses
    pose = random.choice(available_poses)

    spec = {
        "side": side,
        "scene": scene_data["scene"],
        "light": scene_data["light"],
        "pose": pose,
        "seed": old_spec["seed"],
        "ref": ref
    }

    if side == "front":
        prompt = build_front_prompt(spec)
    else:
        prompt = build_back_prompt(spec)
    
    logger.info(f"[REGEN] index={index}, seed={spec['seed']}, new_scene={scene_data['scene'][:40]}, new_pose={pose[:40]}")
    
    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    path = os.path.join(SAVE_DIR, f"ai_{int(time.time() * 1000)}_regen_{index}.png")
    await download_image(url, path)

    current_specs[index] = spec
    
    return path, spec, url
