# Файл: api/bot.py
import os
import json
import asyncio
import html
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- Получаем переменные окружения ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# --- Инициализация ---
app = Flask(__name__)
# Убедимся, что токен существует, чтобы избежать падения при запуске
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

# --- Хэндлеры Aiogram ---

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """Обработчик команды /start"""
    if not WEBAPP_URL:
        await message.answer("Ошибка конфигурации: URL магазина не найден.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Перейти в каталог", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
    )
    await message.answer(
        "👋 Добро пожаловать! Нажмите кнопку ниже, чтобы открыть наш каталог.",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    """Обработчик данных, пришедших из Web App"""
    try:
        data = json.loads(message.web_app_data.data)
        user = message.from_user

        safe_user_firstname = html.escape(user.first_name)
        user_link = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{safe_user_firstname}</a>"

        admin_message = f"🚨 **Новый заказ от клиента:** {user_link}\n\n"
        admin_message += "--- Состав заказа ---\n"
        for item in data.get('items', []):
            safe_item_name = html.escape(item.get('name', '?'))
            admin_message += f"• {safe_item_name} (x{item.get('quantity', 1)}) - {item.get('price', 0) * item.get('quantity', 1)} руб.\n"
        
        admin_message += f"\n💰 **Итого:** {data.get('total_price', 0)} руб.\n\n"
        admin_message += "Напишите клиенту для уточнения деталей."

        if ADMIN_CHAT_ID:
            await bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
        else:
            print("WARNING: ADMIN_CHAT_ID is not set.")

        await message.answer("✅ Спасибо! Ваш заказ отправлен менеджеру. Он скоро свяжется с вами.")
    except Exception as e:
        print(f"!!! CRITICAL ERROR processing order: {e}", flush=True)
        await message.answer("❗️ Произошла ошибка при обработке вашего заказа.")

# --- Flask-часть для приема вебхуков ---

async def process_update(update_data):
    """Главная асинхронная функция для обработки входящего запроса"""
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route('/api/bot', methods=['POST'])
def webhook_handler():
    """Основной маршрут, который принимает вебхуки от Telegram"""
    if not bot:
        return "Bot token not provided", 500

    update_data = request.get_json()
    asyncio.run(process_update(update_data))
    return 'ok', 200
