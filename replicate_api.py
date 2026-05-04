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

# Сцены с упором на материалы для четкости фона
SCENES = [
    "modern city street, 304-grade steel storefronts, 10mm tempered glass windows, sharp pavement texture",
    "underground parking, raw concrete pillars, industrial LED strips, sharp floor markings",
    "luxury hotel driveway, dark granite slabs, architectural spotlighting, sharp reflections",
    "contemporary office lobby, minimalist glass partitions, polished stone flooring",
    "city alleyway at night, exposed brickwork, sharp metal fire escapes, realistic street lamps",
]

FRONT_POSES = [
    "standing close to camera, one hand resting on the hood edge near the temple, other arm relaxed, shoulders squared",
    "direct frontal view, both hands raised lightly touching the hood sides, elbows pointed outward",
    "facing camera squared, torso flat and front-facing, one hand adjusting the hood seam, other arm low",
    "slightly asymmetrical stance, one hand near the jawline gripping the hood, other arm at the side",
]

BACK_POSES = [
    "standing with back to camera, one hand raised resting on the back of the head over the hood",
    "walking away from camera into the depth of the scene, hood up, arms moving naturally, sharp silhouette",
    "standing still facing away, both hands adjusting the hood sides, elbows visible and raised",
    "back view, shoulders slightly angled, head neutral, looking towards the distant sharp architecture",
]

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
        USED_FRONT_POSES = set(); available = list(range(len(FRONT_POSES)))
    idx = random.choice(available); USED_FRONT_POSES.add(idx)
    return idx, FRONT_POSES[idx]

def get_unused_back_pose():
    global USED_BACK_POSES
    available = [i for i in range(len(BACK_POSES)) if i not in USED_BACK_POSES]
    if not available:
        USED_BACK_POSES = set(); available = list(range(len(BACK_POSES)))
    idx = random.choice(available); USED_BACK_POSES.add(idx)
    return idx, BACK_POSES[idx]

def crop_watermark(path: str, crop_percent: float = 0.07):
    try:
        img = Image.open(path)
        w, h = img.size
        img = img.crop((0, 0, w, int(h * (1 - crop_percent))))
        img.save(path)
    except: pass

def build_spec(side):
    if side == "front":
        idx, text = get_unused_front_pose()
        return {"side": "front", "pose_idx": idx, "pose": text, "scene": random.choice(SCENES), "seed": random.randint(100000, 999999), "ref": REF_FRONT}
    else:
        idx, text = get_unused_back_pose()
        return {"side": "back", "pose_idx": idx, "pose": text, "scene": random.choice(SCENES), "seed": random.randint(100000, 999999), "ref": REF_BACK}

def build_prompt(spec):
    # Каждое предложение имеет технический смысл. Никакой воды.
    tech_base = (
        "RAW 9:16 photograph, Sony A7R V, 35mm G-Master lens, f/11 aperture for infinite depth of field. "
        "Strictly NO background blur, zero bokeh, surgical sharpness from foreground to background. "
        "High-resolution 61MP sensor quality, realistic micro-contrast, visible skin pores. "
        "No neon colors, no cinematic grading, neutral realistic exposure. "
    )
    
    clothing = (
        "Preserve exact identity and clothing from reference. "
        "Solid black hoodie, 500GSM heavy-weight cotton weave texture. "
        "MANDATORY: No kangaroo pocket, no front pouch, no zippers, no drawstrings. Seamless flat torso fabric. "
        "Extra-wide baggy black denim jeans, coarse twill grain, heavy fabric drape. "
    )

    if spec["side"] == "front":
        framing = (
            "FRONT shot. Distance: 0.5 meters. Framing: waist-up composition. "
            "Subject occupies 85% of vertical frame height. Positioned to the left side. "
            "Chest logo is the primary focus, high-density silk-screen print, raised ink texture, razor-sharp readable edges. "
        )
    else:
        framing = (
            "BACK shot. Distance: 5.0 meters (twice as far as front shots). Framing: environmental wide shot. "
            "Subject occupies 35-40% of vertical frame height. Vast architectural perspective. "
            "Hood is UP, face not visible. Focus on back silhouette and sharp background details. "
        )

    context = f"Scene: {spec['scene']}. Pose: {spec['pose']}. Seed: {spec['seed']}."
    
    return tech_base + clothing + framing + context

def submit_job_to_polza(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")
    if not polza_key: raise Exception("POLZA_API_KEY missing")
    response = requests.post(
        "https://polza.ai/api/v1/media",
        headers={"Authorization": f"Bearer {polza_key}", "Content-Type": "application/json"},
        json={
            "model": "black-forest-labs/flux.2-pro",
            "input": {"prompt": prompt, "aspect_ratio": "9:16", "image_resolution": "1K", "images": [{"type": "url", "data": image_url}]},
            "async": True
        },
        timeout=30
    )
    res = response.json()
    return (res.get("id") or res.get("task_id")), None

async def poll_polza_job_async(job_id):
    polza_key = os.getenv("POLZA_API_KEY")
    headers = {"Authorization": f"Bearer {polza_key}"}
    for _ in range(60):
        await asyncio.sleep(5)
        try:
            resp = await asyncio.to_thread(requests.get, f"https://polza.ai/api/v1/media/{job_id}", headers=headers, timeout=30)
            res = resp.json()
            if (res.get("status") or "").lower() in ["succeeded", "completed", "done"]:
                output = res.get("output")
                return output[0] if isinstance(output, list) else output
        except: continue
    raise Exception("Poll Timeout")

async def generate_single_image_from_spec(spec):
    prompt = build_prompt(spec)
    job_id, _ = await asyncio.to_thread(submit_job_to_polza, prompt, spec["ref"])
    final_url = await poll_polza_job_async(job_id)
    img = await asyncio.to_thread(requests.get, final_url, timeout=180)
    os.makedirs("output", exist_ok=True)
    path = f"output/ai_{int(time.time() * 1000)}.png"
    with open(path, "wb") as f: f.write(img.content)
    crop_watermark(path)
    return path

async def generate_all_photos():
    reset_used_poses()
    # Твоя очередь: Спина, Лицо, Спина
    sides = ["back", "front", "back"]
    specs = [build_spec(side) for side in sides]
    
    # Генерация строго по очереди для контроля
    paths = []
    for spec in specs:
        path = await generate_single_image_from_spec(spec)
        paths.append(path)
        
    return paths, specs

async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = build_spec(side)
    path = await generate_single_image_from_spec(new_spec)
    return path, new_spec
