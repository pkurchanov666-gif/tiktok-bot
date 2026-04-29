from PIL import Image
import os

for f in os.listdir('photos'):
    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
        img = Image.open(os.path.join('photos', f))
        print(f, img.size, img.mode)