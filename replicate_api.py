import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

SAVE_DIR = "generations"
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

SCENES = ["premium minimalist city street", "exclusive underground parking", "luxury hotel driveway", "high-tech business district"]
MATERIALS = ["polished basalt stone", "raw industrial concrete", "304-grade brushed steel", "tempered reflective glass"]
LIGHTING = ["3000K warm golden light", "6000K cool-white LED strips", "natural blue hour twilight"]
DETAILS = ["sharp reflections on wet pavement", "visible rubber gaskets on glass frames", "sharp industrial ceiling pipes"]

FRONT_POSES = ["one hand actively gripping the edge of the hood near the temple, elbow out", "both hands raised adjusting the sides of the hood", "one hand touching the neck area of the hoodie"]
BACK_POSES = ["back facing camera, one hand raised resting on the back of the head", "walking away into the depth of the scene", "standing still facing away, both hands raised"]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0

LLM_SYSTEM_PROMPT = """You are a technical photographer. Write a 300-word TECHNICAL prompt for a RAW 9:16 photo. f/22, ZERO BOKEH, NO background blur. NO pocket. Front: 0.5m. Back: 8m. Surgical sharpness."""

def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX
    spec = {
        "side": side, "scene": random.choice(SCENES), "material": random.choice(MATERIALS),
        "lighting": random.choice(LIGHTING), "detail": random.choice(DETAILS),
        "seed": random.randint(1, 1000000), "ref": REF_FRONT if side == "front" else REF_BACK
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
    dist = "0.5m" if spec['side'] == 'front' else "8.0m"
    blueprint = f"VIEW: {spec['side'].upper()}. Dist: {dist}. Scene: {spec['scene']}. Pose: {spec['pose']}. Material: {spec['material']}."
    try:
        response = await asyncio.to_thread(requests.post, "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": LLM_SYSTEM_PROMPT}, {"role": "user", "content": f"Write prompt: {blueprint}"}],
                "temperature": 0.5
            }, timeout=30)
        return response.json()["choices"][0]["message"]["content"].strip()
    except: return f"Technical RAW photo, f/22, no bokeh, {spec['side']} view, {spec['scene']}, seed {spec['seed']}"

def _extract_url(obj):
    if isinstance(obj, str) and obj.startswith("http"): return obj
    if isinstance(obj, list) and obj: return _extract_url(obj[0])
    if isinstance(obj, dict):
        for k in ["output", "url", "image", "images", "result"]:
            if k in obj:
                res = _extract_url(obj[k])
                if res: return res
        for v in obj.values():
            res = _extract_url(v)
            if res: return res
    return None

def submit_job_to_polza(prompt, image_url, seed):
    polza_key = os.getenv("POLZA_API_KEY")
    payload = {
        "model": "black-forest-labs/flux.2-pro", 
        "input": {
            "prompt": f"{prompt} --unique {random.random()}", # Гарантируем уникальность текста
            "aspect_ratio": "9:16", 
            "image_resolution": "1K",
            "seed": seed, # Передаем сид
            "images": [{"type": "url", "data": image_url}]
        }, 
        "async": True
    }
    res = requests.post("https://polza.ai/api/v1/media", 
                        headers={"Authorization": f"Bearer {polza_key}", "Content-Type": "application/json"},
                        json=payload, timeout=30)
    print(f"   [API] Submit Status: {res.status_code}")
    data = res.json()
    job_id = data.get("id") or data.get("task_id")
    if not job_id:
        url = _extract_url(data)
        if url: return url, True
        raise Exception(f"Polza Error: {data}")
    return job_id, False

async def poll_polza_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")
    for attempt in range(60):
        await asyncio.sleep(5)
        try:
            res = await asyncio.to_thread(requests.get, f"https://polza.ai/api/v1/media/{job_id}", headers={"Authorization": f"Bearer {polza_key}"})
            data = res.json()
            status = (data.get("status") or data.get("state") or "").lower()
            url = _extract_url(data)
            if url and (status in ["succeeded", "completed", "done", "success"] or not status):
                return url
            if status in ["failed", "error"]: raise Exception(f"Polza Failed: {data}")
        except Exception: continue
    return None

async def generate_single_image(spec):
    print(f"🔎 Начинаю: {spec['side']} (Seed: {spec['seed']})")
    big_prompt = await expand_prompt_via_llm(spec)
    result, is_final = await asyncio.to_thread(submit_job_to_polza, big_prompt, spec["ref"], spec["seed"])
    
    if is_final:
        url = result
    else:
        print(f"   📡 Задание принято, ID: {result}. Ждем...")
        url = await poll_polza_job(result)
        
    if not url: raise Exception("URL не найден")

    img_data = await asyncio.to_thread(requests.get, url, timeout=180)
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}.png")
    with open(path, "wb") as f: f.write(img_data.content)
    with Image.open(path) as im:
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.93))).save(path)
    return path

async def generate_all_photos():
    print("🚀 СТАРТ СЕССИИ (3 ФОТО)")
    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]
    paths = []
    
    for i, spec in enumerate(specs):
        try:
            print(f"📸 Обработка {i+1}/3...")
            path = await generate_single_image(spec)
            paths.append(path)
            print(f"✅ Готово: {path}")
            await asyncio.sleep(1) # Короткая пауза для стабильности
        except Exception as e:
            print(f"❌ Ошибка на {i+1} фото: {e}")
            
    return paths, specs

async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single_image(new_spec)
    return path, new_spec
