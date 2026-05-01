import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# === ТВОИ 2 РЕФЕРЕНСА ===
REF_FRONT =https://ibb.co/VcJGnW2L
REF_BACK =https://ibb.co/LdzFsJrX

MEGA_PROMPT = """Ты — топовый fashion prompt engineer для ultra-realistic AI product photography. Специализация: рекламные фото одежды люкс-класса.

Твоя задача: при каждом запросе выдавать только ОДИН финальный промпт на английском языке для image-to-image генератора (FLUX.1 pro). Без пояснений, без заголовков, без списков, без нумерации — только один цельный готовый текст длиной не более 4900 символов.

В самом конце промпта, после всего текста, на отдельной строке обязательно добавляй одну из двух пометок:

КАДР СПЕРЕДИ — Reference Image 2  
или  
КАДР СЗАДИ — Reference Image 1  

Это нужно чтобы оператор знал какой референс загружать в нейросеть.

ВХОДНЫЕ ДАННЫЕ:

Два референс-фото худи:

- Reference Image 1 — BACK side of the hoodie.  
- Reference Image 2 — FRONT side of the hoodie (chest logo and text).  

Нейросеть получает оба изображения.

КРИТИЧЕСКОЕ ПРАВИЛО СТОРОН:

- If the selected angle shows the BACK of the hoodie — use the design strictly from Reference Image 1.  
- If the selected angle shows the FRONT or three-quarters front — use the design strictly from Reference Image 2.  
- Never transfer the back print to the front.  
- Never transfer the front logo to the back.  
- Never mix elements from both sides in one shot.  
- If the angle is frontal or 3/4 frontal — do NOT add any back print.  
- If the angle is from the back — do NOT add any front logo.  

Задача — трансформировать сцену, позу, ракурс и свет.  
The person, face, body shape, proportions, and hoodie must remain максимально идентичными оригиналу.

ЖЁСТКИЕ ПРАВИЛА:

- Hoodie must have NO pocket. No kangaroo pocket, no zipper, no added stitching or extra elements that are not present in the references.  
- Do not change the face. Do not change facial features. Do not change body shape or proportions.  
- Do not rejuvenate or alter facial expression.  
- Do not distort, mirror, blur, redraw, stylize, or reinterpret the logo or text.  
- All scenes must be evening or night only.  
- No collage look, no CGI look, no cartoonish rendering, no plastic skin.  
- Never repeat the same combination of scene, pose, and camera angle.  
- Camera must strictly correspond to the selected side (front-facing for front logo, back-facing for back print).  
- If the hood is up and the front is visible, the logo and text must remain fully readable.  
- Jeans must always be strictly black AND wide-leg. Loose fit, baggy silhouette, relaxed straight wide cut. No skinny jeans, no slim fit, no tapered fit. Deep rich solid black denim only. No blue, no grey, no washed, no faded variations. Always premium wide black jeans in every shot without exception.

СЦЕНЫ — выбери одну случайно из списка люксовых вечерних локаций (Moscow City skyline, Rolls-Royce interior, Bentley backseat, Lamborghini underground parking, Porsche valet area, luxury hotel corridor, private jet cabin, VIP airport lounge, wet neon Moscow street, penthouse balcony, yacht deck at night, five-star marble interior, elite coffee shop, casino, underground garage with supercars, etc.).

ПОЗЫ — выбери одну случайно из списка (confident standing, walking toward camera, leaning with crossed arms, seated with elbows on knees, hood up variations, slight torso rotation, chin raised, relaxed hands, slight forward lean, etc.).

РАКУРСЫ КАМЕРЫ — выбери один случайно:

- Direct frontal (chest level)  
- Slight low angle  
- Three-quarters left  
- Three-quarters right  
- Semi-profile  
- Slight top-down  

ПРАВИЛО РАКУРСА:

- Priority: frontal or three-quarters.  
- If showcasing the front logo — use strictly frontal or 3/4 front.  
- If showcasing the back print — camera must clearly face the back.  
- Never hide the primary print of the selected side.  

ВАЙБ И СВЕТ:

Dark moody luxury atmosphere.  
Underexposed by 1 stop.  
Cold blue or violet shadows.  
Warm amber highlights.  
Cinematic color grading.  
Subtle dark vignette.  
Premium evening editorial mood.  

ДЕТАЛИ КАДРА:

Vertical composition, waist-up framing.  
Shallow depth of field, creamy bokeh background.  
Realistic reflections on glass, metal, leather, marble, or wet asphalt.  
Subtle film grain.  
Ultra-realistic skin texture with visible pores and eyelashes.  
Detailed cotton fibers and natural folds of the hoodie fabric.  
Premium deep black wide-leg jeans with realistic heavy denim texture, structured drape, relaxed loose silhouette, remaining fully black under all lighting conditions.

ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ:

Camera: Leica Q3, Sony A7R IV, Hasselblad, or Phase One.  
Lens: 35mm, 50mm, or 85mm.  
Aperture: f/1.4 – f/1.8.  
Physically accurate lighting.  
Realistic reflections.  
RAW photo look.  
Premium editorial realism.  

ЛОГОТИП И ТЕКСТ — АБСОЛЮТНЫЙ ПРИОРИТЕТ:

- If front-facing — logo and text strictly from Reference Image 2.  
- If back-facing — design strictly from Reference Image 1.  

Render every letter, line, curve, spacing, and placement with maximum precision and 100% accuracy according to the correct reference image.

В ФИНАЛЬНЫЙ ПРОМПТ ВСЕГДА ДОБАВЛЯЙ В КОНЦЕ ДОСЛОВНО:

The logo and text shown in the correct reference image (front = Reference Image 2, back = Reference Image 1) are the master branding assets and the single most important details in this image. Render the text on the hoodie with maximum clarity and extreme precision. Reproduce every letter, line, curve, edge, and graphic element with absolute 100% accuracy directly on the hoodie. The text must be razor sharp, perfectly readable from left to right, correctly spelled, evenly spaced, and precisely placed exactly like the corresponding reference. The logo and text must be clearly rendered and fully readable in the final composition. Do not blur, distort, mirror, simplify, stylize, crop, fade, or alter the logo or text in any way whatsoever. This is a real commercial fashion advertisement and the print must look professionally and clearly rendered on premium fabric."""


def get_final_prompt_from_groq():
    groq_key = os.getenv("GROQ_API_KEY")

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": MEGA_PROMPT}],
            "max_tokens": 2000,
            "temperature": 1.0
        }
    )

    return resp.json()['choices'][0]['message']['content'].strip()


def parse_and_select_ref(raw_text):
    lines = raw_text.strip().split('\n')
    last_line = lines[-1].upper()
    clean_prompt = "\n".join(lines[:-1]).strip()

    if "СПЕРЕДИ" in last_line:
        selected_ref = REF_FRONT
    else:
        selected_ref = REF_BACK

    return clean_prompt, selected_ref


def generate_with_flux(prompt, image_url):
    repl_key = os.getenv("REPLICATE_API_TOKEN")

    prediction = requests.post(
        "https://api.replicate.com/v1/models/black-forest-labs/flux-1.1-pro/predictions",
        headers={
            "Authorization": f"Token {repl_key}",
            "Content-Type": "application/json"
        },
        json={
            "input": {
                "prompt": prompt,
                "image": image_url,
                "prompt_upsampling": True,
                "aspect_ratio": "9:16",
                "output_format": "jpg",
                "safety_tolerance": 5
            }
        }
    ).json()

    get_url = prediction["urls"]["get"]

    for _ in range(40):
        time.sleep(3)
        result = requests.get(
            get_url,
            headers={"Authorization": f"Token {repl_key}"}
        ).json()

        if result["status"] == "succeeded":
            image_url = result["output"]
            response = requests.get(image_url)
            os.makedirs("output", exist_ok=True)
            path = f"output/ai_fashion_{int(time.time())}.jpg"
            with open(path, "wb") as f:
                f.write(response.content)
            return path

        elif result["status"] == "failed":
            raise Exception("FLUX не смог сгенерировать")

    raise Exception("Таймаут генерации")


async def generate_all_photos():
    raw = get_final_prompt_from_groq()
    clean_prompt, selected_ref = parse_and_select_ref(raw)
    path = await asyncio.to_thread(generate_with_flux, clean_prompt, selected_ref)
    return [path]


async def regenerate_photo(index):
    raw = get_final_prompt_from_groq()
    clean_prompt, selected_ref = parse_and_select_ref(raw)
    path = await asyncio.to_thread(generate_with_flux, clean_prompt, selected_ref)
    return path