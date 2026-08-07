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

# Заголовки для БЕСПЛАТНЫХ раздач (ПК)
HEADERS_FREE = [
    "🔥 ЛУТАЕМ ХАЛЯВУ", 
    "🚨 СВЕЖИЙ ДРОП", 
    "⚡️ СРОЧНО НА АККАУНТ", 
    "🎁 ЗАВОЗ БЕСПЛАТНЫХ ИГР", 
    "🎉 100% СКИДКА (БЕСПЛАТНО)",
    "🤑 ЗАБИРАЙ, ПОКА ДАЮТ",
    "🕹️ ПОПОЛНЕНИЕ БИБЛИОТЕКИ",
    "🚀 ХАЛЯВНАЯ ИГРА",
    "💸 НОЛЬ РУБЛЕЙ, НОЛЬ КОПЕЕК",
    "📦 ЩЕДРЫЙ ПОДАРОК ГЕЙМЕРУ"
]

# Заголовки для СКИДОК
HEADERS_DISCOUNT = [
    "📉 ЖАРКАЯ СКИДКА",
    "🏷️ ОТЛИЧНОЕ ПРЕДЛОЖЕНИЕ",
    "💥 БОЛЬШАЯ СКИДКА",
    "💰 ТОТАЛЬНЫЙ ЦЕНОПАД",
    "✂️ РУБИМ ЦЕНЫ",
    "🔥 ВЫГОДНАЯ СДЕЛКА",
    "🛒 ВРЕМЯ ЗАКУПАТЬСЯ",
    "📉 СЕРЬЕЗНЫЙ ОБВАЛ ЦЕН",
    "🤑 ЭКОНОМИМ КЭШ НА ИГРАХ"
]

# Заголовки специально для ROBLOX
HEADERS_ROBLOX = [
    "🟥 ROBLOX ХАЛЯВА",
    "🎁 СВЕЖИЙ ЛУТ И КОДЫ ROBLOX",
    "⚡️ ПРОМОКОДЫ И ВЕЩИ ROBLOX",
    "🧊 РОБАКСЫ И ПРЕДМЕТЫ",
    "🎮 НОВЫЙ ДРОП В ROBLOX",
    "🎒 БЕСПЛАТНЫЙ ИНВЕНТАРЬ ROBLOX",
    "🔥 СЕКРЕТНЫЕ КОДЫ ДЛЯ ПЛЕЙСОВ",
    "👕 ШМОТ И ПЕТЫ В ROBLOX"
]

# Заголовки для ГАЧА-ИГР (Genshin, Honkai, ZZZ)
HEADERS_GACHA = [
    "💎 НОВЫЕ ПРОМОКОДЫ",
    "✨ ХАЛЯВА HOYOVERSE",
    "🌸 ПРИМОГЕМЫ И НЕФРИТ",
    "🌠 СРОЧНЫЙ ВВОД КОДОВ",
    "🎟️ ХАЛЯВА ОТ РАЗРАБОВ",
    "💫 ЛУТАЕМ КАМНИ ИСТОКА",
    "🎁 ЗАПАСАЕМСЯ КРУТКАМИ",
    "🚀 НОВЫЕ КОДЫ ДЛЯ ГАЧИ",
    "🔮 ПРОМОКОДЫ СО СТРИМА"
]

# Заголовки для МОБИЛЬНЫХ ИГР
HEADERS_MOBILE = [
    "📱 ЛУТ ДЛЯ МОБИЛОК",
    "🎯 МОБИЛЬНАЯ ХАЛЯВА",
    "🔥 ПРОМОКОДЫ НА ТЕЛЕФОН",
    "📲 НОВЫЙ ДРОП ДЛЯ МОБИЛОК",
    "🎒 ХАЛЯВА В КАРМАНЕ",
    "🎮 БОНУСЫ НА СМАРТФОН",
    "💎 СКИНЫ И ВАЛЮТА",
    "🕹️ МОБИЛЬНЫЙ ГЕЙМИНГ"
]

# Заголовки для НОВИНОК STEAM
HEADERS_STEAM_NEW = [
    "🎮 СВЕЖИЙ РЕЛИЗ В STEAM",
    "🚀 НОВИНКА В STEAM",
    "🔥 ТОЛЬКО ЧТО ВЫШЛО В STEAM",
    "🕹️ НОВАЯ ИГРА В STEAM",
    "✨ РЕЛИЗ ДНЯ В STEAM",
    "📦 СОСТОЯЛСЯ РЕЛИЗ В STEAM"
]

PRICE_PREFIXES = ["💸 Прайс:", "💰 Цена вопроса:", "💳 Стоило:"]
DESC_PREFIXES = ["📖 О чём игра:", "👀 Краткая база:", "📜 Сюжет:", "💡 Спойлер:"]

BTN_GET_GAME = [
    "🏃‍♂️ Залутать", 
    "⚡️ Перейти", 
    "🔥 Посмотреть",
    "🎯 Забрать себе",
    "🛒 В магазин",
    "🎁 Активировать"
]

BTN_PROMO = [
    "🤖 Наш трекер халявы на ПК", 
    "💻 Качай GameGiveawaysPro",
    "🚀 Ищи игры в нашей проге",
    "🕹️ Скачать авто-чекер"
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
    
    hashtag_plat = platform.replace(" ", "").replace("-", "").replace("®", "").replace("™", "").replace("(", "").replace(")", "")
    
    if desc:
        desc = desc.replace("<br>", "").replace("\n", " ")
        if len(desc) > 160:
            desc = desc[:157] + "..."
            
    # Выбор правильного заголовка и тегов
    tag_type = ""
    if platform_key == "roblox" or "roblox" in platform.lower():
        header = random.choice(HEADERS_ROBLOX)
        tag_type = "#roblox #роблокс"
    elif platform_key == "steam_new":
        header = random.choice(HEADERS_STEAM_NEW)
        tag_type = "#steam #новинки #релиз"
    elif platform_key == "gacha":
        header = random.choice(HEADERS_GACHA)
        tag_type = "#genshin #honkai #промокоды"
    elif platform_key == "mobile":
        header = random.choice(HEADERS_MOBILE)
        tag_type = "#mobile #мобильныеигры"
    elif is_free:
        header = random.choice(HEADERS_FREE)
        tag_type = "#раздача #freegames"
    else:
        header = random.choice(HEADERS_DISCOUNT)
        tag_type = "#скидки #deals"

    price_pref = random.choice(PRICE_PREFIXES)
    desc_pref = random.choice(DESC_PREFIXES)
            
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
        
    caption += f"\n{tag_type} #{hashtag_plat}"

    reply_markup = {
        "inline_keyboard": [
            [{"text": random.choice(BTN_GET_GAME), "url": link}],
            [{"text": random.choice(BTN_PROMO), "url": "https://github.com/TaJIanT/GameGiveawaysPro/releases/latest"}]
        ]
    }

    try:
        if img_url:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            payload = {
                "chat_id": TG_CHAT_ID, "photo": img_url, 
                "caption": caption, "parse_mode": "HTML", "reply_markup": reply_markup
            }
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            payload = {
                "chat_id": TG_CHAT_ID, "text": caption, 
                "parse_mode": "HTML", "reply_markup": reply_markup
            }
            
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Отправлено: {title}")
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

    print("🤖 Запуск проверки раздач, скидок, мобилок, Roblox и новинок Steam...")
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
    
    free_games = [g for g in raw_free if str(g.get("price", "")).strip().upper() == "FREE" and "gacha" not in g.get("platformkey", "") and "mobile" not in g.get("platformkey", "")]
    print(f"📡 API вернуло бесплатных ПК-игр: {len(free_games)}")
    new_freebies = get_unseen_items(nm, free_games)

    # --- 2. ROBLOX ХАЛЯВА ---
    roblox_items = []
    try:
        raw_roblox = api.fetch_roblox_loot(limit=10)
        print(f"📡 API вернуло раздач Roblox: {len(raw_roblox)}")
        roblox_items = get_unseen_items(nm, raw_roblox)
    except: pass

    # --- 3. ГАЧА И МОБИЛЬНЫЕ ПРОМОКОДЫ ---
    mobile_items = []
    try:
        raw_mobile = api.fetch_gacha_mobile_loot(limit=10)
        print(f"📡 API вернуло Гача/Мобильных кодов: {len(raw_mobile)}")
        mobile_items = get_unseen_items(nm, raw_mobile)
    except: pass

    # --- 4. СКИДКИ ---
    discounts = []
    try:
        discounts.extend(get_unseen_items(nm, api.fetch_cheapshark_discounts(limit=25, max_price=50.0, min_savings=10.0)))
        discounts.extend(get_unseen_items(nm, api.fetch_vkplay_discounts(limit=10, min_savings=10.0)))
        print(f"🧠 В кэше появилось новых скидок: {len(discounts)}")
    except: pass

    # --- 5. НОВИНКИ STEAM ---
    steam_new_items = []
    try:
        raw_steam_new = api.fetch_steam_new_releases(limit=10)
        print(f"📡 API вернуло новинок Steam: {len(raw_steam_new)}")
        steam_new_items = get_unseen_items(nm, raw_steam_new)
    except Exception as e:
        print(f"❌ Ошибка сбора новинок Steam: {e}")

    # --- 6. ПУБЛИКАЦИЯ ---
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

    if mobile_items:
        for game in mobile_items:
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if discounts:
        random.shuffle(discounts)
        for game in discounts[:3]:  # Не больше 3 постов скидок за раз
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if steam_new_items:
        for game in steam_new_items[:2]:  # Не больше 2 новинок за раз
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if total_posted == 0:
        print("🤷‍♂️ Новых раздач, скидок, лута и релизов пока нет.")

if __name__ == '__main__':
    main()
    
