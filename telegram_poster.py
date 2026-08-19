# -*- coding: utf-8 -*-
import os, sys, time, random, requests
from api import GameAPI
from notifications import NotificationManager
from vk_uploader import send_vk_wall_post

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
APP_LINK = "https://github.com/TaJIanT/GameGiveawaysPro/releases/latest"
VK_GROUP_URL = "https://vk.com/club152331651"
TG_CHANNEL_URL = "https://t.me/ggpro_free_games"

FALLBACK_IMAGES = {
    "steam": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091450.png",
    "epic": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091513.png",
    "steam_keys": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091548.png",
    "gog": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091635.png",
    "roblox": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091659.png",
    "gacha": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091811.png",
    "gacha_sale": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091948.png",
    "vkplay": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_092147.png",
    "mobile": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_092302.png",
    "default": "https://raw.githubusercontent.com/TaJIanT/GameGiveawaysPro/main/images/IMG_20260819_091450.png"
}

def process_and_send_game(game):
    title = game.get("title", "Game")
    link = game.get("link", "")
    img_url = game.get("image", "")
    platform_key = game.get("platformkey", "").lower()
    
    # Логика заглушки
    fallback_category = "default"
    if "roblox" in platform_key: fallback_category = "roblox"
    elif "steam" in platform_key and "key" in title.lower(): fallback_category = "steam_keys"
    elif "steam" in platform_key: fallback_category = "steam"
    elif "epic" in platform_key: fallback_category = "epic"
    elif "gog" in platform_key: fallback_category = "gog"
    elif "gacha" in platform_key: fallback_category = "gacha" if "code" in title.lower() else "gacha_sale"
    elif "vkplay" in platform_key: fallback_category = "vkplay"
    elif "mobile" in platform_key: fallback_category = "mobile"
    
    fallback_url = FALLBACK_IMAGES.get(fallback_category, FALLBACK_IMAGES["default"])

    # Отправка в ТГ
    caption = f"🔥 <b>{title}</b>\n\n✈️ ТГ: {TG_CHANNEL_URL}"
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", json={
            "chat_id": TG_CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"
        })
    except: pass

    # Отправка в ВК (с загрузкой фото или заглушкой)
    vk_text = f"🎮 Новая раздача: {title}\n\n👉 {link}\n\n✈️ Наш ТГ: {TG_CHANNEL_URL}"
    send_vk_wall_post(vk_text, img_url, fallback_url)

def main():
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager()
    games = api.fetch_gamerpower_pc(10)
    for game in games:
        process_and_send_game(game)
        time.sleep(2)

if __name__ == '__main__': main()
