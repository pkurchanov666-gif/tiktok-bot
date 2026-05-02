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

POSES_FRONT = [
    "one hand gripping the hood string, other hand relaxed at side, slight chin tilt",
    "both hands pulling hood up over head, looking straight ahead",
    "one hand in pocket, other hand adjusting hood, casual mid-motion",
    "arms crossed loosely, hood up, relaxed confident stance",
    "walking forward, one hand touching the front of the hood lightly",
    "leaning against wall, one hand raised touching hood edge, legs crossed at ankle",
    "standing with one hand on chin, elbow resting on other arm, hood up",
    "mid-step walk toward camera, one hand in pocket, hood slightly back",
    "crouching slightly, elbows on knees, hood up, looking ahead",
    "one thumb hooked in pocket, other hand gripping hood, slight forward lean",
    "both thumbs in pockets, hood up, relaxed weight shift to one leg",
    "turning slightly to the side, one hand pulling hood down a bit, casual",
    "arms loosely at sides, head slightly bowed, hood casting shadow on face",
    "one hand raised adjusting hood from behind, slight profile turn",
    "leaning forward slightly, hood up, both hands resting on thighs",
]

POSES_BACK = [
    "one hand gripping hood from behind, slight head tilt down",
    "both hands pulling hood tighter, elbows raised slightly",
    "one hand in pocket, other hand touching back of hood, walking away slowly",
    "standing still, arms loosely at sides, hood up, head slightly turned to one side",
    "leaning against wall with back, one arm raised touching hood from behind",
    "walking away from camera, one hand swinging naturally, other in pocket",
    "slight torso turn showing mostly back, one hand adjusting hood",
    "standing with legs slightly apart, both hands at sides, hood fully up",
    "crouching with back to camera, hood up, elbows on knees",
    "one hand gripping the back of the hood, head bowed slightly forward",
    "mid-step walk away, arms swinging naturally, hood up",
    "leaning against a wall with shoulder, back facing camera, hood pulled up",
    "arms crossed behind back, head slightly tilted, hood fully on",
    "standing at angle, showing three-quarters back, one hand adjusting hood cuff",
    "slow motion walk away, one hand reaching back touching hood, head down",
]

ANGLES_FRONT = [
    "direct frontal view, eye level",
    "slight low angle frontal, camera below chest height",
    "three-quarters left front, 45 degrees",
    "three-quarters right front, 45 degrees",
    "slight high angle frontal, camera slightly above",
    "close frontal, waist-up tight framing",
    "semi-profile left, still showing front of hoodie",
    "semi-profile right, still showing front of hoodie",
]

ANGLES_BACK = [
    "direct back view, camera eye level",
    "three-quarters back left",
    "three-quarters back right",
    "low angle back view, camera slightly below",
    "slight high angle back view",
    "close back view, waist-up tight framing",
]

HOOD_STATES_FRONT = ["hood up", "hood up", "hood down"]


def generate_final_prompt_from_groq(instruction: str) -> str:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise Exception("GROQ_API_KEY missing")

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": instruction}],
            "temperature": 1.3,
            "max_tokens": 1200
        },
        timeout=120
    )

    if resp.status_code >= 400:
        raise Exception(f"Groq error: {resp.text[:1500]}")

    return resp.json()["choices"][0]["message"]["content"].strip()


def build_batch_specs(count=5):
    # Делаем 5 уникальных комбинаций
    # 3 фронт, 2 бэк — но всегда разные сцены и позы
    sides = ["front", "front", "front", "back", "back"]
    random.shuffle(sides)

    # Берём разные сцены
    scenes = random.sample(SCENES, count)

    # Берём разные позы (без повторов)
    front_poses = random.sample(POSES_FRONT, 5)
    back_poses = random.sample(POSES_BACK, 5)

    front_angles = random.sample(ANGLES_FRONT, 5)
    back_angles = random.sample(ANGLES_BACK, 5)

    fi = 0
    bi = 0
    specs = []

    for i in range(count):
        side = sides[i]
        scene = scenes[i]

        if side == "front":
            pose = front_poses[fi % len(front_poses)]
            angle = front_angles[fi % len(front_angles)]
            hood = random.choice(HOOD_STATES_FRONT)
            ref = REF_FRONT
            fi += 1
        else:
            pose = back_poses[bi % len(back_poses)]
            angle = back_angles[bi % len(back_angles)]
            hood = "hood always up"
            ref = REF_BACK
            bi += 1

        specs.append({
            "side": side,
            "scene": scene,
            "pose": pose,
            "angle": angle,
            "hood": hood,
            "ref": ref,
            "seed": random.randint(100000, 999999)
        })

    return specs


def build_single_spec(force_side=None):
    side = force_side if force_side else random.choice(["front", "back"])

    scene = random.choice(SCENES)

    if side == "front":
        pose = random.choice(POSES_FRONT)
        angle = random.choice(ANGLES_FRONT)
        hood = random.choice(HOOD_STATES_FRONT)
        ref = REF_FRONT
    else:
        pose = random.choice(POSES_BACK)
        angle = random.choice(ANGLES_BACK)
        hood = "hood always up"
        ref = REF_BACK

    return {
        "side": side,
        "scene": scene,
        "pose": pose,
        "angle": angle,
        "hood": hood,
        "ref": ref,
        "seed": random.randint(100000, 999999)
    }


def build_instruction(spec):
    side = spec["side"]
    scene = spec["scene"]
    pose = spec["pose"]
    angle = spec["angle"]
    hood = spec["hood"]
    seed = spec["seed"]

    common = (
        "Write one final English prompt for an ultra-realistic image-to-image fashion photo. "
        "Output ONLY the final prompt. No explanations, no lists, no headers. "
        "Keep the same person, same face, same body shape, same hoodie from the reference image. "
        "Do not redesign the hoodie. "
        "Hoodie must have no pocket, no zipper, no extra elements. "
        "Jeans must be strictly black wide-leg baggy jeans. "
        "The result must look like a normal high-quality realistic photo. "
        "Not a studio shoot, not editorial, not CGI, not fashion campaign. "
        "No professional lighting rig. "
        "No neon colors. "
        "No cinematic teal-orange grading. "
        "No HDR. "
        "Use natural realistic evening or night ambient light. "
        "Neutral colors, logical soft shadows, believable real-world exposure. "
        "The image should feel like a very good quality real photo taken on a mirrorless camera by a friend. "
        f"Scene: {scene}. "
        f"Pose: {pose}. "
        f"Hood state: {hood}. "
        f"Camera angle: {angle}. "
        "Vertical composition, waist-up framing. "
        "Realistic proportions, natural fabric folds, realistic cotton texture. "
        "Render the correct hoodie print with maximum precision. "
    )

    if side == "front":
        side_rules = (
            "This is a FRONT shot. "
            "Use ONLY the front design from Reference Image 2. "
            "Do not add any back print or back elements whatsoever. "
            "The chest logo and text must be clear, sharp, readable, correctly placed. "
            "If hood is up the face may be partially shadowed but the front print must still be visible. "
        )
    else:
        side_rules = (
            "This is a BACK shot. "
            "Use ONLY the back design from Reference Image 1. "
            "Do not add any front logo or chest print whatsoever. "
            "The person must NOT look at the camera under any circumstances. "
            "The hood must always be pulled up on the head. "
            "No face visible. "
            "Camera must clearly face the back of the hoodie. "
            "The back print must be fully visible, accurate, readable, and correctly placed. "
        )

    final_line = (
        f"Unique variation id: {seed}. "
        "The print on the hoodie is the most critical detail. "
        "Reproduce it exactly as in the reference. "
        "Sharp, readable, correct placement, no distortion."
    )

    return common + side_rules + final_line


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


def crop_watermark(path: str, crop_percent: float = 0.07):
    try:
        img = Image.open(path)
        w, h = img.size
        new_h = int(h * (1 - crop_percent))
        cropped = img.crop((0, 0, w, new_h))
        cropped.save(path)
    except Exception as e:
        print(f"Crop failed: {e}")


def generate_image_with_polza(prompt, image_url):
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
            "async": False
        },
        timeout=300
    )

    try:
        res = response.json()
    except Exception:
        raise Exception(f"Polza non-JSON: {response.text[:1500]}")

    print("POLZA RESPONSE:", res)

    final_url = _extract_url(res)

    if not final_url:
        if response.status_code >= 400:
            raise Exception(f"HTTP {response.status_code}: {response.text[:1500]}")
        raise Exception(f"No URL in Polza response: {str(res)[:1500]}")

    img = requests.get(final_url, timeout=180)
    if img.status_code >= 400:
        raise Exception(f"Failed to download: {img.status_code}")

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_{int(time.time() * 1000)}_{random.randint(1000, 9999)}.png"

    with open(path, "wb") as f:
        f.write(img.content)

    # Обрезаем нижние 7% где вотермарк
    crop_watermark(path, crop_percent=0.07)

    return path
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
            "async": False
        },
        timeout=300
    )

    try:
        res = response.json()
    except Exception:
        raise Exception(f"Polza non-JSON: {response.text[:1500]}")

    print("POLZA RESPONSE:", res)

    final_url = _extract_url(res)

    if not final_url:
        if response.status_code >= 400:
            raise Exception(f"HTTP {response.status_code}: {response.text[:1500]}")
        raise Exception(f"No URL in Polza response: {str(res)[:1500]}")

    img = requests.get(final_url, timeout=180)
    if img.status_code >= 400:
        raise Exception(f"Failed to download: {img.status_code}")

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_{int(time.time() * 1000)}_{random.randint(1000, 9999)}.png"

    with open(path, "wb") as f:
        f.write(img.content)

    return path


def generate_single_image_from_spec(spec):
    instruction = build_instruction(spec)
    final_prompt = generate_final_prompt_from_groq(instruction)
    return generate_image_with_polza(final_prompt, spec["ref"])


async def generate_all_photos():
    results = []
    errors = []

    specs = build_batch_specs(5)

    for i, spec in enumerate(specs):
        try:
            path = await asyncio.to_thread(generate_single_image_from_spec, spec)
            if path:
                results.append(path)
                print(f"Photo {i+1}/5 done ✅")
        except Exception as e:
            errors.append(str(e))
            print(f"Photo {i+1}/5 failed: {e}")

        await asyncio.sleep(0.5)

    # Добиваем если не хватает
    attempts = 0
    while len(results) < 5 and attempts < 8:
        attempts += 1
        try:
            spec = build_single_spec()
            path = await asyncio.to_thread(generate_single_image_from_spec, spec)
            if path:
                results.append(path)
        except Exception as e:
            errors.append(str(e))
        await asyncio.sleep(1)

    if results:
        return results[:5]

    raise Exception(errors[0] if errors else "Все генерации упали")


async def regenerate_photo(index):
    force_side = "front" if index in [0, 1, 2] else "back"
    spec = build_single_spec(force_side=force_side)
    return await asyncio.to_thread(generate_single_image_from_spec, spec)
