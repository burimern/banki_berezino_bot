# Файл: api/bot.py
import os
import json
import asyncio
import html
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
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Каталог", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await message.answer("Добро пожаловать!", reply_markup=keyboard)

@dp.message(lambda message: message.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    if not ADMIN_CHAT_ID:
        print("CRITICAL: ADMIN_CHAT_ID is not set!")
        # Отвечаем пользователю, даже если админ не настроен
        return await message.answer("Спасибо! Ваш заказ принят, но уведомление администратору не удалось отправить.")

    try:
        data = json.loads(message.web_app_data.data)
        user = message.from_user
        
        # Используем HTML для красивой ссылки
        safe_user_firstname = html.escape(str(user.first_name or ''))
        user_link = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{safe_user_firstname}</a>"
        
        admin_message = f"🚨 **Новый заказ от клиента:** {user_link}\n\n"
        admin_message += "--- Состав заказа ---\n"
        for item in data.get('items', []):
            safe_item_name = html.escape(str(item.get('name', '?')))
            admin_message += f"• {safe_item_name} (x{item.get('quantity', 1)}) - {item.get('price', 0) * item.get('quantity', 1)} руб.\n"
        admin_message += f"\n💰 **Итого:** {data.get('total_price', 0)} руб.\n\n"
        admin_message += "Напишите клиенту для уточнения деталей."

        await message.bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
        await message.answer("✅ Спасибо! Ваш заказ отправлен менеджеру. Он скоро свяжется с вами.")
        
    except Exception as e:
        print(f"!!! CRITICAL ERROR processing order: {e}")
        # Если что-то пошло не так, отправляем ошибку админу для диагностики
        error_text = f"❌ Ошибка при обработке заказа от {user.id}:\n\n<pre>{html.escape(str(e))}</pre>"
        await message.bot.send_message(ADMIN_CHAT_ID, error_text, parse_mode="HTML")
        # И отвечаем пользователю
        await message.answer("❗️ Произошла внутренняя ошибка при обработке вашего заказа. Администратор уже уведомлен.")

# --- Flask-часть ---
async def process_update(bot: Bot, update_data: dict):
    # Эта функция остается простой
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route('/api/bot', methods=['POST'])
def webhook_handler():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        return "Bot token not provided", 500
        
    bot_instance = Bot(token=BOT_TOKEN)
    update_data = request.get_json()
    # Возвращаемся к простому и надежному asyncio.run
    asyncio.run(process_update(bot_instance, update_data))
    return 'ok', 200
