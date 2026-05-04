import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# --- НАСТРОЙКИ ПУТЕЙ ---
SAVE_DIR = "generations"
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# --- РАНДОМ СПИСКИ ---
SCENES = ["premium minimalist city street", "exclusive underground parking", "luxury hotel driveway", "high-tech business district"]
MATERIALS = ["polished basalt stone", "raw industrial concrete", "304-grade brushed steel", "tempered glass"]
LIGHTING = ["3000K warm golden light", "6000K cool-white LED", "natural blue hour twilight"]
DETAILS = ["sharp reflections on wet pavement", "visible rubber gaskets on windows", "sharp industrial pipes"]

FRONT_POSES = [
    "one hand actively gripping the edge of the hood near the temple, elbow out",
    "both hands raised adjusting the sides of the hood, elbows pointed out and lifted",
    "one hand touching the neck area of the hoodie, other forearm bent across waistband"
]

BACK_POSES = [
    "back facing camera, one hand raised resting on the back of the head over the hood",
    "walking away into the depth of the scene, hood up, one hand touching the hood",
    "standing still facing away, both hands raised adjusting the hood sides"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0

LLM_SYSTEM_PROMPT = """
You are a technical architectural and fashion photographer. 
Your task: Write a 300-word TECHNICAL prompt for a RAW 9:16 photo with TELESCOPIC CLARITY.
STRICT RULES: f/22 aperture, ZERO BOKEH, NO background blur. NO hoodie pocket. Front: 0.5m. Back: 8m.
"""

def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX
    spec = {
        "side": side, "scene": random.choice(SCENES), "material": random.choice(MATERIALS),
        "lighting": random.choice(LIGHTING), "detail": random.choice(DETAILS),
        "seed": random.randint(100000, 999999), "ref": REF_FRONT if side == "front" else REF_BACK
    }
    if side == "front":
        spec["pose"] = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
    else:
        spec["pose"] = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
    return spec

async def expand_prompt_via_llm(spec):
    groq_key = os.getenv("GROQ_API_KEY")
    dist = "0.5m (85% height)" if spec['side'] == 'front' else "8.0m (30% height)"
    blueprint = f"VIEW: {spec['side'].upper()}. Distance: {dist}. Scene: {spec['scene']}. Pose: {spec['pose']}."
    try:
        response = await asyncio.to_thread(requests.post, "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": LLM_SYSTEM_PROMPT}, {"role": "user", "content": f"300-word technical prompt: {blueprint}"}],
                "temperature": 0.5
            }, timeout=30)
        return response.json()["choices"][0]["message"]["content"].strip()
    except: return f"Photo, f/22, no bokeh, {spec['side']} view, {spec['scene']}"

def _extract_url(obj):
    """Вспомогательная функция для поиска URL в глубоком JSON"""
    if isinstance(obj, str) and obj.startswith("http"): return obj
    if isinstance(obj, list) and obj: return _extract_url(obj[0])
    if isinstance(obj, dict):
        for k in ["output", "url", "image", "data"]:
            if k in obj:
                found = _extract_url(obj[k])
                if found: return found
    return None

def submit_job_to_polza(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")
    res = requests.post("https://polza.ai/api/v1/media", headers={"Authorization": f"Bearer {polza_key}"},
        json={
            "model": "black-forest-labs/flux.2-pro", 
            "input": {"prompt": prompt, "aspect_ratio": "9:16", "images": [{"type": "url", "data": image_url}]}, 
            "async": True
        }, timeout=30)
    data = res.json()
    job_id = data.get("id") or data.get("task_id")
    if not job_id: raise Exception(f"Polza Error: {data}")
    return job_id

async def poll_polza_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")
    for _ in range(60):
        await asyncio.sleep(5)
        try:
            res = await asyncio.to_thread(requests.get, f"https://polza.ai/api/v1/media/{job_id}", headers={"Authorization": f"Bearer {polza_key}"})
            data = res.json()
            status = (data.get("status") or data.get("state") or "").lower()
            if status in ["succeeded", "completed", "done"]:
                url = _extract_url(data)
                if url: return url
            if status in ["failed", "error"]: raise Exception(f"Polza Failed: {data}")
        except Exception as e:
            if "Polza Failed" in str(e): raise e
            continue
    return None

async def generate_single_image(spec):
    big_prompt = await expand_prompt_via_llm(spec)
    job_id = await asyncio.to_thread(submit_job_to_polza, big_prompt, spec["ref"])
    
    url = await poll_polza_job(job_id)
    if not url:
        raise Exception("Не удалось получить URL картинки от Polza (Timeout или Error)")

    img_data = await asyncio.to_thread(requests.get, url, timeout=180)
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}.png")
    
    with open(path, "wb") as f: f.write(img_data.content)
    with Image.open(path) as im:
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.93))).save(path)
    return path

async def generate_all_photos():
    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]
    paths = []
    for spec in specs:
        path = await generate_single_image(spec)
        paths.append(path)
    return paths, specs

async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single_image(new_spec)
    return path, new_spec
