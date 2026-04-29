import os
import random
from PIL import Image, ImageDraw, ImageFont
from config import PHOTOS_DIR, OUTPUT_DIR, FONT_FILE

MIN_WIDTH = 800
MIN_HEIGHT = 1200


def get_random_photos():
    all_files = [
        os.path.join(PHOTOS_DIR, f)
        for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp"))
    ]

    valid_imgs = []

    for path in all_files:
        try:
            img = Image.open(path)
            w, h = img.size
            if w >= MIN_WIDTH and h >= MIN_HEIGHT:
                valid_imgs.append(path)
        except Exception:
            pass

    if len(valid_imgs) < 5:
        raise ValueError(f"Нужно минимум 5 качественных фото. Сейчас найдено только {len(valid_imgs)}")

    return random.sample(valid_imgs, 5)


def draw_outlined_text(draw, x, y, text, font, fill="white", outline="black", outline_width=2):
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline)

    draw.text((x, y), text, font=font, fill=fill)


def split_into_two_lines(text, draw, font):
    words = text.split()

    if len(words) <= 1:
        return [text, ""]

    best_lines = None
    best_score = None

    for i in range(1, len(words)):
        line1 = " ".join(words[:i])
        line2 = " ".join(words[i:])

        bbox1 = draw.textbbox((0, 0), line1, font=font)
        bbox2 = draw.textbbox((0, 0), line2, font=font)

        w1 = bbox1[2] - bbox1[0]
        w2 = bbox2[2] - bbox2[0]

        score = abs(w1 - w2)

        if best_score is None or score < best_score:
            best_score = score
            best_lines = [line1, line2]

    return best_lines


def create_slides(text, user_id, selected_photos):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    result_paths = []

    for i, path in enumerate(selected_photos):
        img = Image.open(path).convert("RGB")

        if i == 0:
            draw = ImageDraw.Draw(img)
            w, h = img.size

            font_size = max(20, int(h * 0.025))

            try:
                font = ImageFont.truetype(FONT_FILE, font_size)
            except Exception:
                font = ImageFont.load_default()

            lines = split_into_two_lines(text, draw, font)

            line_height = int(font_size * 1.5)
            total_h = line_height * 2
            y = (h - total_h) // 2

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_w = bbox[2] - bbox[0]
                x = (w - text_w) // 2

                draw_outlined_text(
                    draw,
                    x,
                    y,
                    line,
                    font,
                    fill="white",
                    outline="black",
                    outline_width=2
                )
                y += line_height

        out_path = os.path.join(OUTPUT_DIR, f"slide_{user_id}_{i}.jpg")
        img.save(out_path, quality=100, subsampling=0)
        result_paths.append(out_path)

    return result_paths