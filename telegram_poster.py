# -*- coding: utf-8 -*-
import os
import sys
import requests
from api import GameAPI
from notifications import NotificationManager

# Теперь токены берутся из защищенных секретов GitHub
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

def send_to_telegram(game):
    title = game.get("title", "Неизвестная игра")
    platform = game.get("platform", "PC")
    worth = float(game.get("worth", 0) or 0)
    link = game.get("link", "")
    img_url = game.get("image", "")
    
    hashtag_plat = platform.replace(" ", "")
    caption = f"🔥 <b>{title}</b>\n\n🎮 <b>Платформа:</b> {platform}\n"
    
    if worth > 0:
        caption += f"💰 <b>Стоимость:</b> <s>${worth:.2f}</s> ➡️ <b>Бесплатно!</b>\n\n"
    else:
        caption += f"💰 <b>Стоимость:</b> <b>Бесплатно!</b>\n\n"
    
    caption += f"👉 <a href='{link}'><b>Забрать игру</b></a>\n\n#раздача #{hashtag_plat} #игры"

    try:
        if img_url:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            payload = {"chat_id": TG_CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "HTML"}
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            payload = {"chat_id": TG_CHAT_ID, "text": caption, "parse_mode": "HTML", "disable_web_page_preview": False}
            
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Отправлено: {title}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def fetch_all_freebies(api):
    games = []
    try: games.extend(api.fetch_cheapshark_free(12))
    except: pass
    try: games.extend(api.fetch_gamerpower_pc(15))
    except: pass
    try: games.extend(api.fetch_gamerpower_loot(15))
    except: pass
    return [g for g in games if str(g.get("price", "")).strip().upper() == "FREE"]

def main():
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ ОШИБКА: Секреты TG_TOKEN или TG_CHAT_ID не найдены в GitHub Actions!")
        sys.exit(1)

    print("🤖 Запуск одноразовой проверки для GitHub Actions...")
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    current_free_games = fetch_all_freebies(api)
    new_freebies = nm.get_new_freebies(current_free_games)
    
    if new_freebies:
        for game in new_freebies:
            send_to_telegram(game)
    else:
        print("🤷‍♂️ Новых халявных игр пока нет.")

if __name__ == '__main__':
    main()