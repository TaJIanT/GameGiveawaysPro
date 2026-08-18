# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import requests
from api import GameAPI
from notifications import NotificationManager
from vk_uploader import send_vk_wall_post  # Наш новый модуль ВК

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

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

VK_HEADERS_FREE = [
    "🔥 Очередная годнота подъехала:", "🎁 Разработчики расщедрились, забираем:",
    "⚡ Забираем на аккаунт, пока бесплатно:", "🎉 Раздача дня, лутаем:",
    "🎮 Отличное пополнение вашей библиотеки:", "🤑 100% скидка на отличный проект:",
    "🚀 Хватай, пока дают:", "💸 Абсолютная халява, забираем:",
    "📦 Новый подарок для геймеров:", "🎯 Топовый подгон на сегодня:"
]
VK_HEADERS_DISCOUNT = ["📉 Отличная скидка нарисовалась:", "🏷️ Забираем по вкусной цене:", "💥 Мощный ценопад на игру:", "💰 Бережем кошелек, крутая скидка на:"]
VK_LINK_TEXTS = ["👉 Забрать игру на свой аккаунт", "🎮 Добавить в библиотеку", "⚡ Получить бесплатно", "🚀 Перейти к раздаче", "🎁 Забрать подарок", "🛒 Открыть страницу в магазине"]

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

    price_pref = random.choice(PRICE_PREFIXES)
    desc_pref = random.choice(DESC_PREFIXES)
            
    # ТГ Текст
    main_caption = f"{header}: <b>{title}</b>\n\n🌐 <b>Платформа:</b> {platform}\n"
    if is_free:
        main_caption += f"{price_pref} <s>${worth:.2f}</s> ➡️ <b>0₽ (FREE)</b>\n" if worth > 0 else f"{price_pref} <b>100% Бесплатно!</b>\n"
    else:
        main_caption += f"🏷️ <b>Цена:</b> {price_raw}\n"
    if desc: main_caption += f"\n{desc_pref} <i>{desc}</i>\n"
    main_caption += f"\n{tag_type} #{hashtag_plat}"

    main_markup = {"inline_keyboard": [[{"text": random.choice(BTN_GET_GAME), "url": link}]]}

    # ВК Текст
    vk_caption = f"{vk_header} {title}\n\n🌐 Платформа: {platform}\n\n"
    if not is_free: vk_caption += f"🏷️ Цена: {price_raw}\n\n"
    if desc: vk_caption += f"📖 {desc}\n\n"
    if is_free: vk_caption += "⚡ НЕТ ПРОСТО РАЗДАЕМ КТО УСПЕЛ ТОТ И СЬЕЛ)\n\n"
    
    vk_caption += f"{random.choice(VK_LINK_TEXTS)}:\n{link}\n\nБольше халявы в нашем ТГ канале: @ggpro_free_games"

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

    # Отправляем в ВК
    if img_url:
        send_vk_wall_post(vk_caption, img_url)

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
    
