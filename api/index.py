import os
import json
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler
from .bot import start, button_callback_handler

# Инициализация Flask приложения
app = Flask(__name__)

# Получение токена бота из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Настройка диспетчера
dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Основная функция, которая обрабатывает вебхуки от Telegram."""
    if request.method == "POST":
        update_data = request.get_json(force=True)
        update = Update.decompress(update_data, bot)
        dispatcher.process_update(update)
    return 'ok'

@app.route('/api/set_webhook', methods=['GET'])
def set_webhook():
    """Устанавливает вебхук для бота. Вызывается один раз при деплое."""
    VERCEL_URL = os.getenv('VERCEL_URL')
    if VERCEL_URL:
        url = f'https://{VERCEL_URL}/api/webhook'
        is_set = bot.set_webhook(url)
        if is_set:
            return "Webhook установлен!"
        else:
            return "Не удалось установить вебхук."
    return "Переменная окружения VERCEL_URL не найдена."
