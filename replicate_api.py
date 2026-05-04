import os
import time
import random
import requests
import asyncio
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# --- НАСТРОЙКИ ПУТЕЙ ---
SAVE_DIR = "generations"  # Папка для готовых фото
REF_FRONT = "https://i.ibb.co/gLm8qMzr/5451731499716646851-1.jpg"
REF_BACK = "https://i.ibb.co/TMBfNb1x/5451731499716647027.jpg"

# --- БАЗА ДАННЫХ ДЛЯ РАНДОМА ЧЕРЕЗ PYTHON (РЕЖИССУРА) ---
SCENES = [
    "premium minimalist city street", "exclusive underground parking level", 
    "contemporary art gallery exterior", "luxury hotel driveway entrance", 
    "high-tech business district plaza", "modernist pedestrian urban passage", 
    "premium airport terminal exterior"
]

MATERIALS = [
    "polished basalt stone", "raw industrial concrete", "304-grade brushed steel", 
    "tempered reflective glass", "weathered dark brick", "smooth grey marble", 
    "textured asphalt with crystalline bits", "dark granite architectural slabs"
]

LIGHTING = [
    "3000K warm golden ambient light from shop windows", 
    "6000K cool-white clinical LED strip lighting",
    "4500K neutral evening street lamps with realistic falloff",
    "natural blue hour twilight with soft atmospheric sky reflections",
    "mixed high-contrast urban lighting with deep logical shadows"
]

DETAILS = [
    "sharp reflections on wet pavement puddles", "visible rubber gaskets on glass window frames", 
    "clear metal rivets on structural steel beams", "distant glowing neon commercial signs",
    "detailed texture of stone sidewalk cracks", "sharp industrial ceiling pipes and vents",
    "individual mortar lines between bricks", "reflective metal handrails with visible welds"
]

# --- 10 АКТИВНЫХ ПОЗ (FRONT) - ПОРЯДКОВЫЙ ПЕРЕБОР ---
FRONT_POSES = [
    "one hand actively gripping the edge of the hood near the temple, elbow pointed out", # 1
    "both hands raised adjusting the sides of the hood, elbows wide and lifted", # 2
    "one hand touching the neck area of the hoodie, other forearm bent across waistband", # 3
    "one hand pulling the hood slightly forward over the forehead, thumb in jeans pocket", # 4
    "one hand adjusting the sleeve cuff, other hand raised to grab the hood seam", # 5
    "torso angled slightly, one hand resting on the back of the neck under the hood", # 6
    "both hands high holding the sides of the hood, elbows wide, chest fully open", # 7
    "mid-stride toward camera, one hand touching the hood, other arm in mid-swing", # 8
    "one shoulder dropped, one hand touching the jawline, other hand in jeans pocket", # 9
    "both hands reaching up pulling the hood down towards the face, strong silhouette" # 10
]

# --- 10 АКТИВНЫХ ПОЗ (BACK) - ПОРЯДКОВЫЙ ПЕРЕБОР ---
BACK_POSES = [
    "back facing camera, one hand raised resting on the back of the head over the hood", # 1
    "walking away into the depth of the scene, hood up, one hand touching the hood from behind", # 2
    "standing still facing away, both hands raised adjusting the hood sides, elbows out", # 3
    "back view, shoulders angled, one hand touching the hood seam near the neck", # 4
    "leaning with one shoulder against a concrete pillar, back fully visible, hand on hood", # 5
    "moving away in a three-quarters back stance, one hand adjusting the hood", # 6
    "back fully visible, head slightly tilted, arms active adjusting the hoodie hem", # 7
    "slow walk away from camera, one arm active near the hood, showing depth", # 8
    "standing with back to lens, arms slightly bent out to show hoodie width", # 9
    "three-quarters back view, face hidden by hood, hand touching the hood seam" # 10
]

# Глобальные счетчики поз (сохраняются пока запущен скрипт)
CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0

# --- СИСТЕМНЫЙ ПРОМПТ ДЛЯ ИИ (ТЕХНИЧЕСКОЕ ЗАДАНИЕ) ---
LLM_SYSTEM_PROMPT = """
You are a technical architectural and fashion photographer. 
Your task: Write a 300-word TECHNICAL prompt for a RAW 9:16 photo with TELESCOPIC CLARITY.

STRICT TECHNICAL RULES (ZERO TOLERANCE FOR BLUR):
1. INFINITE HIGH-FREQUENCY DETAIL: Every background element must be rendered with 8K architectural precision. Absolutely NO background blur, NO bokeh. 
2. BACKGROUND OBJECTS: Explicitly describe individual bricks, sharp mortar lines, window frames, glass gaskets, street signs, and concrete grain. Everything in the distance must be surgically sharp.
3. CAMERA: Sony A7R V, 61MP, f/22 aperture for maximum edge-to-edge sharpness across the entire frame. 
4. CLOTHING: Black 500GSM hoodie. MANDATORY: NO kangaroo pocket, NO zippers, NO drawstrings. Seamless flat torso fabric. Extra-wide baggy black denim jeans.
5. LOGO: High-density silk-screen print, raised ink texture, 100% sharp and readable. 
6. POSE RULES: Strictly NO hanging arms along the body. Use active, asymmetrical hand placement.
7. NO AI SMOOTHING: High micro-contrast and raw photographic grain.
"""

def get_next_spec(side):
    """Выбирает параметры через Python для исключения повторов ИИ."""
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX
    
    spec = {
        "side": side,
        "scene": random.choice(SCENES),
        "material": random.choice(MATERIALS),
        "lighting": random.choice(LIGHTING),
        "detail": random.choice(DETAILS),
        "seed": random.randint(100000, 999999),
        "ref": REF_FRONT if side == "front" else REF_BACK
    }
    
    if side == "front":
        spec["pose"] = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
    else:
        spec["pose"] = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
        
    return spec

async def expand_prompt_via_llm(spec):
    """Просит ИИ расписать ТЗ от Python на 300 слов."""
    groq_key = os.getenv("GROQ_API_KEY")
    
    # Разница в дистанции: фронт - 0.5м, спина - 8.0м
    dist = "0.5 meters (Waist-up framing, 85% height)" if spec['side'] == 'front' else "8.0 meters (Environmental wide shot, 30% height)"
    
    blueprint = (
        f"VIEW: {spec['side'].upper()}. DISTANCE: {dist}. "
        f"LOCATION: {spec['scene']}. POSE: {spec['pose']}. "
        f"REQUIRED MATERIALS: {spec['material']}. "
        f"REQUIRED LIGHTING: {spec['lighting']}. "
        f"REQUIRED BG DETAIL: {spec['detail']}."
    )

    try:
        response = await asyncio.to_thread(requests.post,
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Generate a 300-word technical deep-focus prompt for this blueprint: {blueprint}. Ensure background is surgically sharp."}
                ],
                "temperature": 0.5
            }, timeout=30)
        return response.json()["choices"][0]["message"]["content"].strip()
    except:
        return f"Hyper-realistic photo, f/22, no bokeh, {spec['side']} view, {spec['scene']}, {spec['material']}"

def submit_job_to_polza(prompt, image_url):
    """Отправляет запрос в Polza (Nano Banano 2)."""
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
    """Ожидание готовности картинки."""
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
    """Полный цикл: ИИ-промпт -> Генерация -> Сохранение -> Кроп."""
    big_prompt = await expand_prompt_via_llm(spec)
    job_id = await asyncio.to_thread(submit_job_to_polza, big_prompt, spec["ref"])
    url = await poll_polza_job(job_id)
    
    img_data = await asyncio.to_thread(requests.get, url)
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}.png")
    
    with open(path, "wb") as f: f.write(img_data.content)
    with Image.open(path) as im:
        w, h = im.size
        # Удаляем ватермарку (нижние 7%)
        im.crop((0, 0, w, int(h * 0.93))).save(path)
    return path

# --- ГЛАВНАЯ ФУНКЦИЯ (ВЫДАЕТ 3 ФОТО: СПИНА - ЛИЦО - СПИНА) ---
async def generate_all_photos():
    """Генерирует 3 фото в строгом порядке с разной дистанцией."""
    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]
    
    paths = []
    for spec in specs:
        path = await generate_single_image(spec)
        paths.append(path)
        
    return paths, specs

async def regenerate_photo(index, current_specs):
    """Регенерация одного фото из пачки."""
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single_image(new_spec)
    return path, new_spec
