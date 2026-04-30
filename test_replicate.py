import os
import replicate
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("REPLICATE_API_TOKEN")
client = replicate.Client(api_token=token)

# Тестируем рабочую модель
output = client.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": "young male model wearing black hoodie, urban street, fashion photography, 8k",
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "jpg",
    }
)

print("Результат:", output)