# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import requests
from api import GameAPI
from notifications import NotificationManager
from vk_uploader import send_vk_wall_post

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# ==========================================
# ВАЖНЫЕ ССЫЛКИ ПРОЕКТА
# ==========================================
APP_LINK = "https://github.com/TaJIanT/GameGiveawaysPro/releases/latest"
VK_GROUP_URL = "https://vk.com/club152331651"
TG_CHANNEL_URL = "https://t.me/ggpro_free_games"

# ==========================================
# ФИРМЕННЫЕ БАННЕРЫ С GITHUB
# ==========================================
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

# ==========================================
# СЛОВАРИ ДЛЯ ТЕЛЕГРАМА 
# ==========================================
HEADERS_FREE = [
    "🔥 <b>ЭПИЧНАЯ ХАЛЯВА</b>", "🚨 <b>АЛЕРТ: СВЕЖИЙ ДРОП</b>", "⚡️ <b>СРОЧНО НА АККАУНТ</b>", 
    "🎁 <b>ЖИРНАЯ РАЗДАЧА</b>", "🎉 <b>100% СКИДКА</b>",
    "🤑 <b>ЛУТАЕМ ПОКА ДАЮТ</b>", "🕹️ <b>ПОПОЛНЕНИЕ БИБЛИОТЕКИ</b>"
]
HEADERS_DISCOUNT = ["📉 <b>ЖАРКАЯ СКИДКА</b>", "🏷️ <b>ОТЛИЧНОЕ ПРЕДЛОЖЕНИЕ</b>", "💥 <b>ЦЕНОПАД</b>"]
HEADERS_ROBLOX = ["🟥 <b>ROBLOX ХАЛЯВА</b>", "🎁 <b>СВЕЖИЙ ЛУТ ROBLOX</b>"]
HEADERS_GACHA = ["💎 <b>НОВЫЕ ПРОМОКОДЫ</b>", "✨ <b>ХАЛЯВА HOYOVERSE</b>"]
HEADERS_MOBILE = ["📱 <b>ЛУТ ДЛЯ МОБИЛОК</b>", "🎯 <b>МОБИЛЬНАЯ ХАЛЯВА</b>"]
HEADERS_STEAM_NEW = ["🎮 <b>СВЕЖИЙ РЕЛИЗ В STEAM</b>", "🚀 <b>НОВИНКА В МАГАЗИНЕ</b>"]

BTN_GET_GAME = ["🎮 Забрать игру", "⚡️ Залутать сейчас", "🔥 Добавить в библиотеку", "🎯 Перейти к раздаче"]
BTN_GET_APP = ["💻 Наш авто-трекер на ПК", "🚀 Скачать GameGiveawaysPro", "🔔 Не пропускать раздачи (ПК)"]

# ==========================================
# СЛОВАРИ ДЛЯ ВКОНТАКТЕ
# ==========================================
VK_HEADERS_FREE = [
    "🔥 Очередная годнота подъехала!", "🎁 Разработчики расщедрились, лутаем:",
    "⚡ Забираем на аккаунт, пока полностью бесплатно!", "🎉 Раздача дня, успевайте забрать:"
]
VK_HEADERS_DISCOUNT = ["📉 Отличная скидка нарисовалась:", "🏷️ Забираем по вкусной цене:"]
VK_LINK_TEXTS = ["👉 ССЫЛКА НА ИГРУ", "🎮 ЗАБРАТЬ В СВОЮ БИБЛИОТЕКУ", "⚡ ПЕРЕЙТИ К РАЗДАЧЕ"]

def process_and_send_game(game):
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
        if len(desc) > 180:
            desc = desc[:177] + "..."
            
    # Определяем заголовки и теги
    if platform_key == "roblox" or "roblox" in platform.lower():
        header, vk_header, tag_type = random.choice(HEADERS_ROBLOX), random.choice(HEADERS_ROBLOX), "#roblox #роблокс"
    elif platform_key == "steam_new":
        header, vk_header, tag_type = random.choice(HEADERS_STEAM_NEW), random.choice(HEADERS_STEAM_NEW), "#steam #новинки #релиз"
    elif platform_key == "gacha":
        header, vk_header, tag_type = random.choice(HEADERS_GACHA), random.choice(HEADERS_GACHA), "#genshin #honkai #промокоды"
    elif platform_key == "mobile":
        header, vk_header, tag_type = random.choice(HEADERS_MOBILE), random.choice(HEADERS_MOBILE), "#mobile #мобильныеигры"
    elif is_free:
        header, vk_header, tag_type = random.choice(HEADERS_FREE), random.choice(VK_HEADERS_FREE), "#раздача #freegames"
    else:
        header, vk_header, tag_type = random.choice(HEADERS_DISCOUNT), random.choice(VK_HEADERS_DISCOUNT), "#скидки #deals"

    # Логика выбора правильного баннера-заглушки
    fallback_category = "default"
    if "roblox" in platform_key or "roblox" in platform.lower():
        fallback_category = "roblox"
    elif "steam_new" in platform_key or ("steam" in platform.lower() and is_free):
        fallback_category = "steam"
    elif "epic" in platform_key or "epic" in platform.lower():
        fallback_category = "epic"
    elif "gog" in platform_key or "gog" in platform.lower():
        fallback_category = "gog"
    elif "gacha" in platform_key:
        fallback_category = "gacha" if "code" in title.lower() else "gacha_sale"
    elif "vkplay" in platform_key or "vk" in platform.lower():
        fallback_category = "vkplay"
    elif "mobile" in platform_key:
        fallback_category = "mobile"
    elif "key" in title.lower():
        fallback_category = "steam_keys"

    fallback_url = FALLBACK_IMAGES.get(fallback_category, FALLBACK_IMAGES["default"])

    # ==========================================
    # 1. ФОРМИРУЕМ ПОСТ ДЛЯ TELEGRAM
    # ==========================================
    main_caption = f"{header}\n\n"
    main_caption += f"📌 <b>Название:</b> {title}\n"
    main_caption += f"🌐 <b>Магазин:</b> {platform}\n\n"
    
    if is_free:
        if worth > 0:
            main_caption += f"💳 Без раздачи: <s>${worth:.2f}</s>\n"
        main_caption += f"🎁 Сейчас: <b>0₽ [БЕСПЛАТНО]</b>\n\n"
    else:
        main_caption += f"🏷️ <b>Цена по скидке:</b> {price_raw}\n\n"
        
    if desc:
        main_caption += f"📖 <b>Кратко об игре:</b>\n<i>{desc}</i>\n\n"
        
    main_caption += f"{tag_type} #{hashtag_plat}"

    main_markup = {
        "inline_keyboard": [
            [{"text": random.choice(BTN_GET_GAME), "url": link}],
            [{"text": "🔵 Мы ВКонтакте", "url": VK_GROUP_URL}],
            [{"text": random.choice(BTN_GET_APP), "url": APP_LINK}]
        ]
    }

    # ==========================================
    # 2. ФОРМИРУЕМ ПОСТ ДЛЯ ВКОНТАКТЕ
    # ==========================================
    vk_caption = f"{vk_header}\n\n"
    vk_caption += f"📌 Игра: {title}\n"
    vk_caption += f"🌐 Площадка: {platform}\n"
    
    if is_free:
        if worth > 0:
            vk_caption += f"💳 Обычная цена: ${worth:.2f} ➡️ 0₽\n"
        vk_caption += f"🎁 Статус: 100% БЕСПЛАТНО\n\n"
    else:
        vk_caption += f"🏷️ Цена: {price_raw}\n\n"
        
    if desc:
        vk_caption += f"📖 Об игре:\n{desc}\n\n"
        
    vk_caption += f"───────────────\n"
    vk_caption += f"🔻 {random.choice(VK_LINK_TEXTS)} 🔻\n"
    vk_caption += f"{link}\n"
    vk_caption += f"───────────────\n\n"
    
    vk_caption += f"✈️ Больше эксклюзивной халявы в нашем Telegram-канале:\n"
    vk_caption += f"👉 {TG_CHANNEL_URL}\n\n"
    vk_caption += f"⚡ Хочешь узнавать о раздачах прямо на рабочем столе ПК?\n"
    vk_caption += f"💻 Скачивай нашу программу: {APP_LINK}"

    # ==========================================
    # ОТПРАВКА
    # ==========================================
    def send_request(target_chat_id, text_caption, markup=None):
        if not target_chat_id: return
        try:
            payload = {"chat_id": target_chat_id, "caption": text_caption, "parse_mode": "HTML"}
            if markup: payload["reply_markup"] = markup
            if img_url:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                payload["photo"] = img_url
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                payload["text"] = text_caption
                del payload["caption"]
            requests.post(url, json=payload, timeout=10).raise_for_status()
        except Exception as e:
            print(f"❌ Ошибка отправки ТГ: {e}")

    # Отправляем в ТГ
    send_request(TG_CHAT_ID, main_caption, main_markup)
    print(f"✅ Отправлено в Telegram: {title}")

    # Отправляем в ВК (передаем и оригинал картинки, и ссылку на твой баннер)
    send_vk_wall_post(vk_caption, img_url, fallback_url)

def get_unseen_items(nm, games):
    new_items = []
    now = nm._now_ts()
    for g in games or []:
        gid = nm._game_id(g)
        if gid not in nm.seen:
            new_items.append(g)
            nm.seen[gid] = now
    if new_items: nm._save_seen()
    return new_items

def main():
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ ОШИБКА: Секреты не найдены!")
        sys.exit(1)

    print("🤖 Запуск парсера GameGiveawaysPro...")
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    raw_free = []
    for func in [api.fetch_cheapshark_free, api.fetch_gamerpower_pc, api.fetch_gamerpower_loot]:
        try: raw_free.extend(func(15))
        except: pass
    
    free_games = [g for g in raw_free if str(g.get("price", "")).strip().upper() == "FREE" and "gacha" not in g.get("platformkey", "") and "mobile" not in g.get("platformkey", "")]
    new_freebies = get_unseen_items(nm, free_games)

    roblox_items = []
    try: roblox_items = get_unseen_items(nm, api.fetch_roblox_loot(limit=10))
    except: pass
# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import requests
from api import GameAPI
from notifications import NotificationManager
from vk_uploader import send_vk_wall_post

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# ==========================================
# ВАЖНЫЕ ССЫЛКИ ПРОЕКТА
# ==========================================
APP_LINK = "https://github.com/TaJIanT/GameGiveawaysPro/releases/latest"
VK_GROUP_URL = "https://vk.com/club152331651"
TG_CHANNEL_URL = "https://t.me/ggpro_free_games"

# ==========================================
# ФИРМЕННЫЕ БАННЕРЫ С GITHUB
# ==========================================
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

# ==========================================
# СЛОВАРИ ДЛЯ ТЕЛЕГРАМА 
# ==========================================
HEADERS_FREE = [
    "🔥 <b>ЭПИЧНАЯ ХАЛЯВА</b>", "🚨 <b>АЛЕРТ: СВЕЖИЙ ДРОП</b>", "⚡️ <b>СРОЧНО НА АККАУНТ</b>", 
    "🎁 <b>ЖИРНАЯ РАЗДАЧА</b>", "🎉 <b>100% СКИДКА</b>",
    "🤑 <b>ЛУТАЕМ ПОКА ДАЮТ</b>", "🕹️ <b>ПОПОЛНЕНИЕ БИБЛИОТЕКИ</b>"
]
HEADERS_DISCOUNT = ["📉 <b>ЖАРКАЯ СКИДКА</b>", "🏷️ <b>ОТЛИЧНОЕ ПРЕДЛОЖЕНИЕ</b>", "💥 <b>ЦЕНОПАД</b>"]
HEADERS_ROBLOX = ["🟥 <b>ROBLOX ХАЛЯВА</b>", "🎁 <b>СВЕЖИЙ ЛУТ ROBLOX</b>"]
HEADERS_GACHA = ["💎 <b>НОВЫЕ ПРОМОКОДЫ</b>", "✨ <b>ХАЛЯВА HOYOVERSE</b>"]
HEADERS_MOBILE = ["📱 <b>ЛУТ ДЛЯ МОБИЛОК</b>", "🎯 <b>МОБИЛЬНАЯ ХАЛЯВА</b>"]
HEADERS_STEAM_NEW = ["🎮 <b>СВЕЖИЙ РЕЛИЗ В STEAM</b>", "🚀 <b>НОВИНКА В МАГАЗИНЕ</b>"]

BTN_GET_GAME = ["🎮 Забрать игру", "⚡️ Залутать сейчас", "🔥 Добавить в библиотеку", "🎯 Перейти к раздаче"]
BTN_GET_APP = ["💻 Наш авто-трекер на ПК", "🚀 Скачать GameGiveawaysPro", "🔔 Не пропускать раздачи (ПК)"]

# ==========================================
# СЛОВАРИ ДЛЯ ВКОНТАКТЕ
# ==========================================
VK_HEADERS_FREE = [
    "🔥 Очередная годнота подъехала!", "🎁 Разработчики расщедрились, лутаем:",
    "⚡ Забираем на аккаунт, пока полностью бесплатно!", "🎉 Раздача дня, успевайте забрать:"
]
VK_HEADERS_DISCOUNT = ["📉 Отличная скидка нарисовалась:", "🏷️ Забираем по вкусной цене:"]
VK_LINK_TEXTS = ["👉 ССЫЛКА НА ИГРУ", "🎮 ЗАБРАТЬ В СВОЮ БИБЛИОТЕКУ", "⚡ ПЕРЕЙТИ К РАЗДАЧЕ"]

def process_and_send_game(game):
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
        if len(desc) > 180:
            desc = desc[:177] + "..."
            
    # Определяем заголовки и теги
    if platform_key == "roblox" or "roblox" in platform.lower():
        header, vk_header, tag_type = random.choice(HEADERS_ROBLOX), random.choice(HEADERS_ROBLOX), "#roblox #роблокс"
    elif platform_key == "steam_new":
        header, vk_header, tag_type = random.choice(HEADERS_STEAM_NEW), random.choice(HEADERS_STEAM_NEW), "#steam #новинки #релиз"
    elif platform_key == "gacha":
        header, vk_header, tag_type = random.choice(HEADERS_GACHA), random.choice(HEADERS_GACHA), "#genshin #honkai #промокоды"
    elif platform_key == "mobile":
        header, vk_header, tag_type = random.choice(HEADERS_MOBILE), random.choice(HEADERS_MOBILE), "#mobile #мобильныеигры"
    elif is_free:
        header, vk_header, tag_type = random.choice(HEADERS_FREE), random.choice(VK_HEADERS_FREE), "#раздача #freegames"
    else:
        header, vk_header, tag_type = random.choice(HEADERS_DISCOUNT), random.choice(VK_HEADERS_DISCOUNT), "#скидки #deals"

    # Логика выбора правильного баннера-заглушки
    fallback_category = "default"
    if "roblox" in platform_key or "roblox" in platform.lower():
        fallback_category = "roblox"
    elif "steam_new" in platform_key or ("steam" in platform.lower() and is_free):
        fallback_category = "steam"
    elif "epic" in platform_key or "epic" in platform.lower():
        fallback_category = "epic"
    elif "gog" in platform_key or "gog" in platform.lower():
        fallback_category = "gog"
    elif "gacha" in platform_key:
        fallback_category = "gacha" if "code" in title.lower() else "gacha_sale"
    elif "vkplay" in platform_key or "vk" in platform.lower():
        fallback_category = "vkplay"
    elif "mobile" in platform_key:
        fallback_category = "mobile"
    elif "key" in title.lower():
        fallback_category = "steam_keys"

    fallback_url = FALLBACK_IMAGES.get(fallback_category, FALLBACK_IMAGES["default"])

    # ==========================================
    # 1. ФОРМИРУЕМ ПОСТ ДЛЯ TELEGRAM
    # ==========================================
    main_caption = f"{header}\n\n"
    main_caption += f"📌 <b>Название:</b> {title}\n"
    main_caption += f"🌐 <b>Магазин:</b> {platform}\n\n"
    
    if is_free:
        if worth > 0:
            main_caption += f"💳 Без раздачи: <s>${worth:.2f}</s>\n"
        main_caption += f"🎁 Сейчас: <b>0₽ [БЕСПЛАТНО]</b>\n\n"
    else:
        main_caption += f"🏷️ <b>Цена по скидке:</b> {price_raw}\n\n"
        
    if desc:
        main_caption += f"📖 <b>Кратко об игре:</b>\n<i>{desc}</i>\n\n"
        
    main_caption += f"{tag_type} #{hashtag_plat}"

    main_markup = {
        "inline_keyboard": [
            [{"text": random.choice(BTN_GET_GAME), "url": link}],
            [{"text": "🔵 Мы ВКонтакте", "url": VK_GROUP_URL}],
            [{"text": random.choice(BTN_GET_APP), "url": APP_LINK}]
        ]
    }

    # ==========================================
    # 2. ФОРМИРУЕМ ПОСТ ДЛЯ ВКОНТАКТЕ
    # ==========================================
    vk_caption = f"{vk_header}\n\n"
    vk_caption += f"📌 Игра: {title}\n"
    vk_caption += f"🌐 Площадка: {platform}\n"
    
    if is_free:
        if worth > 0:
            vk_caption += f"💳 Обычная цена: ${worth:.2f} ➡️ 0₽\n"
        vk_caption += f"🎁 Статус: 100% БЕСПЛАТНО\n\n"
    else:
        vk_caption += f"🏷️ Цена: {price_raw}\n\n"
        
    if desc:
        vk_caption += f"📖 Об игре:\n{desc}\n\n"
        
    vk_caption += f"───────────────\n"
    vk_caption += f"🔻 {random.choice(VK_LINK_TEXTS)} 🔻\n"
    vk_caption += f"{link}\n"
    vk_caption += f"───────────────\n\n"
    
    vk_caption += f"✈️ Больше эксклюзивной халявы в нашем Telegram-канале:\n"
    vk_caption += f"👉 {TG_CHANNEL_URL}\n\n"
    vk_caption += f"⚡ Хочешь узнавать о раздачах прямо на рабочем столе ПК?\n"
    vk_caption += f"💻 Скачивай нашу программу: {APP_LINK}"

    # ==========================================
    # ОТПРАВКА
    # ==========================================
    def send_request(target_chat_id, text_caption, markup=None):
        if not target_chat_id: return
        try:
            payload = {"chat_id": target_chat_id, "caption": text_caption, "parse_mode": "HTML"}
            if markup: payload["reply_markup"] = markup
            if img_url:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                payload["photo"] = img_url
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                payload["text"] = text_caption
                del payload["caption"]
            requests.post(url, json=payload, timeout=10).raise_for_status()
        except Exception as e:
            print(f"❌ Ошибка отправки ТГ: {e}")

    # Отправляем в ТГ
    send_request(TG_CHAT_ID, main_caption, main_markup)
    print(f"✅ Отправлено в Telegram: {title}")

    # Отправляем в ВК (передаем и оригинал картинки, и ссылку на твой баннер)
    send_vk_wall_post(vk_caption, img_url, fallback_url)

def get_unseen_items(nm, games):
    new_items = []
    now = nm._now_ts()
    for g in games or []:
        gid = nm._game_id(g)
        if gid not in nm.seen:
            new_items.append(g)
            nm.seen[gid] = now
    if new_items: nm._save_seen()
    return new_items

def main():
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ ОШИБКА: Секреты не найдены!")
        sys.exit(1)

    print("🤖 Запуск парсера GameGiveawaysPro...")
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    raw_free = []
    for func in [api.fetch_cheapshark_free, api.fetch_gamerpower_pc, api.fetch_gamerpower_loot]:
        try: raw_free.extend(func(15))
        except: pass
    
    free_games = [g for g in raw_free if str(g.get("price", "")).strip().upper() == "FREE" and "gacha" not in g.get("platformkey", "") and "mobile" not in g.get("platformkey", "")]
    new_freebies = get_unseen_items(nm, free_games)

    roblox_items = []
    try: roblox_items = get_unseen_items(nm, api.fetch_roblox_loot(limit=10))
    except: pass

    mobile_items = []
    try: mobile_items = get_unseen_items(nm, api.fetch_gacha_mobile_loot(limit=10))
    except: pass

    discounts = []
    try:
        discounts.extend(get_unseen_items(nm, api.fetch_cheapshark_discounts(limit=25, max_price=50.0, min_savings=10.0)))
        discounts.extend(get_unseen_items(nm, api.fetch_vkplay_discounts(limit=10, min_savings=10.0)))
    except: pass

    steam_new = []
    try: steam_new = get_unseen_items(nm, api.fetch_steam_new_releases(limit=10))
    except: pass

    total_posted = 0

    for game_list, limit in [(new_freebies, None), (roblox_items, None), (mobile_items, None), (discounts, 3), (steam_new, 2)]:
        if game_list:
            if limit: random.shuffle(game_list)
            for game in (game_list[:limit] if limit else game_list):
                process_and_send_game(game)
                time.sleep(2)
                total_posted += 1

    if total_posted == 0:
        print("🤷‍♂️ Новых раздач пока нет.")

if __name__ == '__main__':
    main()
