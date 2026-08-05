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

# Заголовки для БЕСПЛАТНЫХ раздач
HEADERS_FREE = [
    "🔥 ЛУТАЕМ ХАЛЯВУ", 
    "🚨 СВЕЖИЙ ДРОП", 
    "⚡️ СРОЧНО НА АККАУНТ", 
    "🎁 ЗАВОЗ БЕСПЛАТНЫХ ИГР", 
    "💥 100% СКИДКА",
    "🎮 ОФИЦИАЛЬНАЯ РАЗДАЧА"
]

# Заголовки для СКИДОК
HEADERS_DISCOUNT = [
    "📉 ЖАРКАЯ СКИДКА",
    "🏷️ ОТЛИЧНОЕ ПРЕДЛОЖЕНИЕ",
    "💥 БОЛЬШАЯ СКИДКА",
    "💸 ХОРОШАЯ ЦЕНА"
]

PRICE_PREFIXES = ["💸 Прайс:", "💰 Цена вопроса:", "💳 Стоило:"]
DESC_PREFIXES = ["📖 О чём игра:", "👀 Краткая база:", "📜 Сюжет:", "💡 Спойлер:"]

BTN_GET_GAME = [
    "🏃‍♂️ Залутать игру", 
    "⚡️ Перейти к игре", 
    "🛒 Купить по скидке", 
    "🕹️ Перейти в магазин",
    "🔥 Посмотреть предложение"
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
    price_raw = str(game.get("price", "FREE")).strip()
    link = game.get("link", "")
    img_url = game.get("image", "")
    desc = game.get("description", "")
    
    is_free = price_raw.upper() == "FREE"
    hashtag_plat = platform.replace(" ", "").replace("-", "")
    
    if desc:
        desc = desc.replace("<br>", "").replace("\n", " ")
        if len(desc) > 160:
            desc = desc[:157] + "..."
            
    header = random.choice(HEADERS_FREE if is_free else HEADERS_DISCOUNT)
    price_pref = random.choice(PRICE_PREFIXES)
    desc_pref = random.choice(DESC_PREFIXES)
    btn_game_text = random.choice(BTN_GET_GAME)
    btn_promo_text = random.choice(BTN_PROMO)
            
    caption = f"{header}: <b>{title}</b>\n\n"
    caption += f"🌐 <b>Платформа:</b> {platform}\n"
    
    if is_free:
        if worth > 0:
            caption += f"{price_pref} <s>${worth:.2f}</s> ➡️ <b>0₽ (FREE)</b>\n"
        else:
            caption += f"{price_pref} <b>100% Бесплатно!</b>\n"
    else:
        # Форматирование для скидки
        caption += f"🏷️ <b>Цена:</b> {price_raw}\n"
        
    if desc:
        caption += f"\n{desc_pref} <i>{desc}</i>\n"
        
    tag_type = "#раздача #freegames" if is_free else "#скидки #deals"
    caption += f"\n{tag_type} #{hashtag_plat}"

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
        print(f"✅ Отправлено: {title} ({'FREE' if is_free else price_raw})")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def get_unseen_items(nm, games):
    """Универсальная фильтрация новых игр (бесплатных и скидок)"""
    new_items = []
    now = nm._now_ts()
    for g in games or []:
        gid = nm._game_id(g)
        if gid not in nm.seen:
            new_items.append(g)
            nm.seen[gid] = now
    if new_items:
        nm._save_seen()
    return new_items

def main():
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ ОШИБКА: Секреты не найдены!")
        sys.exit(1)

    print("🤖 Запуск проверки раздач и скидок...")
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    # 1. Получаем бесплатные игры
    free_games = []
    try: free_games.extend(api.fetch_cheapshark_free(12))
    except: pass
    try: free_games.extend(api.fetch_gamerpower_pc(15))
    except: pass
    try: free_games.extend(api.fetch_gamerpower_loot(15))
    except: pass
    
    free_games = [g for g in free_games if str(g.get("price", "")).strip().upper() == "FREE"]
    new_freebies = get_unseen_items(nm, free_games)

    # 2. Получаем скидки (например, со скидкой от 70% и до $15)
    discounts = []
    try:
        raw_discounts = api.fetch_cheapshark_discounts(limit=25, max_price=15.0, min_savings=70.0)
        discounts = get_unseen_items(nm, raw_discounts)
    except Exception as e:
        print(f"Ошибка получения скидок: {e}")

    # 3. Публикация
    total_posted = 0

    # Сначала всегда постим бесплатные игры
    if new_freebies:
        print(f"🎁 Найдено новых бесплатных игр: {len(new_freebies)}")
        for game in new_freebies:
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    # Затем постим не более 3 лучших скидок за запуск, чтобы не спамить в канал
    if discounts:
        max_discounts_per_run = 3
        to_post_discounts = discounts[:max_discounts_per_run]
        print(f"🏷️ Найдено новых скидок: {len(discounts)}. Постим {len(to_post_discounts)} шт.")
        for game in to_post_discounts:
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if total_posted == 0:
        print("🤷‍♂️ Новых раздач и скидок пока нет.")

if __name__ == '__main__':
    main()
    
