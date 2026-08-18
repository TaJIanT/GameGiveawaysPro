# -*- coding: utf-8 -*-
import os
import re
import requests

VK_TOKEN = os.environ.get("VK_TOKEN")
VK_GROUP_ID = "152331651"  # Твоя группа
VK_API_VERSION = "5.193"

def clean_html(raw_html):
    """ВК не поддерживает HTML-теги, поэтому вычищаем <b>, <i>, <a> и т.д."""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def send_vk_wall_post(html_text, img_url):
    """Публикует запись с картинкой на стене группы ВКонтакте."""
    if not VK_TOKEN:
        print("❌ Ошибка: VK_TOKEN не найден. Проверьте секреты GitHub и .yml файл.")
        return False

    text = clean_html(html_text)
    
    try:
        # 1. Загружаем саму картинку
        img_data = requests.get(img_url, timeout=10).content

        # 2. Получаем сервер ВК для загрузки фото
        r_server = requests.get("https://api.vk.com/method/photos.getWallUploadServer", params={
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "group_id": VK_GROUP_ID
        }).json()

        if "error" in r_server:
            print(f"❌ Ошибка ВК (getWallUploadServer): {r_server['error']}")
            return False

        upload_url = r_server['response']['upload_url']

        # 3. Отправляем фото на сервер
        files = {'photo': ('cover.jpg', img_data, 'image/jpeg')}
        r_upload = requests.post(upload_url, files=files).json()

        # 4. Сохраняем фото в ВК
        r_save = requests.post("https://api.vk.com/method/photos.saveWallPhoto", data={
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "group_id": VK_GROUP_ID,
            "server": r_upload.get('server'),
            "photo": r_upload.get('photo'),
            "hash": r_upload.get('hash')
        }).json()

        photo_info = r_save['response'][0]
        photo_attachment = f"photo{photo_info['owner_id']}_{photo_info['id']}"

        # 5. Публикуем пост на стене
        r_post = requests.post("https://api.vk.com/method/wall.post", data={
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "owner_id": f"-{VK_GROUP_ID}",  # Минус обязателен для групп!
            "from_group": 1,
            "message": text,
            "attachments": photo_attachment
        }).json()

        if "response" in r_post:
            print(f"✅ Успешно отправлено в ВК: post_id {r_post['response']['post_id']}")
            return True
        else:
            print(f"❌ Ошибка ВК (wall.post): {r_post.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при отправке в ВК: {e}")
        return False
      
