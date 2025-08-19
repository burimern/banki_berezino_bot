import json
import os
from aiogram import Router, types
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from .keyboards import get_main_menu

router = Router()
WEBAPP_URL = os.getenv("WEBAPP_URL") # Будем брать из настроек Vercel

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в наш магазин!\n\n"
        "Нажмите на кнопку ниже, чтобы посмотреть каталог.",
        reply_markup=get_main_menu(WEBAPP_URL)
    )

@router.message(lambda message: message.content_type == ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        order_details = "✅ Ваш заказ принят!\n\nСостав заказа:\n"
        for item in data.get('items', []):
            order_details += f"- {item.get('title', 'Неизвестно')} (x{item.get('quantity', 1)})\n"
        order_details += f"\nИтого: {data.get('total_price', 0)} руб."
        await message.answer(order_details)
    except Exception as e:
        await message.answer(f"❗️ Что-то пошло не так при обработке заказа: {e}")
