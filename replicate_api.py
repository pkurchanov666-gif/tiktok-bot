import os
import asyncio
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Берём токен из любого источника
hf_token = (
    os.environ.get("HF_TOKEN") or
    os.getenv("HF_TOKEN")
)

POSES = [
    "standing straight, hands in pockets, urban street",
    "leaning against wall, looking away, city background",
    "sitting on stairs, relaxed pose, urban environment",
    "walking forward, city street background",
    "arms crossed, serious look, minimal background"
]

BASE_PROMPT = (
    "photorealistic fashion photo of a young stylish male model "
    "wearing a high-end streetwear hoodie, {pose}, "
    "fashion photography, 8k resolution, sharp details"
)


async def generate_photo(index):
    token = os.environ.get("HF_TOKEN") or os.getenv("HF_TOKEN")

    if not token:
        raise Exception("HF_TOKEN не найден!")

    client = InferenceClient(
        "black-forest-labs/FLUX.1-schnell",
        token=token
    )

    pose = POSES[index]
    prompt = BASE_PROMPT.format(pose=pose)

    try:
        image = await asyncio.to_thread(
            client.text_to_image,
            prompt=prompt
        )
        os.makedirs("output", exist_ok=True)
        path = f"output/ai_photo_{index}.jpg"
        image.save(path)
        return path
    except Exception as e:
        raise Exception(f"HF Error: {e}")


async def generate_all_photos():
    return [await generate_photo(i) for i in range(5)]


async def regenerate_photo(index):
    return await generate_photo(index)
