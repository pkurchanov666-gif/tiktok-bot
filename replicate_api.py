import os
import asyncio
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

POSES = [
    "standing straight, hands in pockets, urban street",
    "leaning against wall, looking away, city background",
    "sitting on stairs, relaxed pose, urban environment",
    "walking forward, city street background",
    "arms crossed, serious look, minimal background"
]

async def generate_photo(index):
    token = os.environ.get("HF_TOKEN") or os.getenv("HF_TOKEN")

    if not token:
        all_keys = list(os.environ.keys())
        raise Exception(f"HF_TOKEN не найден. Все ключи: {all_keys}")

    client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=token)

    prompt = (
        f"photorealistic fashion photo of a young stylish male model "
        f"wearing a high-end streetwear hoodie, {POSES[index]}, "
        f"fashion photography, 8k resolution, sharp details"
    )

    image = await asyncio.to_thread(client.text_to_image, prompt=prompt)

    os.makedirs("output", exist_ok=True)
    path = f"output/ai_photo_{index}.jpg"
    image.save(path)
    return path

async def generate_all_photos():
    return [await generate_photo(i) for i in range(5)]

async def regenerate_photo(index):
    return await generate_photo(index)