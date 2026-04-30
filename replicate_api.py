import os
import asyncio
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
hf_token = os.getenv("HF_TOKEN")
client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=hf_token)

POSES = [
    "standing straight, hands in pockets",
    "leaning against wall, looking away",
    "sitting on stairs, relaxed pose",
    "walking forward, city background",
    "arms crossed, serious look"
]

async def generate_photo(index):
    if not hf_token: raise Exception("HF_TOKEN не найден в .env")
    prompt = f"photorealistic fashion photo of a young male model wearing hoodie, {POSES[index]}, urban street style, 8k"
    try:
        image = await asyncio.to_thread(client.text_to_image, prompt=prompt)
        os.makedirs("output", exist_ok=True)
        path = f"output/ai_photo_{index}.jpg"
        image.save(path)
        return path
    except Exception as e: raise Exception(f"HF Error: {e}")

async def generate_all_photos():
    return [await generate_photo(i) for i in range(5)]

async def regenerate_photo(index):
    return await generate_photo(index)
