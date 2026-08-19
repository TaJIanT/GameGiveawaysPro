# -*- coding: utf-8 -*-
import os
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# Токен подтягивается автоматически из настроек Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Твои данные
CHANNEL_USERNAME = "@ggpro_free_games"
GITHUB_LINK = "https://github.com/TaJIanT/GameGiveawaysPro/releases/tag/v1.0.6"

# Заглушка, чтобы облако Render не усыпляло бота
@app.route('/')
def index():
    return "Бот-прокладка работает 24/7!"

# 1. Приветствие и кнопки (минимум текста для пользователя)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=1)
    btn_sub = InlineKeyboardButton("1️⃣ Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    btn_check = InlineKeyboardButton("2️⃣ Забрать программу", callback_data="check_sub")
    markup.add(btn_sub, btn_check)

    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Доступ к приватной утилите **GameGiveawaysPro** открыт только для подписчиков нашего канала.\n\n"
        f"Подпишись на {CHANNEL_USERNAME} и жми кнопку ниже 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# 2. Проверка подписки и выдача файла
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    try:
        # Проверяем статус в основном канале
        status = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id).status
        
        if status in ['member', 'administrator', 'creator']:
            # Незаметный ответ-уведомление сверху экрана
            bot.answer_callback_query(call.id, "✅ Проверка пройдена!")
            
            # Красивый финальный текст с прямой ссылкой на релиз
            success_text = (
                "🎉 **Доступ открыт!**\n\n"
                "Твоя утилита готова к загрузке. Она будет сама мониторить халяву и присылать уведомления на рабочий стол.\n\n"
                f"👉 [Скачать GameGiveawaysPro (v1.0.6)]({GITHUB_LINK})\n\n"
                "_Ссылка ведет на официальный репозиторий GitHub._"
            )
            
            # Меняем сообщение (кнопки исчезают, появляется ссылка)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=success_text,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            # Ругаемся всплывающим окном, если не подписался
            bot.answer_callback_query(call.id, "❌ Подписка не найдена!\n\nСначала подпишись на канал, затем жми кнопку.", show_alert=True)
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка. Убедитесь, что бот назначен админом канала.", show_alert=True)

def run_bot():
    print("🤖 Бот запущен и готов к работе!")
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
