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

def send_vk_wall_post(html_text, game_link):
    """Публикует запись на стене группы с автоматическим сниппетом (карточкой-ссылкой)"""
    if not VK_TOKEN:
        print("❌ Ошибка: VK_TOKEN не найден. Проверьте секреты GitHub.")
        return False

    text = clean_html(html_text)
    
    try:
        # Отправляем текст и ПЕРЕДАЕМ ССЫЛКУ В ATTACHMENTS
        r_post = requests.post("https://api.vk.com/method/wall.post", data={
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "owner_id": f"-{VK_GROUP_ID}",  # Минус обязателен для групп!
            "from_group": 1,
            "message": text,
            "attachments": game_link  # <--- Вот эта магия создаст карточку с картинкой!
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
        
