# -*- coding: utf-8 -*-
import os
import threading
import telebot
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Заглушка для облака, чтобы оно не выключало бота
@app.route('/')
def index():
    return "Бот-охранник работает!"

# Моментальное одобрение заявок
@bot.chat_join_request_handler()
def approve_join(message):
    try:
        bot.approve_chat_join_request(message.chat.id, message.from_user.id)
        print(f"✅ Принята заявка от: {message.from_user.first_name}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def run_bot():
    print("🤖 Бот запущен и ждет заявок...")
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
