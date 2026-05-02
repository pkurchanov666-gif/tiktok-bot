import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

SCENES = [
    "ordinary evening city street with realistic ambient light",
    "simple underground parking with natural ceiling lights",
    "quiet apartment hallway with warm household lighting",
    "hotel corridor with normal practical lights and soft shadows",
    "building entrance at night with realistic street lamps",
    "parking lot near a shopping center in the evening",
    "coffee shop entrance at night with neutral warm lighting",
    "residential courtyard at dusk with natural shadows",
    "office lobby with simple interior light",
    "rooftop parking at sunset with neutral natural tones",
    "stairwell with natural window light coming from above",
    "shopping mall entrance at night, glass doors behind",
    "quiet city alley at evening with distant streetlights",
    "metro station exit area in the evening",
    "basketball court edge at dusk, ambient sky light",
]

LIGHT_DETAILS = [
    "natural evening ambient light with soft logical shadows",
    "neutral warm street lighting with believable shadows",
    "ordinary night lighting with realistic exposure",
    "soft mixed practical lighting with natural contrast",
    "subtle urban evening light without dramatic effects",
]

BACKGROUND_DETAILS = [
    "realistic background depth and natural perspective",
    "ordinary city details softly blurred in the background",
    "subtle reflections on pavement or glass",
    "natural environmental shadows and realistic depth",
    "normal lived-in urban atmosphere",
]

CROP_STYLES = [
    "vertical waist-up composition",
    "vertical mid-torso composition",
    "vertical chest-to-head framing",
    "vertical upper-body framing",
]

CAMERA_FEELS = [
    "shot on a quality mirrorless camera",
    "shot on a modern high-end phone camera",
    "captured like a real spontaneous street photo",
    "shot casually but sharply with natural realism",
]

ANGLES_FRONT = [
    "direct frontal view, eye level",
    "slight low angle frontal",
    "three-quarters left front",
    "three-quarters right front",
    "slight top-down frontal",
]

ANGLES_BACK = [
    "direct back view",
    "three-quarters back left",
    "three-quarters back right",
    "slight low angle back view",
    "slight top-down back view",
]

FRONT_POSES = [
    "both hands holding the hood near the jawline, elbows clearly lifted outward, shoulders squared toward camera",
    "left hand gripping the hood edge near the temple, right forearm bent across lower torso, calm confident stance",
    "right hand gripping the hood edge near the cheek, left arm bent across torso, relaxed confident posture",
    "arms crossed firmly on chest, shoulders relaxed, subtle forward lean",
    "one hand touching chin thoughtfully, the other arm folded across body, composed stance",
    "one forearm resting across the lower chest, other hand raised near hood seam, assertive relaxed pose",
    "slight forward lean, one hand resting on upper thigh, the other hand touching hood near the neck",
    "semi-profile stance, one hand pulling hood slightly forward, other arm bent near waist",
    "leaning lightly against a wall, one hand touching the hood edge, the other arm bent across torso",
    "mid-step walk toward camera, one hand touching the hood edge, the other arm moving naturally",
]

BACK_POSES = [
    "back facing camera, one hand gripping the back of the hood, other arm relaxed close to torso",
    "back facing camera, both hands pulling the hood tighter around the head, elbows clearly raised",
    "walking away from camera, one hand touching the hood from behind, the other arm swinging naturally",
    "slow natural walk away from camera, arms moving naturally, hood fully up",
    "leaning with shoulder against wall, back fully visible, one hand adjusting hood",
    "three-quarters back stance, one hand touching the hood seam near the neck, shoulders slightly angled",
    "standing with back to camera, head slightly lowered, both arms active near the hood",
    "back fully visible, both arms raised near hood sides, elbows clearly visible, body stable",
    "moving away in a three-quarters back stance, one arm active near hood, body clearly in motion",
    "shoulder-led back view, hood fully up, one hand near hood, the other arm low and natural",
]

# Глобальное хранилище использованных поз
USED_FRONT_POSES = set()
USED_BACK_POSES = set()


def reset_used_poses():
    global USED_FRONT_POSES, USED_BACK_POSES
    USED_FRONT_POSES = set()
    USED_BACK_POSES = set()


def get_unused_front_pose():
    global USED_FRONT_POSES

    available = [i for i in range(len(FRONT_POSES)) if i not in USED_FRONT_POSES]

    if not available:
        USED_FRONT_POSES = set()
        available = list(range(len(FRONT_POSES)))

    idx = random.choice(available)
    USED_FRONT_POSES.add(idx)

    return idx, FRONT_POSES[idx]


def get_unused_back_pose():
    global USED_BACK_POSES

    available = [i for i in range(len(BACK_POSES)) if i not in USED_BACK_POSES]

    if not available:
        USED_BACK_POSES = set()
        available = list(range(len(BACK_POSES)))

    idx = random.choice(available)
    USED_BACK_POSES.add(idx)

    return idx, BACK_POSES[idx]


def crop_watermark(path: str, crop_percent: float = 0.07):
    try:
        img = Image.open(path)
        w, h = img.size
        new_h = int(h * (1 - crop_percent))
        img = img.crop((0, 0, w, new_h))
        img.save(path)
    except Exception as e:
        print(f"Crop failed: {e}")


def build_spec(side):
    if side == "front":
        pose_idx, pose_text = get_unused_front_pose()
        return {
            "side": "front",
            "pose_idx": pose_idx,
            "pose": pose_text,
            "scene": random.choice(SCENES),
            "angle": random.choice(ANGLES_FRONT),
            "hood": random.choice(["hood up", "hood up", "hood down"]),
            "light_detail": random.choice(LIGHT_DETAILS),
            "background_detail": random.choice(BACKGROUND_DETAILS),
            "crop_style": random.choice(CROP_STYLES),
            "camera_feel": random.choice(CAMERA_FEELS),
            "seed": random.randint(100000, 999999),
            "ref": REF_FRONT,
        }
    else:
        pose_idx, pose_text = get_unused_back_pose()
        return {
            "side": "back",
            "pose_idx": pose_idx,
            "pose": pose_text,
            "scene": random.choice(SCENES),
            "angle": random.choice(ANGLES_BACK),
            "hood": "hood up",
            "light_detail": random.choice(LIGHT_DETAILS),
            "background_detail": random.choice(BACKGROUND_DETAILS),
            "crop_style": random.choice(CROP_STYLES),
            "camera_feel": random.choice(CAMERA_FEELS),
            "seed": random.randint(100000, 999999),
            "ref": REF_BACK,
        }


def build_prompt(spec):
    common = (
        "Ultra-realistic image-to-image fashion photo of the same person from the reference image. "
        "Keep the same face, same body shape, same proportions, same hoodie. "
        "Do not redesign the clothing. "
        "Hoodie has no pocket, no zipper, no extra stitching, no extra details. "
        "Strictly black wide-leg jeans, loose fit, baggy silhouette, deep solid black denim. "
        "Normal high-quality real photo, not a studio shoot, not editorial, not CGI, not overprocessed. "
        "No professional lighting setup. "
        "No neon colors. "
        "No cinematic grading. "
        f"{spec['camera_feel']}. "
        f"{spec['light_detail']}. "
        f"{spec['background_detail']}. "
        f"{spec['crop_style']}. "
        f"Scene: {spec['scene']}. "
        f"Pose must be exactly: {spec['pose']}. "
        f"Camera angle: {spec['angle']}. "
        f"Hood state: {spec['hood']}. "
        "Avoid generic straight standing. "
        "Avoid both arms hanging straight down. "
        "Natural fabric folds, realistic cotton texture, believable real-world shadows. "
    )

    if spec["side"] == "front":
        side_rules = (
            "FRONT shot. Use only the front design from Reference Image 2. "
            "Do not add any back print. "
            "Chest logo and text must be clear, sharp, readable, correctly placed. "
            "If the hood is up, the front print must still remain visible. "
        )
    else:
        side_rules = (
            "BACK shot. Use only the back design from Reference Image 1. "
            "Do not add any front logo. "
            "Person must NOT look at the camera. "
            "No face visible. "
            "Hood must always be up. "
            "Camera clearly faces the back. "
            "Back print fully visible and accurate. "
        )

    ending = (
        "Branding is the most important detail. "
        "Render text and logo with maximum precision, sharp and readable. "
        f"Seed: {spec['seed']}."
    )

    return common + side_rules + ending


def _extract_url(obj):
    if isinstance(obj, str):
        if obj.startswith("http://") or obj.startswith("https://"):
            return obj
        return None
    if isinstance(obj, list):
        for item in obj:
            found = _extract_url(item)
            if found:
                return found
        return None
    if isinstance(obj, dict):
        for key in ["output", "url", "image_url", "image", "src", "data", "result", "results"]:
            if key in obj:
                found = _extract_url(obj[key])
                if found:
                    return found
        return None
    return None


def submit_job_to_polza(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")
    if not polza_key:
        raise Exception("POLZA_API_KEY missing")

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
                "images": [
                    {
                        "type": "url",
                        "data": image_url
                    }
                ]
            },
            "async": True
        },
        timeout=30
    )

    if response.status_code >= 400:
        raise Exception(f"HTTP {response.status_code}: {response.text[:1500]}")

    try:
        res = response.json()
    except Exception:
        raise Exception(f"Non-JSON: {response.text[:500]}")

    print("POLZA SUBMIT:", res)

    job_id = (
        res.get("id") or
        res.get("job_id") or
        res.get("taskId") or
        res.get("task_id")
    )

    if not job_id:
        url = _extract_url(res)
        if url:
            return None, url
        raise Exception(f"No job_id: {res}")

    return job_id, None


async def poll_polza_job_async(job_id, max_wait=300, interval=5):
    polza_key = os.getenv("POLZA_API_KEY")
    headers = {"Authorization": f"Bearer {polza_key}"}

    elapsed = 0
    while elapsed < max_wait:
        await asyncio.sleep(interval)
        elapsed += interval

        try:
            resp = await asyncio.to_thread(
                requests.get,
                f"https://polza.ai/api/v1/media/{job_id}",
                headers=headers,
                timeout=30
            )
            res = resp.json()
        except Exception as e:
            print(f"Poll error: {e}")
            continue

        print(f"POLZA POLL [{elapsed}s]:", res)

        status = (
            res.get("status") or
            res.get("state") or
            res.get("jobStatus") or
            ""
        ).lower()

        if status in ["succeeded", "completed", "done", "success", "finished"]:
            url = _extract_url(res)
            if url:
                return url
            raise Exception(f"Done but no URL: {res}")

        if status in ["failed", "error", "cancelled"]:
            raise Exception(f"Job failed: {res}")

        url = _extract_url(res)
        if url:
            return url

    raise Exception(f"Timeout after {max_wait}s")


async def generate_image_async(prompt, image_url):
    job_id, immediate_url = await asyncio.to_thread(submit_job_to_polza, prompt, image_url)

    if immediate_url:
        final_url = immediate_url
    else:
        final_url = await poll_polza_job_async(job_id, max_wait=300, interval=5)

    img = await asyncio.to_thread(requests.get, final_url, timeout=180)
    if img.status_code >= 400:
        raise Exception(f"Failed to download: {img.status_code}")

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_{int(time.time() * 1000)}_{random.randint(1000, 9999)}.png"

    with open(path, "wb") as f:
        f.write(img.content)

    crop_watermark(path, crop_percent=0.07)
    return path


async def generate_single_image_from_spec(spec):
    prompt = build_prompt(spec)
    return await generate_image_async(prompt, spec["ref"])


async def generate_all_photos():
    reset_used_poses()

    # Чередуем: front, back, front, back, front
    sides = ["front", "back", "front", "back", "front"]
    specs = [build_spec(side) for side in sides]

    tasks = [generate_single_image_from_spec(spec) for spec in specs]
    paths = await asyncio.gather(*tasks)

    return list(paths), specs


async def regenerate_photo(index, current_specs):
    old_spec = current_specs[index]
    side = old_spec["side"]

    # Берём новую неиспользованную позу
    new_spec = build_spec(side)

    # Если попалась та же — пробуем ещё
    tries = 0
    while new_spec["pose_idx"] == old_spec["pose_idx"] and tries < 20:
        new_spec = build_spec(side)
        tries += 1

    path = await generate_single_image_from_spec(new_spec)
    return path, new_spec
