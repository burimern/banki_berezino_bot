# Файл: api/bot.py
import os
import json
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- Инициализация ---
app = Flask(__name__)
dp = Dispatcher()

# --- Хэндлеры ---

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    WEBAPP_URL = os.getenv("WEBAPP_URL")
    if not WEBAPP_URL:
        return await message.answer("Ошибка конфигурации.")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Каталог", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await message.answer("Добро пожаловать!", reply_markup=keyboard)

@dp.message(lambda message: message.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    # --- СНАЧАЛА отвечаем пользователю, чтобы он не ждал ---
    await message.answer("✅ Спасибо, принял ваш заказ в обработку!")

    # --- ТЕПЕРЬ без спешки готовим и отправляем сообщение админу ---
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    if not ADMIN_CHAT_ID:
        print("CRITICAL: ADMIN_CHAT_ID is not set!")
        return # Просто выходим, пользователь уже получил ответ

    try:
        data = json.loads(message.web_app_data.data)
        user = message.from_user
        
        # --- Максимально упрощаем сообщение, убираем HTML-форматирование ---
        user_info = f"@{user.username}" if user.username else f"ID: {user.id} ({user.first_name})"
        
        admin_message = f"Новый заказ от: {user_info}\n\n"
        admin_message += "Состав:\n"
        for item in data.get('items', []):
            admin_message += f"- {item.get('name', '?')} x{item.get('quantity', 1)}\n"
        admin_message += f"\nИтого: {data.get('total_price', 0)} руб."

        await message.bot.send_message(ADMIN_CHAT_ID, admin_message) # Убрали parse_mode
        
    except Exception as e:
        # Если что-то пошло не так, отправляем ошибку админу
        error_text = f"Ошибка при обработке заказа от {user_info}:\n{e}"
        await message.bot.send_message(ADMIN_CHAT_ID, error_text)

# --- Flask-часть ---
async def process_update(bot: Bot, update_data: dict):
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route('/api/bot', methods=['POST'])
def webhook_handler():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        return "Bot token not provided", 500
        
    bot_instance = Bot(token=BOT_TOKEN)
    update_data = request.get_json()
    # Запускаем обработку в фоне, чтобы сразу вернуть ответ Telegram
    asyncio.get_event_loop().run_in_executor(None, asyncio.run, process_update(bot_instance, update_data))
    return 'ok', 200
