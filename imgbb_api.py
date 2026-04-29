import httpx
import base64

# Твой ключ вставлен напрямую
IMGBB_API_KEY = "dfc9d671f50314314265749dc8dcd4a1"

async def upload_images_to_imgbb(image_paths):
    urls = []
    async with httpx.AsyncClient(timeout=60) as client:
        for path in image_paths:
            with open(path, "rb") as f:
                img_data = f.read()
                img_b64 = base64.b64encode(img_data).decode('utf-8')
            
            try:
                response = await client.post(
                    "https://api.imgbb.com/1/upload",
                    data={
                        "key": IMGBB_API_KEY,
                        "image": img_b64
                    }
                )
                res_data = response.json()
                if response.status_code == 200:
                    urls.append(res_data["data"]["url"])
                else:
                    raise Exception(f"Ошибка ImgBB API: {res_data}")
            except Exception as e:
                raise Exception(f"Ошибка при связи с ImgBB: {e}")
    return urls