import os
import time
import random
import requests
import asyncio
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
]

POSES_FRONT = [
    "standing naturally with relaxed hands",
    "walking slowly toward camera",
    "slight torso rotation, relaxed posture",
    "leaning lightly against a wall",
    "hands in pockets, calm expression",
    "casual standing pose, natural body language",
]

POSES_BACK = [
    "standing with back to camera",
    "walking away from camera",
    "slight turn of shoulders but back still dominant",
    "hood up, back fully visible, natural relaxed posture",
    "standing still with arms relaxed and back facing camera",
]

ANGLES_FRONT = [
    "direct frontal view",
    "slight low angle frontal",
    "three-quarters left front",
    "three-quarters right front",
]

ANGLES_BACK = [
    "direct back view",
    "three-quarters back left",
    "three-quarters back right",
]


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
            "temperature": 1.25,
            "max_tokens": 1200
        },
        timeout=120
    )

    if resp.status_code >= 400:
        raise Exception(f"Groq error: {resp.text[:1500]}")

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def build_single_spec(force_side=None):
    if force_side:
        side = force_side
    else:
        side = "front" if random.random() < 0.6 else "back"

    scene = random.choice(SCENES)

    if side == "front":
        pose = random.choice(POSES_FRONT)
        angle = random.choice(ANGLES_FRONT)
        ref = REF_FRONT
    else:
        pose = random.choice(POSES_BACK)
        angle = random.choice(ANGLES_BACK)
        ref = REF_BACK

    return {
        "side": side,
        "scene": scene,
        "pose": pose,
        "angle": angle,
        "ref": ref,
        "seed": random.randint(100000, 999999)
    }


def build_batch_specs(count=5):
    fronts = 3
    backs = 2

    chosen_scenes = random.sample(SCENES, min(count, len(SCENES)))

    front_poses = random.sample(POSES_FRONT, min(fronts, len(POSES_FRONT)))
    back_poses = random.sample(POSES_BACK, min(backs, len(POSES_BACK)))

    front_angles = random.sample(ANGLES_FRONT, min(fronts, len(ANGLES_FRONT)))
    back_angles = random.sample(ANGLES_BACK, min(backs, len(ANGLES_BACK)))

    sides = ["front"] * fronts + ["back"] * backs
    random.shuffle(sides)

    specs = []
    fi = 0
    bi = 0

    for i in range(count):
        side = sides[i] if i < len(sides) else ("front" if random.random() < 0.6 else "back")
        scene = chosen_scenes[i % len(chosen_scenes)]

        if side == "front":
            pose = front_poses[fi % len(front_poses)]
            angle = front_angles[fi % len(front_angles)]
            ref = REF_FRONT
            fi += 1
        else:
            pose = back_poses[bi % len(back_poses)]
            angle = back_angles[bi % len(back_angles)]
            ref = REF_BACK
            bi += 1

        specs.append({
            "side": side,
            "scene": scene,
            "pose": pose,
            "angle": angle,
            "ref": ref,
            "seed": random.randint(100000, 999999)
        })

    return specs


def build_instruction(spec):
    side = spec["side"]
    scene = spec["scene"]
    pose = spec["pose"]
    angle = spec["angle"]
    seed = spec["seed"]

    common_rules = (
        "Write one final English prompt for an ultra-realistic image-to-image fashion photo. "
        "Output only the final prompt, no explanations, no lists. "
        "Keep the same person, same face, same body shape, same hoodie. "
        "Do not redesign the clothing. "
        "Hoodie must have no pocket, no zipper, no extra elements. "
        "Jeans must be strictly black wide-leg jeans. "
        "The result must look like a normal high-quality realistic photo, not a studio shoot, not editorial, not CGI. "
        "No professional lighting setup. "
        "No neon colors. "
        "No cinematic teal-orange grading. "
        "Use natural realistic evening or night ambient light, neutral colors, logical soft shadows, believable real-world exposure. "
        "The image should feel like an ordinary but very good real photo taken on a quality phone or mirrorless camera. "
        "Scene must be: " + scene + ". "
        "Pose must be: " + pose + ". "
        "Camera angle must be: " + angle + ". "
        "Vertical composition, realistic proportions, natural fabric folds, realistic cotton texture. "
        "Render the correct hoodie print with maximum precision and readability. "
    )

    if side == "front":
        side_rules = (
            "This is a FRONT shot. "
            "Use only the front design from the front reference image. "
            "Do not add any back print. "
            "The logo and text on the chest must be clear, sharp, readable, and perfectly placed. "
            "The subject may look naturally toward camera or slightly away, but the front of the hoodie must stay fully visible. "
        )
    else:
        side_rules = (
            "This is a BACK shot. "
            "Use only the back design from the back reference image. "
            "Do not add any front logo. "
            "The person must NOT look at the camera. "
            "The hood must always be up on the head. "
            "The camera must clearly face the back of the hoodie. "
            "Back print must stay fully visible and accurate. "
            "No eye contact, no frontal face presentation. "
        )

    final_line = (
        f"Unique variation id: {seed}. "
        "The branding on the hoodie is the most important detail. "
        "Keep it accurate, sharp, readable, and correctly positioned."
    )

    return common_rules + side_rules + final_line


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
        raise Exception(f"Polza non-JSON response: {response.text[:1500]}")

    print("POLZA MEDIA RESPONSE:", res)

    # Даже если Polza ноет про ошибку, но URL есть — берём URL и не падаем
    final_url = _extract_url(res)

    if not final_url:
        if response.status_code >= 400:
            raise Exception(f"HTTP {response.status_code}: {response.text[:1500]}")
        raise Exception(f"Unexpected Polza response: {str(res)[:1500]}")

    img = requests.get(final_url, timeout=180)
    if img.status_code >= 400:
        raise Exception(f"Failed to download image: {img.status_code}")

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
    target_count = 5
    results = []
    errors = []

    specs = build_batch_specs(target_count)

    for spec in specs:
        try:
            path = await asyncio.to_thread(generate_single_image_from_spec, spec)
            if path:
                results.append(path)
        except Exception as e:
            errors.append(str(e))
        await asyncio.sleep(1)

    # если не добили 5 — пробуем добить ещё
    attempts = 0
    while len(results) < target_count and attempts < 10:
        attempts += 1
        try:
            extra_spec = build_single_spec()
            path = await asyncio.to_thread(generate_single_image_from_spec, extra_spec)
            if path:
                results.append(path)
        except Exception as e:
            errors.append(str(e))
        await asyncio.sleep(1)

    if results:
        return results[:5]

    raise Exception(errors[0] if errors else "Все AI генерации упали")


async def regenerate_photo(index):
    # Для первых трёх слотов чаще фронт, для двух последних чаще бэк
    force_side = "front" if index in [0, 1, 2] else "back"
    spec = build_single_spec(force_side=force_side)
    return await asyncio.to_thread(generate_single_image_from_spec, spec)
