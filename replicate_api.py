import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Ссылки на референсы (твои фото)
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# --- ЭСТЕТИЧНЫЕ ЛОКАЦИИ (БЕЗ МЫЛА И ГРЯЗИ) ---
SCENES = [
    "premium minimalist city street, clean polished stone architecture, sharp glass storefronts",
    "exclusive modern underground parking, pristine concrete, bright linear LED lighting",
    "contemporary art gallery exterior, sharp geometric white walls, architectural precision",
    "luxury hotel driveway at night, dark reflective granite surfaces, flawless modern geometry",
    "high-tech business district, glass skyscrapers, sharp steel frames, clean urban aesthetic",
    "modernist pedestrian plaza, pristine stone materials, sharp architectural lines",
    "premium airport terminal entrance, massive glass panels, sharp 304-grade steel details"
]

# --- 10 АКТИВНЫХ ПОЗ (FRONT) - БЕЗ РУК ПО ШВАМ ---
FRONT_POSES = [
    "one hand actively gripping the edge of the hood near the temple, other hand tucked into the jeans pocket", # 1
    "both hands raised adjusting the sides of the hood, elbows pointed out and lifted, shoulders squared", # 2
    "one hand touching the neck area of the hoodie, the other forearm bent and resting across the waistband", # 3
    "one hand pulling the hood slightly forward over the forehead, the other thumb hooked into the jeans pocket", # 4
    "one hand adjusting the sleeve cuff, while the other hand is raised to grab the opposite side of the hood", # 5
    "torso angled slightly, one hand resting on the back of the neck under the hood, other hand near the waist", # 6
    "both hands high holding the sides of the hood, elbows wide, chest fully open and flat", # 7
    "mid-stride toward camera, one hand touching the hood seam, the other arm bent naturally in mid-swing", # 8
    "one shoulder dropped, one hand touching the jawline, the other hand deep inside the baggy jeans pocket", # 9
    "both hands reaching up pulling the hood down towards the face, creating a strong asymmetrical silhouette" # 10
]

# --- 10 АКТИВНЫХ ПОЗ (BACK) ---
BACK_POSES = [
    "back facing camera, one hand raised resting on the back of the head over the hood, distant perspective", # 1
    "walking away into the depth of the scene, hood up, one hand touching the hood from behind", # 2
    "standing still facing away, both hands raised adjusting the hood sides, elbows visible and pointed out", # 3
    "back view, shoulders angled, one hand touching the hood seam near the neck, looking at sharp buildings", # 4
    "leaning with one shoulder against a pristine concrete pillar, back fully visible, one hand adjusting the hood", # 5
    "moving away in a three-quarters back stance, one hand adjusting the hood near the neck, body in motion", # 6
    "back fully visible, head slightly tilted, both arms active adjusting the bottom hem of the hoodie", # 7
    "slow walk away from camera, one arm active near the hood, capturing the expansive architectural scene", # 8
    "standing with back to lens, arms slightly bent and out to the sides to show hoodie width, no hanging arms", # 9
    "three-quarters back view, face hidden by hood, one hand raised touching the hood, looking over the shoulder" # 10
]

# Глобальные счетчики для перебора поз по порядку
CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0

# --- СИСТЕМНЫЙ ПРОМПТ ДЛЯ ИИ (GEMINI 1.5 FLASH / LLAMA 3.3) ---
LLM_SYSTEM_PROMPT = """
You are a technical architectural and fashion photographer. 
Your task: Write a 300-word TECHNICAL prompt for a RAW 9:16 photo with TELESCOPIC CLARITY.

STRICT VISUAL RULES (ZERO TOLERANCE FOR BLUR):
1. INFINITE HIGH-FREQUENCY DETAIL: Every background element must be rendered with 8K architectural precision. Absolutely NO background blur, NO bokeh, NO soft edges. 
2. BACKGROUND OBJECTS: Explicitly describe individual bricks, sharp mortar lines, window frames, glass gaskets, street signs, and concrete grain. Everything in the distance must be surgically sharp.
3. CAMERA: Sony A7R V, 61MP, G-Master lens. Aperture f/22 for maximum depth of field. 
4. CLOTHING: Black 500GSM hoodie. MANDATORY: NO kangaroo pocket, NO zippers, NO drawstrings. Torso is a seamless flat fabric plane. 
5. POSE RULES: Strictly NO hanging arms along the body. Use active, asymmetrical hand placement.
6. SCALE: Front shots = 0.5m distance (85% height). Back shots = 8m distance (30% height).
7. NO AI SMOOTHING: High micro-contrast and raw photographic grain.
"""

def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX
    scene = random.choice(SCENES)
    if side == "front":
        pose = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
        return {"side": "front", "pose": pose, "scene": scene, "ref": REF_FRONT}
    else:
        pose = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
        return {"side": "back", "pose": pose, "scene": scene, "ref": REF_BACK}

async def expand_prompt_via_llm(spec):
    groq_key = os.getenv("GROQ_API_KEY")
    dist = "0.5 meters (Waist-up, 85% height)" if spec['side'] == 'front' else "8.0 meters (Environmental, 30% height)"
    blueprint = f"{spec['side'].upper()} VIEW. Distance: {dist}. Scene: {spec['scene']}. Pose: {spec['pose']}."

    try:
        response = await asyncio.to_thread(requests.post,
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Write a 300-word technical deep-focus prompt for: {blueprint}. Describe background bricks and windows as surgically sharp."}
                ],
                "temperature": 0.5
            }, timeout=30)
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"Hyper-realistic photo, deep focus, f/22, no bokeh, {spec['side']} view, {spec['scene']}"

def submit_job_to_polza(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")
    res = requests.post("https://polza.ai/api/v1/media", headers={"Authorization": f"Bearer {polza_key}"},
        json={
            "model": "black-forest-labs/flux.2-pro", 
            "input": {
                "prompt": prompt, "aspect_ratio": "9:16", "image_resolution": "1K", 
                "images": [{"type": "url", "data": image_url}]
            }, 
            "async": True
        }, timeout=30)
    return res.json().get("id")

async def poll_polza_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")
    for _ in range(60):
        await asyncio.sleep(5)
        try:
            res = await asyncio.to_thread(requests.get, f"https://polza.ai/api/v1/media/{job_id}", headers={"Authorization": f"Bearer {polza_key}"})
            data = res.json()
            if data.get("status") in ["succeeded", "completed", "done"]:
                return data.get("output")[0]
        except: continue
    return None

async def generate_single_image(spec):
    # 1. Получаем технический промпт на 300 слов
    big_prompt = await expand_prompt_via_llm(spec)
    
    # 2. Генерируем изображение
    job_id = await asyncio.to_thread(submit_job_to_polza, big_prompt, spec["ref"])
    url = await poll_polza_job(job_id)
    
    # 3. Сохраняем и чистим ватермарку
    img_data = await asyncio.to_thread(requests.get, url)
    path = f"output/ai_{int(time.time()*1000)}.png"
    os.makedirs("output", exist_ok=True)
    with open(path, "wb") as f: f.write(img_data.content)
    
    with Image.open(path) as im:
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.93))).save(path) # Удаление ватермарки Polza
        
    return path

# --- ГЛАВНАЯ ОЧЕРЕДЬ ГЕНЕРАЦИИ (СПИНА - ЛИЦО - СПИНА) ---
async def generate_all_photos():
    # Ровно 3 фото в нужном порядке
    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]
    
    paths = []
    # Генерируем по очереди
    for spec in specs:
        path = await generate_single_image(spec)
        paths.append(path)
        
    return paths, specs

async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single_image(new_spec)
    return path, new_spec
