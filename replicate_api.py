import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# --- КОНФИГУРАЦИЯ ---
SAVE_DIR = "generations"
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# --- РЕЖИССУРА ПАЙТОНА (РАНДОМ) ---
SCENES = ["premium minimalist city street", "exclusive underground parking", "luxury hotel driveway", "high-tech business district"]
MATERIALS = ["polished basalt stone", "raw industrial concrete", "304-grade brushed steel", "tempered reflective glass", "weathered dark brick"]
LIGHTING = ["3000K warm golden light", "6000K cool-white LED strips", "natural blue hour twilight", "4500K neutral street lamps"]
DETAILS = ["sharp reflections on wet pavement", "visible rubber gaskets on glass frames", "sharp industrial ceiling pipes", "individual mortar lines between bricks"]

# --- ПОЗЫ (10 ШТУК) ---
FRONT_POSES = [
    "one hand actively gripping the edge of the hood near the temple, elbow out",
    "both hands raised adjusting the sides of the hood, elbows pointed out and lifted",
    "one hand touching the neck area of the hoodie, other forearm bent across waistband",
    "one hand pulling the hood slightly forward over the forehead, thumb in jeans pocket",
    "adjusting sleeve cuff, other hand raised to grab the hood seam",
    "torso angled slightly, one hand on the back of the neck under hood",
    "both hands high holding hood sides, elbows wide, chest open",
    "mid-stride toward camera, one hand touching hood, other arm in swing",
    "one shoulder dropped, hand touching jawline, other hand in pocket",
    "both hands pulling hood down towards face, strong silhouette"
]

BACK_POSES = [
    "back facing camera, one hand raised resting on the back of the head over the hood",
    "walking away into the depth of the scene, hood up, hand touching hood from behind",
    "standing still facing away, both hands raised adjusting hood sides, elbows out",
    "back view, shoulders angled, hand touching hood seam near the neck",
    "leaning with one shoulder against a pillar, back fully visible, hand on hood",
    "moving away in a 3/4 back stance, one hand adjusting hood",
    "back fully visible, head tilted, arms active adjusting hoodie hem",
    "slow walk away from camera, one arm active near hood",
    "standing with back to lens, arms slightly bent to show hoodie width",
    "3/4 back view, face hidden by hood, hand touching hood seam"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0

# --- СИСТЕМНЫЙ ПРОМПТ ДЛЯ GROQ ---
LLM_SYSTEM_PROMPT = """
You are a technical architectural and fashion photographer. 
Write a 300-word TECHNICAL prompt for a RAW 9:16 photo with TELESCOPIC CLARITY.
STRICT RULES: f/22 aperture, ZERO BOKEH, NO background blur. NO hoodie pocket, NO zippers.
FRONT: 0.5m distance (85% height). BACK: 8.0m distance (30% height).
Every letter of the logo must be sharp and readable. No AI smoothing.
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
    blueprint = f"VIEW: {spec['side'].upper()}. Dist: {dist}. Scene: {spec['scene']}. Pose: {spec['pose']}. Material: {spec['material']}."
    try:
        response = await asyncio.to_thread(requests.post, "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": LLM_SYSTEM_PROMPT}, {"role": "user", "content": f"300-word prompt: {blueprint}"}],
                "temperature": 0.5
            }, timeout=30)
        return response.json()["choices"][0]["message"]["content"].strip()
    except: return f"RAW photo, f/22, no bokeh, {spec['side']} view, {spec['scene']}"

def _extract_url(obj):
    if isinstance(obj, str) and obj.startswith("http"): return obj
    if isinstance(obj, list) and obj: return _extract_url(obj[0])
    if isinstance(obj, dict):
        for k in ["output", "url", "image", "images"]:
            if k in obj:
                res = _extract_url(obj[k])
                if res: return res
    return None

def submit_job_to_polza(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")
    payload = {
        "model": "black-forest-labs/flux.2-pro", 
        "input": {
            "prompt": prompt, 
            "aspect_ratio": "9:16", 
            "image_resolution": "1K", # ЭТА СТРОКА РЕШАЕТ ТВОЮ ОШИБКУ
            "images": [{"type": "url", "data": image_url}]
        }, 
        "async": True
    }
    res = requests.post("https://polza.ai/api/v1/media", 
                        headers={"Authorization": f"Bearer {polza_key}", "Content-Type": "application/json"},
                        json=payload, timeout=30)
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
            if status in ["succeeded", "completed", "done", "success"]:
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
    if not url: raise Exception("No image URL received")
    
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
