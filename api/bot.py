# Файл: api/bot.py
import os
import json
import asyncio
import html
import traceback
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- Инициализация ---
app = Flask(__name__)
dp = Dispatcher()

# --- Глобальный обработчик ошибок ---
@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    if ADMIN_CHAT_ID:
        try:
            tb_str = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            error_message = (
                f"🚨 <b>Ошибка в боте!</b>\n\n"
                f"<b>Тип:</b> {html.escape(str(type(exception).__name__))}\n"
                f"<b>Сообщение:</b> {html.escape(str(exception))}\n\n"
                f"<b>Traceback:</b>\n<pre>{html.escape(tb_str)}</pre>"
            )
            if len(error_message) > 4096:
                error_message = error_message[:4090] + "..."
            await update.bot.send_message(chat_id=ADMIN_CHAT_ID, text=error_message, parse_mode="HTML")
        except Exception as e:
            print(f"!!! Не удалось отправить ошибку админу: {e}")
    return True

# --- Старт ---
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    WEBAPP_URL = os.getenv("WEBAPP_URL")
    if not WEBAPP_URL:
        return await message.answer("Ошибка конфигурации: нет WEBAPP_URL")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("Добро пожаловать в магазин! 👋", reply_markup=keyboard)

# --- Обработка заказа из WebApp ---
@dp.message(lambda m: m.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

    try:
        data = json.loads(message.web_app_data.data)
    except Exception as e:
        return await message.answer(f"❌ Ошибка разбора данных заказа: {e}")

    user = message.from_user
    safe_user_firstname = html.escape(str(user.first_name or ''))
    user_link = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{safe_user_firstname}</a>"

    admin_message = f"🛒 <b>Новый заказ</b>\n\n👤 Клиент: {user_link}\n\n"

    # Состав заказа
    total = 0
    for item in data.get("items", []):
        safe_item_name = html.escape(str(item.get("name", "?")))
        quantity = int(item.get("quantity", 1))
        price = float(item.get("price", 0))
        subtotal = price * quantity
        total += subtotal
        admin_message += f"• {safe_item_name} (x{quantity}) — {subtotal} руб.\n"

    admin_message += f"\n💰 <b>Итого:</b> {data.get('total_price', total)} руб.\n"
    admin_message += "\nНапишите клиенту для уточнения деталей."

    if ADMIN_CHAT_ID:
        await message.bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")

    await message.answer("✅ Спасибо! Ваш заказ отправлен менеджеру.")

# --- Flask-часть ---
async def process_update(bot: Bot, update_data: dict):
    print("=== Update ===")
    print(update_data)  # лог для дебага
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route("/api/bot", methods=["POST"])
def webhook_handler():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        return "Bot token not provided", 500

    bot_instance = Bot(token=BOT_TOKEN)
    update_data = request.get_json()
    asyncio.run(process_update(bot_instance, update_data))
    return "ok", 200
