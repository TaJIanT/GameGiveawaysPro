# -*- coding: utf-8 -*-
import os
import requests

VK_TOKEN = os.environ.get("VK_TOKEN")
VK_GROUP_ID = "152331651"
VK_API_VERSION = "5.193"

def _upload_photo_to_vk(img_url):
    try:
        print(f"🔄 Скачиваем картинку: {img_url}")
        # Добавляем User-Agent, чтобы Steam не отдавал заглушки или мусор
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r_img = requests.get(img_url, headers=headers, timeout=10)
        
        if r_img.status_code != 200:
            print(f"⚠️ Ошибка скачивания картинки (код {r_img.status_code}).")
            return None
            
        img_data = r_img.content
        
        # Динамически получаем реальный тип файла от Steam
        content_type = r_img.headers.get('Content-Type', 'image/jpeg')
        ext = 'png' if 'png' in content_type else 'jpg'
        
        print("🔄 Запрашиваем сервер ВК для загрузки фото...")
        r_server = requests.get("https://api.vk.com/method/photos.getWallUploadServer", params={
            "access_token": VK_TOKEN, "v": VK_API_VERSION, "group_id": VK_GROUP_ID
        }).json()
        
        if "error" in r_server: 
            print(f"⚠️ Ошибка получения сервера ВК: {r_server['error']}")
            return None
        
        upload_url = r_server['response']['upload_url']
        
        # Передаем ВК точное расширение и правильный MIME-тип
        files = {'photo': (f'cover.{ext}', img_data, content_type)}
        r_upload = requests.post(upload_url, files=files).json()

        if "error" in r_upload or not r_upload.get('photo'):
            print(f"⚠️ Ошибка загрузки файла на сервер ВК: {r_upload}")
            return None

        r_save = requests.post("https://api.vk.com/method/photos.saveWallPhoto", data={
            "access_token": VK_TOKEN, "v": VK_API_VERSION, "group_id": VK_GROUP_ID,
            "server": r_upload.get('server'), "photo": r_upload.get('photo'), "hash": r_upload.get('hash')
        }).json()

        if "error" in r_save:
            print(f"⚠️ Ошибка сохранения фото в ВК: {r_save['error']}")
            return None
            
        photo_info = r_save['response'][0]
        attachment_str = f"photo{photo_info['owner_id']}_{photo_info['id']}"
        print(f"✅ Картинка успешно загружена на сервер ВК: {attachment_str}")
        return attachment_str
        
    except Exception as e:
        print(f"⚠️ Критическая ошибка при обработке фото: {e}")
        return None

def send_vk_wall_post(html_text, img_url=None, fallback_url=None):
    if not VK_TOKEN: 
        print("❌ Токен ВК не найден")
        return False
    
    photo_attachment = None
    if img_url: 
        photo_attachment = _upload_photo_to_vk(img_url)
        
    if not photo_attachment and fallback_url: 
        print("⏳ Оригинал не удался. Пробуем загрузить ЗАПАСНУЮ картинку (заглушку)...")
        photo_attachment = _upload_photo_to_vk(fallback_url)

    post_data = {
        "access_token": VK_TOKEN, "v": VK_API_VERSION,
        "owner_id": f"-{VK_GROUP_ID}", "from_group": 1, "message": html_text
    }
    if photo_attachment: 
        post_data["attachments"] = photo_attachment

    print("🔄 Отправляем пост на стену...")
    r = requests.post("https://api.vk.com/method/wall.post", data=post_data).json()
    
    if "error" in r:
        print(f"❌ Ошибка публикации поста: {r['error']}")
    else:
        print("✅ Пост в ВК успешно опубликован!")
        
    return "response" in r
