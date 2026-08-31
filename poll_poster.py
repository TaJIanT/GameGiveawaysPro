# -*- coding: utf-8 -*-
import os
import json
import random
import requests
from vk_uploader import send_vk_wall_post

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
POLLS_FILE = "polls.json"

def load_polls():
    if not os.path.exists(POLLS_FILE):
        return []
    with open(POLLS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_polls(polls):
    with open(POLLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(polls, f, ensure_ascii=False, indent=2)

def send_tg_poll(question, options):
    """Отправляет нативный опрос в Telegram"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPoll"
    payload = {
        "chat_id": TG_CHAT_ID,
        "question": question,
        "options": options,
        "is_anonymous": True,
        "type": "regular"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("✅ Опрос успешно отправлен в Telegram")
    except Exception as e:
        print(f"❌ Ошибка отправки опроса в ТГ: {e}")

def send_vk_poll_post(question, options):
    """Отправляет текстовый опрос во ВКонтакте с призывом к комментам"""
    # Эмодзи-цифры для красивого оформления в ВК
    numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    # Убраны HTML-теги, так как ВК их не поддерживает
    vk_text = f"🔥 Опрос дня!\n\n🤔 {question}\n\n"
    for i, opt in enumerate(options):
        emoji = numbers[i] if i < len(numbers) else "👉"
        vk_text += f"{emoji} {opt}\n"
        
    vk_text += "\n👇 Пишите цифру или свой развернутый ответ в комментарии! Посмотрим, кого здесь больше!"
    
    try:
        send_vk_wall_post(vk_text, "", "")
        print("✅ Опрос успешно отправлен во ВКонтакте")
    except Exception as e:
        print(f"❌ Ошибка отправки опроса в ВК: {e}")

def main():
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ ОШИБКА: Секреты ТГ не найдены!")
        return

    polls = load_polls()
    
    # Ищем все неиспользованные опросы
    available_polls = [p for p in polls if not p.get("used", False)]
    
    if not available_polls:
        print("🤷‍♂️ Все опросы из базы закончились! Нужно добавить новые.")
        return

    # Берем первый доступный опрос
    current_poll = available_polls[0]
    question = current_poll["question"]
    options = current_poll["options"]

    print(f"🤖 Публикуем опрос: {question}")
    
    # 1. Отправляем в ТГ
    send_tg_poll(question, options)
    
    # 2. Отправляем в ВК
    send_vk_poll_post(question, options)
    
    # Отмечаем как использованный и сохраняем
    current_poll["used"] = True
    save_polls(polls)

if __name__ == '__main__':
    main()
    
