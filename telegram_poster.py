# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import requests
from api import GameAPI
from notifications import NotificationManager

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

HEADERS = [
    "🔥 ЛУТАЕМ ХАЛЯВУ", 
    "🚨 СВЕЖИЙ ДРОП", 
    "⚡️ СРОЧНО НА АККАУНТ", 
    "🎁 ЗАВОЗ БЕСПЛАТНЫХ ИГР", 
    "💥 100% СКИДКА",
    "🎮 ОФИЦИАЛЬНАЯ РАЗДАЧА"
]

PRICE_PREFIXES = ["💸 Прайс:", "💰 Цена вопроса:", "💳 Стоило:"]
DESC_PREFIXES = ["📖 О чём игра:", "👀 Краткая база:", "📜 Сюжет:", "💡 Спойлер:"]

BTN_GET_GAME = [
    "🏃‍♂️ Залутать игру", 
    "⚡️ Забрать на акк", 
    "🎁 Получить бесплатно", 
    "🕹️ К раздаче",
    "🔥 Схватить пока дают"
]

BTN_PROMO = [
    "🤖 Наш трекер халявы на ПК", 
    "💻 Качай GameGiveawaysPro", 
    "🚀 Больше игр в нашей проге",
    "⚡️ Установить авто-чекер (GitHub)"
]

def send_to_telegram(game):
    title = game.get("title", "Неизвестная игра")
    platform = game.get("platform", "PC")
    worth = float(game.get("worth", 0) or 0)
    link = game.get("link", "")
    img_url = game.get("image", "")
    desc = game.get("description", "")
    
    hashtag_plat = platform.replace(" ", "").replace("-", "")
    
    if desc:
        desc = desc.replace("<br>", "").replace("\n", " ")
        if len(desc) > 160:
            desc = desc[:157] + "..."
            
    header = random.choice(HEADERS)
    price_pref = random.choice(PRICE_PREFIXES)
    desc_pref = random.choice(DESC_PREFIXES)
    btn_game_text = random.choice(BTN_GET_GAME)
    btn_promo_text = random.choice(BTN_PROMO)
            
    caption = f"{header}: <b>{title}</b>\n\n"
    caption += f"🌐 <b>Платформа:</b> {platform}\n"
    
    if worth > 0:
        caption += f"{price_pref} <s>${worth:.2f}</s> ➡️ <b>0₽ (FREE)</b>\n"
    else:
        caption += f"{price_pref} <b>100% Бесплатно!</b>\n"
        
    if desc:
        caption += f"\n{desc_pref} <i>{desc}</i>\n"
        
    caption += f"\n#раздача #{hashtag_plat} #freegames"

    reply_markup = {
        "inline_keyboard": [
            [{"text": btn_game_text, "url": link}],
            [{"text": btn_promo_text, "url": "https://github.com/TaJIanT/GameGiveawaysPro/releases/latest"}]
        ]
    }

    try:
        if img_url:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            payload = {
                "chat_id": TG_CHAT_ID, 
                "photo": img_url, 
                "caption": caption, 
                "parse_mode": "HTML",
                "reply_markup": reply_markup
            }
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            payload = {
                "chat_id": TG_CHAT_ID, 
                "text": caption, 
                "parse_mode": "HTML", 
                "disable_web_page_preview": False,
                "reply_markup": reply_markup
            }
            
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
        print("❌ ОШИБКА: Секреты не найдены!")
        sys.exit(1)

    print("🤖 Запуск проверки раздач...")
    api =GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    current_free_games = fetch_all_freebies(api)
    new_freebies = nm.get_new_freebies(current_free_games)
    
    if new_freebies:
        for game in new_freebies:
            send_to_telegram(game)
            time.sleep(2)
    else:
        print("🤷‍♂️ Новых халявных игр пока нет.")

if __name__ == '__main__':
    main()
    
