from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

async def generate_text():
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Generate 1 short motivation quote for TikTok, max 7 words, English, no emojis, no quotes."}]
    )
    result = resp.choices[0].message.content
    return result.strip().replace('"', '')
