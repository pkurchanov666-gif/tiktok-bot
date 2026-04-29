import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PHOTOS_DIR = "photos"
FONTS_DIR = "fonts"
OUTPUT_DIR = "output"
FONT_FILE = os.path.join(FONTS_DIR, "font.ttf")
VIDEO_SIZE = (1080, 1920)
SLIDE_DURATION = 3
SLIDE_COUNT = 5
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")