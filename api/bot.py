import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not BOT_TOKEN or not WEBAPP_URL:
    raise RuntimeError("Необходимо задать BOT_TOKEN и WEBAPP_URL в .env")

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Flask-приложение
app = Flask(__name__)

# Обработчик команды /start
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("Добро пожаловать в магазин! 👋", reply_markup=keyboard)

# Функция обработки обновлений через webhook
async def process_update(bot_instance, update_data):
    update = types.Update(**update_data)
    await dp.process_update(update)

# Flask webhook
@app.route("/api/bot", methods=["POST"])
def webhook_handler():
    update_data = request.get_json()
    asyncio.run(process_update(bot, update_data))
    return "ok", 200

# Для локального тестирования (необязательно)
if __name__ == "__main__":
    app.run(port=8000)
