# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import requests
import json
import xml.etree.ElementTree as ET
from email.utils import formatdate
from api import GameAPI
from notifications import NotificationManager

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

RSS_FILE = "rss.xml"
FEED_CACHE = "dzen_feed.json"

# Заголовки для БЕСПЛАТНЫХ раздач (ПК)
HEADERS_FREE = [
    "🔥 ЛУТАЕМ ХАЛЯВУ", "🚨 СВЕЖИЙ ДРОП", "⚡️ СРОЧНО НА АККАУНТ", 
    "🎁 ЗАВОЗ БЕСПЛАТНЫХ ИГР", "🎉 100% СКИДКА (БЕСПЛАТНО)",
    "🤑 ЗАБИРАЙ, ПОКА ДАЮТ", "🕹️ ПОПОЛНЕНИЕ БИБЛИОТЕКИ",
    "🚀 ХАЛЯВНАЯ ИГРА", "💸 НОЛЬ РУБЛЕЙ, НОЛЬ КОПЕЕК",
    "📦 ЩЕДРЫЙ ПОДАРОК ГЕЙМЕРУ"
]

HEADERS_DISCOUNT = ["📉 ЖАРКАЯ СКИДКА", "🏷️ ОТЛИЧНОЕ ПРЕДЛОЖЕНИЕ", "💥 БОЛЬШАЯ СКИДКА", "💰 ТОТАЛЬНЫЙ ЦЕНОПАД"]
HEADERS_ROBLOX = ["🟥 ROBLOX ХАЛЯВА", "🎁 СВЕЖИЙ ЛУТ И КОДЫ ROBLOX", "⚡️ ПРОМОКОДЫ И ВЕЩИ ROBLOX"]
HEADERS_GACHA = ["💎 НОВЫЕ ПРОМОКОДЫ", "✨ ХАЛЯВА HOYOVERSE", "🌸 ПРИМОГЕМЫ И НЕФРИТ"]
HEADERS_MOBILE = ["📱 ЛУТ ДЛЯ МОБИЛОК", "🎯 МОБИЛЬНАЯ ХАЛЯВА", "🔥 ПРОМОКОДЫ НА ТЕЛЕФОН"]
HEADERS_STEAM_NEW = ["🎮 СВЕЖИЙ РЕЛИЗ В STEAM", "🚀 НОВИНКА В STEAM", "🔥 ТОЛЬКО ЧТО ВЫШЛО В STEAM"]

PRICE_PREFIXES = ["💸 Прайс:", "💰 Цена вопроса:", "💳 Стоило:"]
DESC_PREFIXES = ["📖 О чём игра:", "👀 Краткая база:", "📜 Сюжет:", "💡 Спойлер:"]

BTN_GET_GAME = ["🏃‍♂️ Залутать", "⚡️ Перейти", "🔥 Посмотреть", "🎯 Забрать себе", "🛒 В магазин", "🎁 Активировать"]
BTN_PROMO = ["🤖 Наш трекер халявы на ПК", "💻 Качай GameGiveawaysPro", "🚀 Ищи игры в нашей проге", "🕹️ Скачать авто-чекер"]

# --- ВАРИАТИВНОСТЬ ДЛЯ ДЗЕНА (RSS) ---
RSS_TITLE_TEMPLATES = [
    "🔥 Бесплатная игра: {title} раздается прямо сейчас!",
    "🎁 Забирай 100% скидку на {title}",
    "⚡ Временно бесплатно: {title} для ПК",
    "🎮 Очередная раздача халявы: {title}",
    "🚀 Успей забрать {title} бесплатно на свой аккаунт",
    "📦 Щедрый дроп: раздают игру {title}"
]

RSS_DESC_TEMPLATES = [
    "Отличное пополнение для твоей библиотеки.",
    "Забирай скорее, пока разработчики не передумали!",
    "Шикарная возможность сэкономить.",
    "Не упусти шанс забрать этот проект навсегда.",
    "Халява не вечна, так что лучше поторопиться.",
    "Идеально, чтобы поиграть на выходных."
]


def update_rss_feed(game):
    """Создает и обновляет автономный RSS-файл для Дзена с вариативным текстом"""
    title = game.get("title", "Game")
    link = game.get("link", "")
    desc = game.get("description", "")
    platform = game.get("platform", "PC")
    img_url = game.get("image", "")
    game_id = game.get("id", str(time.time()))
    
    # Случайная генерация уникального заголовка и приписки
    rss_title = random.choice(RSS_TITLE_TEMPLATES).format(title=title)
    random_phrase = random.choice(RSS_DESC_TEMPLATES)
    
    # Формируем HTML для Дзена
    html_desc = f"""
    <img src="{img_url}"><br><br>
    <b>Платформа:</b> {platform}<br><br>
    {desc}<br><br>
    <i>{random_phrase}</i><br><br>
    ⚡ <b>НЕТ ПРОСТО РАЗДАЕМ КТО УСПЕЛ ТОТ И СЬЕЛ)</b><br><br>
    <a href="{link}">👉 Забрать игру на свой аккаунт</a><br><br>
    <hr>
    <i>Больше моментальных раздач и наша бесплатная программа для ПК (GameGiveawaysPro) ждут вас в <a href="https://t.me/ggpro_free_games">нашем Telegram-канале</a>!</i>
    """
    
    # Загружаем историю прошлых раздач
    try:
        if os.path.exists(FEED_CACHE):
            with open(FEED_CACHE, 'r', encoding='utf-8') as f:
                feed_items = json.load(f)
        else:
            feed_items = []
    except:
        feed_items = []

    new_item = {
        "title": rss_title,
        "link": link,
        "description": html_desc,
        "pubDate": formatdate(timeval=None, localtime=False, usegmt=True),
        "guid": game_id
    }
    
    # Оставляем только последние 20 штук, чтобы лента не была бесконечной
    if not any(item["guid"] == new_item["guid"] for item in feed_items):
        feed_items.insert(0, new_item)
    feed_items = feed_items[:20]
    
    # Сохраняем кэш RSS
    with open(FEED_CACHE, 'w', encoding='utf-8') as f:
        json.dump(feed_items, f, ensure_ascii=False, indent=2)
        
    # Генерируем сам XML файл
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Халява Steam и Epic Games"
    ET.SubElement(channel, "link").text = "https://t.me/ggpro_free_games"
    ET.SubElement(channel, "description").text = "Отборные 100% скидки и бесплатные раздачи топовых игр."
    
    for item in feed_items:
        item_el = ET.SubElement(channel, "item")
        ET.SubElement(item_el, "title").text = item["title"]
        ET.SubElement(item_el, "link").text = item["link"]
        ET.SubElement(item_el, "description").text = item["description"]
        ET.SubElement(item_el, "pubDate").text = item["pubDate"]
        ET.SubElement(item_el, "guid").text = item["guid"]
        
    tree = ET.ElementTree(rss)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"📝 RSS лента обновлена: {title}")


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
            # Отбираем жирные раздачи в RSS
            plat = game.get("platformkey", "").lower()
            if "epic" in plat or "steam" in plat:
                update_rss_feed(game)
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
        for game in discounts[:3]:  
            send_to_telegram(game)
            time.sleep(2)
            total_posted += 1

    if steam_new_items:
        for game in steam_new_items[:2]:  
            send_to_telegram(game)
            update_rss_feed(game) # Новинки у нас бесплатные, тоже пишем в RSS
            time.sleep(2)
            total_posted += 1

    if total_posted == 0:
        print("🤷‍♂️ Новых раздач, скидок, лута и релизов пока нет.")

if __name__ == '__main__':
    main()
    
