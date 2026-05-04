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

FRONT_SCENES = [
    "Интерьер премиального автомобиля с кожаным салоном",
    "Современный стеклянный лифт бизнес-центра",
    "Салон автомобиля с панорамной крышей"
]

BACK_SCENES = [
    "Современная городская улица с каменной плиткой",
    "Подземная парковка с гладким бетоном",
    "Современная бизнес-площадь со стеклянными фасадами",
    "Вход в люксовый отель с гранитной отделкой"
]

FRONT_POSES = [
    "правая рука держит край капюшона у виска, левая рука в кармане джинсов",
    "обе руки подняты и поправляют капюшон",
    "правая рука тянет капюшон вперед, левая согнута у пояса",
    "левая рука в кармане, правая касается воротника худи"
]

BACK_POSES = [
    "правая рука лежит на затылке поверх капюшона, левая согнута у бедра",
    "правая рука касается шва капюшона сзади, левая расслаблена",
    "обе руки подняты и поправляют капюшон",
    "правая рука на капюшоне, левая немного отведена от тела"
]

CURRENT_FRONT_INDEX = 0
CURRENT_BACK_INDEX = 0


def get_next_spec(side):
    global CURRENT_FRONT_INDEX, CURRENT_BACK_INDEX

    if side == "front":
        scene = random.choice(FRONT_SCENES)
        pose = FRONT_POSES[CURRENT_FRONT_INDEX % len(FRONT_POSES)]
        CURRENT_FRONT_INDEX += 1
        ref = REF_FRONT
    else:
        scene = random.choice(BACK_SCENES)
        pose = BACK_POSES[CURRENT_BACK_INDEX % len(BACK_POSES)]
        CURRENT_BACK_INDEX += 1
        ref = REF_BACK

    return {
        "side": side,
        "scene": scene,
        "pose": pose,
        "seed": random.randint(1, 999999),
        "ref": ref
    }


def build_prompt(spec):

    camera_block = (
        "Ultra-realistic RAW 9:16 photograph captured on a Sony A7R V "
        "with a 35mm lens set to f/11 aperture to ensure deep focus across the entire frame. "
        "There is absolutely no background blur and no bokeh. "
        "Every distant surface and architectural line must remain sharp and clearly resolved. "
    )

    skin_block = (
        "Natural human skin tones must be preserved with visible pores and realistic softness. "
        "Skin texture must not appear metallic or artificial. "
        "No reflective chrome-like highlights and no plastic gloss. "
    )

    hoodie_block = (
        "The hoodie is constructed from heavy 500GSM black cotton fabric with clearly visible textile weave. "
        "Fabric folds must appear natural and consistent with body movement. "
        "STRICT RULE: NO kangaroo pocket, NO front pouch, NO zippers, NO drawstrings. "
        "The entire hoodie torso must remain smooth and uninterrupted with no stitching indicating a pocket. "
    )

    jeans_block = (
        "The jeans are wide black denim with relaxed loose fit. "
        "The fabric must drape naturally around the hips, thighs and knees. "
        "Subtle creases and visible stitching around waistband and pockets must be present. "
        "Denim texture should show realistic grain without stiffness. "
    )

    if spec["side"] == "front":

        framing_block = (
            "FRONT VIEW. Camera distance exactly 0.7 meters. "
            "Framing from head to knees. "
            "The subject occupies approximately 80–85 percent of vertical frame height. "
            "Upper portion of the wide jeans must be clearly visible. "
            "The chest logo must be sharp, clean-edged and fully readable without distortion. "
        )

    else:

        framing_block = (
            "BACK VIEW. Camera distance MUST be exactly 10 meters. "
            "This distance is mandatory and must not be closer. "
            "Wide environmental composition. "
            "The subject occupies approximately 25–30 percent of vertical frame height. "
            "The surrounding environment must visually dominate the frame. "
            "Hood fully up. Face not visible. "
        )

    environment_block = (
        f"Scene: {spec['scene']}. "
        "Background surfaces such as pavement seams, building edges, glass reflections "
        "and structural lines must remain crisp and detailed. "
        "Lighting is neutral urban light around 4500K with balanced exposure and natural shadow falloff. "
    )

    pose_block = f"Pose: {spec['pose']}. "

    return (
        camera_block +
        skin_block +
        hoodie_block +
        jeans_block +
        framing_block +
        environment_block +
        pose_block
    )


def submit_job(prompt, image_url):
    polza_key = os.getenv("POLZA_API_KEY")

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
                "images": [{"type": "url", "data": image_url}]
            },
            "async": True
        },
        timeout=30
    )

    data = response.json()
    job_id = data.get("id") or data.get("task_id")
    if not job_id:
        raise Exception(f"Polza error: {data}")

    return job_id


async def poll_job(job_id):
    polza_key = os.getenv("POLZA_API_KEY")

    for _ in range(60):
        await asyncio.sleep(5)

        res = await asyncio.to_thread(
            requests.get,
            f"https://polza.ai/api/v1/media/{job_id}",
            headers={"Authorization": f"Bearer {polza_key}"},
            timeout=30
        )

        data = res.json()
        status = (data.get("status") or "").lower()

        if status in ["succeeded", "completed", "done"]:
            output = data.get("output")
            if isinstance(output, list) and output:
                return output[0]

    raise Exception("Generation timeout")


async def generate_single(spec):
    prompt = build_prompt(spec)
    job_id = await asyncio.to_thread(submit_job, prompt, spec["ref"])
    url = await poll_job(job_id)

    img = await asyncio.to_thread(requests.get, url)

    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f"ai_{int(time.time()*1000)}.png")

    with open(path, "wb") as f:
        f.write(img.content)

    with Image.open(path) as im:
        w, h = im.size
        im.crop((0, 0, w, int(h * 0.93))).save(path)

    return path


async def generate_all_photos():
    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]

    paths = []
    for spec in specs:
        path = await generate_single(spec)
        paths.append(path)
        async def generate_all_photos():
    sides = ["back", "front", "back"]
    specs = [get_next_spec(side) for side in sides]

    paths = []
    for spec in specs:
        path = await generate_single(spec)
        paths.append(path)

    return paths, specs


async def regenerate_photo(index, current_specs):
    side = current_specs[index]["side"]
    new_spec = get_next_spec(side)
    path = await generate_single(new_spec)
    return path, new_spec

    return paths, specs
