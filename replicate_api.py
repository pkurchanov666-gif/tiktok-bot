import replicate
import httpx
import os
import base64
import asyncio

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN or ""

HOODIE_FRONT = "hoodie_front.jpg"
HOODIE_BACK = "hoodie_back.jpg"

POSES = [
    "confident young male model standing straight, hands in pockets, urban street, fashion photography, photorealistic",
    "young male model leaning against wall, casual pose, looking away, lifestyle photography, photorealistic",
    "young male model sitting on stairs, relaxed pose, urban environment, aesthetic photography, photorealistic",
    "young male model walking forward, dynamic pose, city street, fashion editorial, photorealistic",
    "young male model arms crossed, serious look, minimalist background, luxury fashion, photorealistic",
]


def load_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = path.split(".")[-1].lower()
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


async def generate_photo(index: int) -> str:
    pose = POSES[index]
    hoodie_b64 = load_image_b64(HOODIE_FRONT)

    output = await asyncio.to_thread(
        replicate.run,
        "stability-ai/stable-diffusion-img2img:15a3689ee13b0d2616e98820eca31d4af4a36106d57a9048c8cb9b8f2b85b2a9",
        input={
            "image": hoodie_b64,
            "prompt": f"young male model wearing this exact hoodie, {pose}, high quality, 8k, detailed",
            "negative_prompt": "ugly, blurry, low quality, distorted, deformed, nude, nsfw",
            "prompt_strength": 0.65,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
    )

    image_url = output[0] if isinstance(output, list) else str(output)

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(image_url)

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