# -*- coding: utf-8 -*-
import os
import re
import requests

VK_TOKEN = os.environ.get("VK_TOKEN")
VK_GROUP_ID = "152331651"
VK_API_VERSION = "5.193"

def clean_html(raw_html):
    """Вычищает HTML-теги, чтобы в ВК был красивый текст без <b> и <i>"""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def _upload_photo_to_vk(img_url):
    try:
        print(f"🔄 Скачиваем картинку: {img_url}")
        r_img = requests.get(img_url, timeout=10)
        if r_img.status_code != 200:
            print(f"⚠️ Ошибка скачивания картинки (код {r_img.status_code})")
            return None
            
        img_data = r_img.content
        
        print("🔄 Запрашиваем сервер ВК для загрузки фото...")
        r_server = requests.get("https://api.vk.com/method/photos.getWallUploadServer", params={
            "access_token": VK_TOKEN, "v": VK_API_VERSION, "group_id": VK_GROUP_ID
        }).json()
        
        if "error" in r_server: 
            print(f"⚠️ Ошибка получения сервера ВК: {r_server['error']}")
            return None
        
        upload_url = r_server['response']['upload_url']
        files = {'photo': ('cover.jpg', img_data, 'image/jpeg')}
        r_upload = requests.post(upload_url, files=files).json()

        if "error" in r_upload or not r_upload.get('photo'):
            print(f"⚠️ Ошибка загрузки файла на сервер ВК: {r_upload}")
            return None

        r_save = requests.post("https://api.vk.com/method/photos.saveWallPhoto", data={
            "access_token": VK_TOKEN, "v": VK_API_VERSION, "group_id": VK_GROUP_ID,
            "server": r_upload.get('server'), "photo": r_upload.get('photo'), "hash": r_upload.get('hash')
        }).json()

        if "error" in r_save:
            print(f"⚠️ Ошибка сохранения фото в ВК: {r_save['error']}")
            return None
            
        photo_info = r_save['response'][0]
        attachment_str = f"photo{photo_info['owner_id']}_{photo_info['id']}"
        print(f"✅ Картинка успешно загружена на сервер ВК: {attachment_str}")
        return attachment_str
        
    except Exception as e:
        print(f"⚠️ Критическая ошибка при обработке фото: {e}")
        return None

def send_vk_wall_post(html_text, img_url=None, fallback_url=None):
    if not VK_TOKEN: 
        print("❌ Токен ВК не найден")
        return False
    
    # Очищаем текст от HTML-тегов перед отправкой
    clean_text = clean_html(html_text)
    
    photo_attachment = None
    if img_url: 
        photo_attachment = _upload_photo_to_vk(img_url)
        
    if not photo_attachment and fallback_url: 
        print("⏳ Оригинал не удался. Пробуем загрузить ЗАПАСНУЮ картинку (заглушку)...")
        photo_attachment = _upload_photo_to_vk(fallback_url)

    post_data = {
        "access_token": VK_TOKEN, "v": VK_API_VERSION,
        "owner_id": f"-{VK_GROUP_ID}", "from_group": 1, "message": clean_text
    }
    if photo_attachment: 
        post_data["attachments"] = photo_attachment

    print("🔄 Отправляем пост на стену...")
    r = requests.post("https://api.vk.com/method/wall.post", data=post_data).json()
    
    if "error" in r:
        print(f"❌ Ошибка публикации поста: {r['error']}")
    else:
        print("✅ Пост в ВК успешно опубликован!")
        
    return "response" in r
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
