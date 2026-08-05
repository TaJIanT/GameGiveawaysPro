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

# Заголовки специально для ROBLOX
HEADERS_ROBLOX = [
    "🟥 ROBLOX ХАЛЯВА",
    "🎁 СВЕЖИЙ ЛУТ И КОДЫ ROBLOX",
    "⚡️ ПРОМОКОДЫ И ВЕЩИ ROBLOX",
    "🎮 БЕСПЛАТНО ДЛЯ ROBLOX"
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
    platform_key = game.get("platformkey", "").lower()
    worth = float(game.get("worth", 0) or 0)
    price_raw = str(game.get("price", "FREE")).strip()
    link = game.get("link", "")
    img_url = game.get("image", "")
    desc = game.get("description", "")
    
    is_free = price_raw.upper() == "FREE"
    is_roblox = platform_key == "roblox" or "roblox" in platform.lower()
    
    hashtag_plat = platform.replace(" ", "").replace("-", "").replace("®", "").replace("™", "")
    
    if desc:
        desc = desc.replace("<br>", "").replace("\n", " ")
        if len(desc) > 160:
            desc = desc[:157] + "..."
            
    if is_roblox:
        header = random.choice(HEADERS_ROBLOX)
    elif is_free:
        header = random.choice(HEADERS_FREE)
    else:
        header = random.choice(HEADERS_DISCOUNT)

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
        caption += f"🏷️ <b>Цена:</b> {price_raw}\n"
        
    if desc:
        caption += f"\n{desc_pref} <i>{desc}</i>\n"
        
    if is_roblox:
        tag_type = "#roblox #роблокс #халява"
    elif is_free:
        tag_type = "#раздача #freegames"
    else:
        tag_type = "#скидки #deals"

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

    print("🤖 Запуск проверки раздач, скидок и Roblox...")
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    # --- 1. БЕСПЛАТНЫЕ ИГРЫ ДЛЯ ПК ---
    raw_free = []
    try: raw_free.extend(api.fetch_cheapshark_free(15))
    except: pass
    try: raw_free.extend(api.fetch_gamerpower_pc(15))
    except: pass
    try: raw_free.extend(api.fetch_gamerpower_loot(15))
    except: pass
    
    free_games = [g for g in raw_free if str(g.get("price", "")).strip().upper() == "FREE"]
    print(f"📡 API вернуло бесплатных ПК-игр: {len(free_games)}")
    new_freebies = get_unseen_items(nm, free_games)
    print(f"🧠 После кэша осталось новых (бесплатных): {len(new_freebies)}")

    # --- 2. ROBLOX ХАЛЯВА ---
    roblox_items = []
    try:
        raw_roblox = api.fetch_roblox_loot(limit=10)
        print(f"📡 API вернуло раздач и кодов Roblox: {len(raw_roblox)}")
        roblox_items = get_unseen_items(nm, raw_roblox)
        print(f"🧠 После кэша осталось новых (Roblox): {len(roblox_items)}")
    except Exception as e:
        print(f"❌ Ошибка получения Roblox: {e}")

    # --- 3. СКИДКИ ---
    discounts = []
    try:
        raw_discounts = api.fetch_cheapshark_discounts(limit=25, max_price=50.0, min_savings=10.0)
        print(f"📡 API вернуло скидок (CheapShark): {len(raw_discounts)}")
        discounts.extend(get_unseen_items(nm, raw_discounts))
    except Exception as e:
        print(f"❌ Ошибка получения скидок CheapShark: {e}")

    try:
        vk_discounts = api.fetch_vkplay_discounts(limit=10, min_savings=10.0)
        print(f"📡 API вернуло скидок (VK Play): {len(vk_discounts)}")
        discounts.extend(get_unseen_items(nm, vk_discounts))
    except Exception as e:
        print(f"❌ Ошибка получения скидок VK Play: {e}")
        
    print(f"🧠 После кэша осталось новых (скидок всего): {len(discounts)}")

    # --- 4. ПУБЛИКАЦИЯ ---
    total_posted = 0

    if new_freebies:
        for game in new_freebies:
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if roblox_items:
        for game in roblox_items:
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if discounts:
        max_discounts_per_run = 3
        random.shuffle(discounts)
        to_post_discounts = discounts[:max_discounts_per_run]
        
        for game in to_post_discounts:
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if total_posted == 0:
        print("🤷‍♂️ Новых раздач, скидок и лута Roblox пока нет.")

if __name__ == '__main__':
    main()
    
