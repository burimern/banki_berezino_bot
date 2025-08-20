# Файл: api/bot.py
import os
import json
import asyncio
import html
import traceback
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError

app = Flask(__name__)
dp = Dispatcher()

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    WEBAPP_URL = os.getenv("WEBAPP_URL")
    if not WEBAPP_URL: return await message.answer("Ошибка конфигурации: URL магазина не найден.")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти в каталог", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await message.answer("👋 Добро пожаловать! Нажмите кнопку ниже, чтобы открыть наш каталог.", reply_markup=keyboard)

@dp.message(lambda message: message.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    try:
        data = json.loads(message.web_app_data.data)
        user = message.from_user
        safe_user_firstname = html.escape(str(user.first_name or ''))
        user_link = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{safe_user_firstname}</a>"
        
        admin_message = f"🚨 **Новый заказ от клиента:** {user_link}\n\n"
        admin_message += "--- Состав заказа ---\n"
        for item in data.get('items', []):
            safe_item_name = html.escape(str(item.get('name', '?')))
            admin_message += f"• {safe_item_name} (x{item.get('quantity', 1)}) - {item.get('price', 0) * item.get('quantity', 1)} руб.\n"
        admin_message += f"\n💰 **Итого:** {data.get('total_price', 0)} руб.\n\n"
        admin_message += "Напишите клиенту для уточнения деталей."

        if not ADMIN_CHAT_ID:
            print("WARNING: ADMIN_CHAT_ID is not set.")
            return await message.answer("✅ Заказ принят (админ не настроен).")

        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ---
        try:
            await message.bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
            await message.answer("✅ Спасибо! Ваш заказ отправлен.")
        except TelegramAPIError as e:
            # Если отправка в группу не удалась, отправляем ошибку пользователю
            error_text = f"Не удалось отправить заказ в группу. Ошибка:\n\n<pre>{html.escape(str(e))}</pre>"
            await message.answer(error_text, parse_mode="HTML")
            # Также логируем ошибку
            print(f"!!! Telegram API Error: {e}")

    except Exception as e:
        print(f"!!! CRITICAL ERROR in handle_web_app_data: {traceback.format_exc()}")
        await message.answer("❗️ Произошла критическая ошибка при обработке заказа.")

# --- Flask-часть (без изменений) ---
async def process_update(bot: Bot, update_data: dict):
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route('/api/bot', methods=['POST'])
def webhook_handler():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("CRITICAL: BOT_TOKEN is not set!")
        return "Bot token not provided", 500
    bot_instance = Bot(token=BOT_TOKEN)
    update_data = request.get_json()
    asyncio.run(process_update(bot_instance, update_data))
    return 'ok', 200
