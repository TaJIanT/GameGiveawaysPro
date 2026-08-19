# -*- coding: utf-8 -*-
import os
import requests

VK_TOKEN = os.environ.get("VK_TOKEN")
VK_GROUP_ID = "152331651"
VK_API_VERSION = "5.193"

def _upload_photo_to_vk(img_url):
    try:
        img_data = requests.get(img_url, timeout=10).content
        
        # Запрашиваем сервер для загрузки
        r_server = requests.get("https://api.vk.com/method/photos.getWallUploadServer", params={
            "access_token": VK_TOKEN, "v": VK_API_VERSION, "group_id": VK_GROUP_ID
        }).json()
        if "error" in r_server: return None
        
        # Отправляем файл
        upload_url = r_server['response']['upload_url']
        files = {'photo': ('cover.jpg', img_data, 'image/jpeg')}
        r_upload = requests.post(upload_url, files=files).json()

        # Сохраняем фото
        r_save = requests.post("https://api.vk.com/method/photos.saveWallPhoto", data={
            "access_token": VK_TOKEN, "v": VK_API_VERSION, "group_id": VK_GROUP_ID,
            "server": r_upload.get('server'), "photo": r_upload.get('photo'), "hash": r_upload.get('hash')
        }).json()

        if "error" not in r_save:
            photo_info = r_save['response'][0]
            return f"photo{photo_info['owner_id']}_{photo_info['id']}"
        return None
    except Exception as e:
        print(f"⚠️ Ошибка загрузки фото: {e}")
        return None

def send_vk_wall_post(html_text, img_url=None, fallback_url=None):
    if not VK_TOKEN: return False
    
    # Пытаемся загрузить оригинал, если не вышло — заглушку
    photo_attachment = None
    if img_url: photo_attachment = _upload_photo_to_vk(img_url)
    if not photo_attachment and fallback_url: photo_attachment = _upload_photo_to_vk(fallback_url)

    post_data = {
        "access_token": VK_TOKEN, "v": VK_API_VERSION,
        "owner_id": f"-{VK_GROUP_ID}", "from_group": 1, "message": html_text
    }
    if photo_attachment: post_data["attachments"] = photo_attachment

    r = requests.post("https://api.vk.com/method/wall.post", data=post_data).json()
    return "response" in r
