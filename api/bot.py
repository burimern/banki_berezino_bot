import os
import json
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_menu(url: str) -> InlineKeyboardMarkup:
    web_app = WebAppInfo(url=url)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Каталог товаров", web_app=web_app)]]
    )
    return keyboard

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    if not WEBAPP_URL:
        await message.answer("Ошибка: URL для Web App не настроен.")
        return
    await message.answer(
        "👋 Добро пожаловать в наш магазин!",
        reply_markup=get_main_menu(WEBAPP_URL)
    )

@dp.message(lambda message: message.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        user = message.from_user
        user_link = f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

        admin_message = f"🚨 **Новый заказ от клиента:** {user_link}\n\n"
        admin_message += "--- Состав заказа ---\n"
        for item in data.get('items', []):
            admin_message += f"• {item.get('name', '?')} (x{item.get('quantity', 1)}) - {item.get('price', 0) * item.get('quantity', 1)} руб.\n"
        admin_message += f"\n💰 **Итого:** {data.get('total_price', 0)} руб.\n\n"
        admin_message += "Напишите клиенту для уточнения деталей доставки."

        if ADMIN_CHAT_ID:
            await bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
        else:
            print("WARNING: ADMIN_CHAT_ID is not set.")

        await message.answer("✅ Спасибо! Ваш заказ отправлен менеджеру. Он скоро свяжется с вами для уточнения деталей.")

    except Exception as e:
        print(f"ERROR processing order: {e}")
        await message.answer(f"❗️ Произошла ошибка при отправке заказа.")

async def handle_update(update_data):
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

@app.route('/api/bot', methods=['POST'])
def process_webhook():
    update_data = request.get_json()
    asyncio.run(handle_update(update_data))
    return 'ok', 200
