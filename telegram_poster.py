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
TG_DZEN_CHAT_ID = os.environ.get("TG_DZEN_CHAT_ID") 

# ==========================================
# СЛОВАРИ ДЛЯ ТЕЛЕГРАМА
# ==========================================
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

# ==========================================
# СЛОВАРИ ДЛЯ ДЗЕНА И ОК (Уникальные заголовки)
# ==========================================
DZEN_HEADERS_FREE = [
    "🔥 Очередная годнота подъехала:",
    "🎁 Разработчики расщедрились, забираем:",
    "⚡ Забираем на аккаунт, пока бесплатно:",
    "🎉 Раздача дня, лутаем:",
    "🎮 Отличное пополнение вашей библиотеки:",
    "🤑 100% скидка на отличный проект:",
    "🚀 Хватай, пока дают:",
    "💸 Абсолютная халява, забираем:",
    "📦 Новый подарок для геймеров:",
    "🎯 Топовый подгон на сегодня:"
]
DZEN_HEADERS_DISCOUNT = [
    "📉 Отличная скидка нарисовалась:",
    "🏷️ Забираем по вкусной цене:",
    "💥 Мощный ценопад на игру:",
    "💰 Бережем кошелек, крутая скидка на:"
]
DZEN_LINK_TEXTS = [
    "👉 Забрать игру на свой аккаунт",
    "🎮 Добавить в библиотеку",
    "⚡ Получить бесплатно",
    "🚀 Перейти к раздаче",
    "🎁 Забрать подарок",
    "🛒 Открыть страницу в магазине"
]

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
        if len(desc) > 160:
            desc = desc[:157] + "..."
            
    # Выбор тегов и заголовков для ТГ
    if platform_key == "roblox" or "roblox" in platform.lower():
        header = random.choice(HEADERS_ROBLOX)
        dzen_header = random.choice(HEADERS_ROBLOX)
        tag_type = "#roblox #роблокс"
    elif platform_key == "steam_new":
        header = random.choice(HEADERS_STEAM_NEW)
        dzen_header = random.choice(HEADERS_STEAM_NEW)
        tag_type = "#steam #новинки #релиз"
    elif platform_key == "gacha":
        header = random.choice(HEADERS_GACHA)
        dzen_header = random.choice(HEADERS_GACHA)
        tag_type = "#genshin #honkai #промокоды"
    elif platform_key == "mobile":
        header = random.choice(HEADERS_MOBILE)
        dzen_header = random.choice(HEADERS_MOBILE)
        tag_type = "#mobile #мобильныеигры"
    elif is_free:
        header = random.choice(HEADERS_FREE)
        dzen_header = random.choice(DZEN_HEADERS_FREE)
        tag_type = "#раздача #freegames"
    else:
        header = random.choice(HEADERS_DISCOUNT)
        dzen_header = random.choice(DZEN_HEADERS_DISCOUNT)
        tag_type = "#скидки #deals"

    price_pref = random.choice(PRICE_PREFIXES)
    desc_pref = random.choice(DESC_PREFIXES)
            
    # 1. Текст для основного ТГ-канала
    main_caption = f"{header}: <b>{title}</b>\n\n"
    main_caption += f"🌐 <b>Платформа:</b> {platform}\n"
    
    if is_free:
        if worth > 0:
            main_caption += f"{price_pref} <s>${worth:.2f}</s> ➡️ <b>0₽ (FREE)</b>\n"
        else:
            main_caption += f"{price_pref} <b>100% Бесплатно!</b>\n"
    else:
        main_caption += f"🏷️ <b>Цена:</b> {price_raw}\n"
        
    if desc:
        main_caption += f"\n{desc_pref} <i>{desc}</i>\n"
        
    main_caption += f"\n{tag_type} #{hashtag_plat}"

    main_markup = {
        "inline_keyboard": [
            [{"text": random.choice(BTN_GET_GAME), "url": link}]
        ]
    }

    # 2. Текст для буферного канала Дзена / ОК
    dzen_caption = f"{dzen_header} <b>{title}</b>\n\n"
    dzen_caption += f"🌐 <b>Платформа:</b> {platform}\n\n"
    
    if not is_free:
        dzen_caption += f"🏷️ <b>Цена:</b> {price_raw}\n\n"
        
    if desc:
        dzen_caption += f"📖 {desc}\n\n"
        
    if is_free:
        dzen_caption += "⚡ <b>НЕТ ПРОСТО РАЗДАЕМ КТО УСПЕЛ ТОТ И СЬЕЛ)</b>\n\n"
        
    random_link_text = random.choice(DZEN_LINK_TEXTS)
    dzen_caption += f"<a href='{link}'>{random_link_text}</a>"

    # Функция отправки запроса в Telegram
    def send_request(target_chat_id, text_caption, markup=None):
        if not target_chat_id:
            return
        try:
            payload = {
                "chat_id": target_chat_id, 
                "caption": text_caption, 
                "parse_mode": "HTML"
            }
            if markup:
                payload["reply_markup"] = markup
                
            if img_url:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                payload["photo"] = img_url
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                payload["text"] = text_caption
                del payload["caption"]
                
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
        except Exception as e:
            print(f"❌ Ошибка отправки в чат {target_chat_id}: {e}")

    # Отправляем в основной канал
    send_request(TG_CHAT_ID, main_caption, main_markup)
    print(f"✅ Отправлено в основной ТГ: {title}")

    # Отправляем в буферный канал для Дзена (теперь идет ВСЁ)
    if TG_DZEN_CHAT_ID:
        send_request(TG_DZEN_CHAT_ID, dzen_caption, markup=None)
        print(f"✅ Отправлено в буфер Дзена: {title}")


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

    print("🤖 Запуск парсера GameGiveawaysPro...")
    api = GameAPI(usegamerpower=True)
    nm = NotificationManager(parent=None)
    
    raw_free = []
    try: raw_free.extend(api.fetch_cheapshark_free(15))
    except: pass
    try: raw_free.extend(api.fetch_gamerpower_pc(15))
    except: pass
    try: raw_free.extend(api.fetch_gamerpower_loot(15))
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

    steam_new_items = []
    try: steam_new_items = get_unseen_items(nm, api.fetch_steam_new_releases(limit=10))
    except: pass

    total_posted = 0

    # Теперь все списки используют общую функцию отправки в оба канала
    if new_freebies:
        for game in new_freebies:
            process_and_send_game(game)
            time.sleep(2)
            total_posted += 1

    if roblox_items:
        for game in roblox_items:
            process_and_send_game(game)
            time.sleep(2)
            total_posted += 1

    if mobile_items:
        for game in mobile_items:
            process_and_send_game(game)
            time.sleep(2)
            total_posted += 1

    if discounts:
        random.shuffle(discounts)
        for game in discounts[:3]: 
            process_and_send_game(game)
            time.sleep(2)
            total_posted += 1

    if steam_new_items:
        for game in steam_new_items[:2]:  
            process_and_send_game(game)
            time.sleep(2)
            total_posted += 1

    if total_posted == 0:
        print("🤷‍♂️ Новых раздач пока нет.")

if __name__ == '__main__':
    main()
    
