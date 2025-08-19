import json
import os
from aiogram import Router, types
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from .keyboards import get_main_menu

router = Router()

# ПРАВИЛЬНО: Получаем переменную по ее ИМЕНИ
WEBAPP_URL = os.getenv("WEBAPP_URL") 

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    # Добавим проверку, чтобы бот не падал, если переменная не найдена
    if not WEBAPP_URL:
        await message.answer("Извините, магазин временно недоступен (ошибка конфигурации URL).")
        return # Прерываем выполнение

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
