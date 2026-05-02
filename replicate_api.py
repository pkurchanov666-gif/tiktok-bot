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

POSE_SLOT_TYPES = {
    "front_hood_grab": {
        "side": "front",
        "angles": [
            "direct frontal view, eye level",
            "slight low angle frontal",
            "three-quarters left front",
            "three-quarters right front",
        ],
        "hood_states": ["hood up", "hood up", "hood down"],
        "poses": [
            {
                "name": "left_hand_hood",
                "text": "left hand gripping the edge of the hood near the temple, right arm relaxed close to torso, slight torso turn"
            },
            {
                "name": "right_hand_hood",
                "text": "right hand gripping the hood edge near the cheek, left arm relaxed across lower torso, calm confident stance"
            },
            {
                "name": "both_hands_hood",
                "text": "both hands holding the hood near the jawline, elbows slightly lifted, stable confident posture"
            },
            {
                "name": "one_hand_string_pull",
                "text": "one hand pulling the hood string lightly near the neck, other arm bent across the abdomen"
            },
        ],
    },
    "front_cross_body": {
        "side": "front",
        "angles": [
            "direct frontal view, eye level",
            "three-quarters left front",
            "three-quarters right front",
            "slight top-down frontal",
        ],
        "hood_states": ["hood up", "hood down", "hood up"],
        "poses": [
            {
                "name": "crossed_arms",
                "text": "arms crossed firmly on chest, shoulders relaxed, subtle forward lean"
            },
            {
                "name": "one_arm_folded_other_hood",
                "text": "one arm folded across torso, other hand touching hood near the neck, confident relaxed posture"
            },
            {
                "name": "chin_touch_folded_arm",
                "text": "one hand touching chin thoughtfully, the other arm folded across body, composed stance"
            },
            {
                "name": "forearm_across_torso",
                "text": "one forearm resting across the lower chest, other hand raised near hood seam, relaxed but assertive pose"
            },
        ],
    },
    "front_motion": {
        "side": "front",
        "angles": [
            "direct frontal view, eye level",
            "slight low angle frontal",
            "three-quarters left front",
            "three-quarters right front",
        ],
        "hood_states": ["hood up", "hood down", "hood up"],
        "poses": [
            {
                "name": "walking_hood_touch",
                "text": "mid-step walk toward camera, one hand touching the hood edge, the other arm moving naturally"
            },
            {
                "name": "leaning_wall_hood",
                "text": "leaning lightly against a wall, one hand touching the hood, the other arm bent across torso"
            },
            {
                "name": "forward_lean_thigh",
                "text": "slight forward lean, one hand resting on thigh, the other hand touching hood near the neck"
            },
            {
                "name": "semi_profile_hood_pull",
                "text": "semi-profile stance, one hand pulling hood slightly forward, other arm bent near waist"
            },
        ],
    },
    "back_hood_touch": {
        "side": "back",
        "angles": [
            "direct back view",
            "three-quarters back left",
            "three-quarters back right",
            "slight low angle back view",
        ],
        "hood_states": ["hood up"],
        "poses": [
            {
                "name": "back_one_hand_hood",
                "text": "back facing camera, one hand gripping the back of the hood, other arm relaxed close to torso"
            },
            {
                "name": "back_both_hands_hood",
                "text": "back facing camera, both hands pulling the hood tighter around the head, elbows slightly raised"
            },
            {
                "name": "back_hood_adjust",
                "text": "three-quarters back stance, one hand touching the hood seam near the neck, shoulders slightly angled"
            },
            {
                "name": "back_head_down_hands_active",
                "text": "standing with back to camera, head slightly lowered, both arms active near the hood"
            },
        ],
    },
    "back_motion": {
        "side": "back",
        "angles": [
            "direct back view",
            "three-quarters back left",
            "three-quarters back right",
            "slight top-down back view",
        ],
        "hood_states": ["hood up"],
        "poses": [
            {
                "name": "back_walk_away",
                "text": "walking away from camera naturally, one hand touching the hood from behind, the other arm swinging naturally"
            },
            {
                "name": "back_slow_walk",
                "text": "slow natural walk away from camera, arms moving naturally, hood fully up"
            },
            {
                "name": "back_wall_lean",
                "text": "leaning with shoulder against wall, back fully visible, one hand adjusting hood"
            },
            {
                "name": "back_turn_motion",
                "text": "moving away in a three-quarters back stance, one arm active near hood, body in natural motion"
            },
        ],
    },
}

RECENT_KEYS = []


def crop_watermark(path: str, crop_percent: float = 0.07):
    try:
        img = Image.open(path)
        w, h = img.size
        new_h = int(h * (1 - crop_percent))
        img = img.crop((0, 0, w, new_h))
        img.save(path)
    except Exception as e:
        print(f"Crop failed: {e}")


def combo_key(spec):
    return (
        spec["slot_type"],
        spec["scene"],
        spec["pose_name"],
        spec["angle"],
        spec["hood"],
        spec["light_detail"],
        spec["camera_feel"],
        spec["crop_style"],
    )


def register_key(spec):
    global RECENT_KEYS
    RECENT_KEYS.append(combo_key(spec))
    if len(RECENT_KEYS) > 50:
        RECENT_KEYS = RECENT_KEYS[-50:]


def similarity_score(a, b):
    fields = ["scene", "pose_name", "angle", "hood", "light_detail", "camera_feel", "crop_style"]
    score = 0
    for f in fields:
        if a.get(f) == b.get(f):
            score += 1
    return score


def build_spec_for_slot(slot_type, avoid_spec=None):
    slot = POSE_SLOT_TYPES[slot_type]
    side = slot["side"]

    for _ in range(80):
        pose = random.choice(slot["poses"])
        scene = random.choice(SCENES)
        angle = random.choice(slot["angles"])
        hood = random.choice(slot["hood_states"])

        spec = {
            "slot_type": slot_type,
            "side": side,
            "scene": scene,
            "pose_name": pose["name"],
            "pose": pose["text"],
            "angle": angle,
            "hood": hood,
            "ref": REF_FRONT if side == "front" else REF_BACK,
            "light_detail": random.choice(LIGHT_DETAILS),
            "background_detail": random.choice(BACKGROUND_DETAILS),
            "crop_style": random.choice(CROP_STYLES),
            "camera_feel": random.choice(CAMERA_FEELS),
            "seed": random.randint(100000, 999999),
        }

        if combo_key(spec) in RECENT_KEYS:
            continue

        if avoid_spec and similarity_score(spec, avoid_spec) >= 3:
            continue

        register_key(spec)
        return spec

    pose = random.choice(slot["poses"])
    spec = {
        "slot_type": slot_type,
        "side": side,
        "scene": random.choice(SCENES),
        "pose_name": pose["name"],
        "pose": pose["text"],
        "angle": random.choice(slot["angles"]),
        "hood": random.choice(slot["hood_states"]),
        "ref": REF_FRONT if side == "front" else REF_BACK,
        "light_detail": random.choice(LIGHT_DETAILS),
        "background_detail": random.choice(BACKGROUND_DETAILS),
        "crop_style": random.choice(CROP_STYLES),
        "camera_feel": random.choice(CAMERA_FEELS),
        "seed": random.randint(100000, 999999),
    }
    register_key(spec)
    return spec


def build_prompt(spec):
    common = (
        "Ultra-realistic image-to-image fashion photo of the same person from the reference image. "
        "Keep the same face, same body shape, same proportions, same hoodie. "
        "Do not redesign the clothing. "
        "Hoodie has no pocket, no zipper, no extra stitching, no extra details. "
        "Strictly black wide-leg jeans, loose fit, baggy silhouette, deep solid black denim. "
        "Normal high-quality real photo, not a studio shoot, not editorial, not CGI, not overprocessed. "
        "No professional lighting setup. No neon colors. No cinematic grading. "
        f"{spec['camera_feel']}. "
        f"{spec['light_detail']}. "
        f"{spec['background_detail']}. "
        f"{spec['crop_style']}. "
        f"Scene: {spec['scene']}. "
        f"Pose must be exactly: {spec['pose']}. "
        f"Camera angle: {spec['angle']}. "
        f"Hood state: {spec['hood']}. "
        "Avoid generic straight standing. Avoid both arms hanging straight down. "
        "Natural fabric folds, realistic cotton texture. "
    )

    if spec["side"] == "front":
        side_rules = (
            "FRONT shot. Use only front design from Reference Image 2. "
            "No back print. Chest logo must be clear, sharp, readable. "
        )
    else:
        side_rules = (
            "BACK shot. Use only back design from Reference Image 1. "
            "No front logo. Person must NOT look at camera. No face visible. "
            "Hood always up. Camera faces the back. Back print fully visible. "
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
        raise Exception(f"Polza submit error HTTP {response.status_code}: {response.text[:1500]}")

    try:
        res = response.json()
    except Exception:
        raise Exception(f"Polza non-JSON: {response.text[:500]}")

    print("POLZA SUBMIT:", res)

    job_id = res.get("id") or res.get("job_id") or res.get("taskId") or res.get("task_id")

    if not job_id:
        url = _extract_url(res)
        if url:
            return None, url
        raise Exception(f"No job_id in Polza response: {res}")

    return job_id, None


def poll_polza_job(job_id, max_wait=300, interval=5):
    polza_key = os.getenv("POLZA_API_KEY")
    headers = {"Authorization": f"Bearer {polza_key}"}

    elapsed = 0
    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        resp = requests.get(
            f"https://polza.ai/api/v1/media/{job_id}",
            headers=headers,
            timeout=30
        )

        try:
            res = resp.json()
        except Exception:
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
            raise Exception(f"Job completed but no URL: {res}")

        if status in ["failed", "error", "cancelled"]:
            raise Exception(f"Polza job failed: {res}")

        url = _extract_url(res)
        if url:
            return url

    raise Exception(f"Polza job timeout after {max_wait}s")


def generate_image_with_polza(prompt, image_url):
    job_id, immediate_url = submit_job_to_polza(prompt, image_url)

    if immediate_url:
        final_url = immediate_url
    else:
        final_url = poll_polza_job(job_id, max_wait=300, interval=5)

    img = requests.get(final_url, timeout=180)
    if img.status_code >= 400:
        raise Exception(f"Failed to download image: {img.status_code}")

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_{int(time.time() * 1000)}_{random.randint(1000, 9999)}.png"

    with open(path, "wb") as f:
        f.write(img.content)

    crop_watermark(path, crop_percent=0.07)
    return path


def generate_single_image_from_spec(spec):
    prompt = build_prompt(spec)
    return generate_image_with_polza(prompt, spec["ref"])


async def generate_all_photos():
    # ТЕСТ РЕЖИМ: генерим только 1 фото
    spec = build_spec_for_slot("front_hood_grab")
    path = await asyncio.to_thread(generate_single_image_from_spec, spec)
    return [path], [spec]


async def regenerate_photo(index, current_specs):
    old_spec = current_specs[index]
    slot_type = old_spec["slot_type"]

    new_spec = build_spec_for_slot(slot_type=slot_type, avoid_spec=old_spec)

    tries = 0
    while (
        new_spec["pose_name"] == old_spec["pose_name"] or
        similarity_score(new_spec, old_spec) >= 3
    ) and tries < 50:
        new_spec = build_spec_for_slot(slot_type=slot_type, avoid_spec=old_spec)
        tries += 1

    path = await asyncio.to_thread(generate_single_image_from_spec, new_spec)
    return path, new_spec
