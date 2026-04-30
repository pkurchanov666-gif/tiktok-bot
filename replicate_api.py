import os
import asyncio
import httpx
import base64
import replicate as replicate_client

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

HOODIE_FRONT = "hoodie_front.jpg"
HOODIE_BACK = "hoodie_back.jpg"

POSES = [
    "standing straight hands in pockets, looking at camera, confident expression, urban street background, golden hour lighting",
    "leaning against concrete wall, casual pose, looking slightly away, city rooftop background, sunset lighting",
    "sitting on wooden stairs, relaxed pose, arms on knees, industrial loft background, soft natural lighting",
    "walking forward dynamic pose, slight motion blur, downtown street background, moody cinematic lighting",
    "arms crossed, serious confident look, clean minimal white background, studio professional lighting",
]

BASE_PROMPT = (
    "photorealistic photo of a young stylish male model wearing this exact hoodie, "
    "{pose}, "
    "fashion editorial style, high end clothing brand, 8k resolution, sharp details, "
    "professional fashion photography, vogue magazine style"
)

NEGATIVE_PROMPT = (
    "ugly, blurry, low quality, distorted face, deformed hands, "
    "extra limbs, bad anatomy, watermark, text, logo, nsfw, nude"
)


def load_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = path.split(".")[-1].lower()
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


async def generate_photo(index: int) -> str:
    pose = POSES[index]
    prompt = BASE_PROMPT.format(pose=pose)
    hoodie_b64 = load_image_b64(HOODIE_FRONT)

    client = replicate_client.Client(api_token=REPLICATE_API_TOKEN)

    output = await asyncio.to_thread(
        client.run,
        "stability-ai/stable-diffusion-img2img:15a3689ee13b0d2616e98820eca31d4af4a36106d57a9048c8cb9b8f2b85b2a9",
        input={
            "image": hoodie_b64,
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "prompt_strength": 0.65,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
    )

    image_url = output[0] if isinstance(output, list) else str(output)

    async with httpx.AsyncClient(timeout=60) as client_http:
        response = await client_http.get(image_url)

    os.makedirs("output", exist_ok=True)
    temp_path = f"output/ai_photo_{index}.jpg"

    with open(temp_path, "wb") as f:
        f.write(response.content)

    return temp_path


async def generate_all_photos() -> list:
    paths = []
    for i in range(5):
        path = await generate_photo(i)
        paths.append(path)
    return paths


async def regenerate_photo(index: int) -> str:
    return await generate_photo(index)