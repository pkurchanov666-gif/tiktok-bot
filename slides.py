import os
import random
from PIL import Image
from config import PHOTOS_DIR, OUTPUT_DIR, SLIDE_COUNT, VIDEO_SIZE


def get_random_photos(count: int = SLIDE_COUNT):
    all_photos = [
        os.path.join(PHOTOS_DIR, f)
        for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if len(all_photos) < count:
        raise ValueError(f"Нужно минимум {count} фото, найдено {len(all_photos)}")

    return random.sample(all_photos, count)


def resize_photo(img: Image.Image, size: tuple = VIDEO_SIZE) -> Image.Image:
    target_w, target_h = size
    target_ratio = target_w / target_h

    img_w, img_h = img.size
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        new_h = img_h
        new_w = int(img_h * target_ratio)
    else:
        new_w = img_w
        new_h = int(img_w / target_ratio)

    left = (img_w - new_w) // 2
    top = (img_h - new_h) // 2
    right = left + new_w
    bottom = top + new_h

    img = img.crop((left, top, right, bottom))
    img = img.resize(size, Image.LANCZOS)
    return img


def create_slides(text: str, user_id: int, photos: list):
    # text оставили в сигнатуре, чтобы не ломать bot.py,
    # но на фото больше ничего НЕ рисуем
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    paths = []

    for i, photo_path in enumerate(photos):
        img = Image.open(photo_path).convert("RGB")
        img = resize_photo(img)

        output_path = os.path.join(OUTPUT_DIR, f"slide_{user_id}_{i}.jpg")
        img.save(output_path, quality=95)
        paths.append(output_path)

    return paths
