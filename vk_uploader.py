# -*- coding: utf-8 -*-
import os
import re
import requests

VK_TOKEN = os.environ.get("VK_TOKEN")
VK_GROUP_ID = "152331651"  # Твоя группа
VK_API_VERSION = "5.193"

def clean_html(raw_html):
    """Вычищаем HTML-теги для ВКонтакте"""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def _upload_photo_to_vk(img_url):
    """Скачивает картинку по ссылке и загружает её на сервер ВК"""
    try:
        img_data = requests.get(img_url, timeout=10).content
        
        r_server = requests.get("https://api.vk.com/method/photos.getWallUploadServer", params={
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "group_id": VK_GROUP_ID
        }).json()

        if "error" in r_server:
            print(f"⚠️ Ошибка сервера ВК: {r_server['error'].get('error_msg')}")
            return None

        upload_url = r_server['response']['upload_url']
        files = {'photo': ('cover.jpg', img_data, 'image/jpeg')}
        r_upload = requests.post(upload_url, files=files).json()

        r_save = requests.post("https://api.vk.com/method/photos.saveWallPhoto", data={
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "group_id": VK_GROUP_ID,
            "server": r_upload.get('server'),
            "photo": r_upload.get('photo'),
            "hash": r_upload.get('hash')
        }).json()

        if "error" not in r_save:
            photo_info = r_save['response'][0]
            return f"photo{photo_info['owner_id']}_{photo_info['id']}"
        else:
            print(f"⚠️ ВК отклонил сохранение фото: {r_save['error'].get('error_msg')}")
            return None
            
    except Exception as e:
        print(f"⚠️ Ошибка при обработке картинки {img_url}: {e}")
        return None

def send_vk_wall_post(html_text, img_url=None, fallback_url=None):
    """Публикует пост. Пытается загрузить оригинал, при ошибке берет твою заглушку."""
    if not VK_TOKEN:
        print("❌ Ошибка: VK_TOKEN не найден.")
        return False

    text = clean_html(html_text)
    photo_attachment = None
    
    # 1. Пытаемся загрузить оригинальную обложку
    if img_url:
        print(f"⏳ Загружаем основную обложку игры...")
        photo_attachment = _upload_photo_to_vk(img_url)
        
    # 2. Если обложка не загрузилась, но есть заглушка платформы — грузим её
    if not photo_attachment and fallback_url:
        print(f"⏳ Оригинал не прошел. Загружаем твой ФИРМЕННЫЙ БАННЕР...")
        photo_attachment = _upload_photo_to_vk(fallback_url)

    # 3. Публикуем сам пост
    try:
        post_data = {
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "owner_id": f"-{VK_GROUP_ID}",
            "from_group": 1,
            "message": text
        }
        
        if photo_attachment:
            post_data["attachments"] = photo_attachment

        r_post = requests.post("https://api.vk.com/method/wall.post", data=post_data).json()

        if "response" in r_post:
            mode = "с картинкой" if photo_attachment else "только текст (ошибка всех картинок)"
            print(f"✅ Успешно отправлено в ВК ({mode}): post_id {r_post['response']['post_id']}")
            return True
        else:
            print(f"❌ Ошибка ВК (wall.post): {r_post.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Критическая ошибка при отправке в ВК: {e}")
        return False
