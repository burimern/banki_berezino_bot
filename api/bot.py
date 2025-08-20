# Файл: api/bot.py
import os
import json
import asyncio
import html
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- Инициализация Flask и Dispatcher (без создания Bot) ---
app = Flask(__name__)
dp = Dispatcher()

# --- Хэндлеры Aiogram ---

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """Обработчик команды /start"""
    WEBAPP_URL = os.getenv("WEBAPP_URL")
    if not WEBAPP_URL:
        await message.answer("Ошибка конфигурации: URL магазина не найден.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Перейти в каталог", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await message.answer("👋 Добро пожаловать! Нажмите кнопку ниже, чтобы открыть наш каталог.", reply_markup=keyboard)


@dp.message(Command("test"))
async def send_test_message(message: types.Message):
    """Отправляет тестовое сообщение в чат админа по команде /test"""
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    await message.answer(f"Пытаюсь отправить тестовое сообщение в чат с ID: {ADMIN_CHAT_ID}")
    
    if not ADMIN_CHAT_ID:
        await message.answer("Ошибка: ADMIN_CHAT_ID не установлен.")
        return

    try:
        # bot берется из контекста dp.feed_update
        await message.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="✅ Это тестовое сообщение. Если вы его видите, значит, бот может писать в этот чат."
        )
        await message.answer("✅ Успешно! Сообщение должно было прийти в чат.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке:\n\n<pre>{html.escape(str(e))}</pre>", parse_mode="HTML")


@dp.message(lambda message: message.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    """Обработчик данных из Web App"""
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
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
            # bot берется из контекста dp.feed_update
            await message.bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
        else:
            print("WARNING: ADMIN_CHAT_ID is not set.")

        await message.answer("✅ Спасибо! Ваш заказ отправлен.")
    except Exception as e:
        print(f"!!! CRITICAL ERROR processing order: {e}", flush=True)
        await message.answer("❗️ Произошла ошибка при обработке заказа.")


# --- Flask-часть для приема вебхуков ---

async def process_update(bot: Bot, update_data: dict):
    """Главная асинхронная функция для обработки входящего запроса"""
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route('/api/bot', methods=['POST'])
def webhook_handler():
    """Основной маршрут, который принимает вебхуки от Telegram"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("CRITICAL: BOT_TOKEN is not set!")
        return "Bot token not provided", 500

    bot_instance = Bot(token=BOT_TOKEN)
    update_data = request.get_json()
    asyncio.run(process_update(bot_instance, update_data))
    return 'ok', 200
