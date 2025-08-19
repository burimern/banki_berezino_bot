import json
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from .keyboards import get_main_menu

# Замените на переменные окружения в реальном проекте
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """
    Этот хэндлер будет вызываться на команду /start
    """
    await message.answer(
        "👋 Добро пожаловать в наш магазин жидкостей для вейпов!\n\n"
        "Нажмите на кнопку ниже, чтобы посмотреть каталог.",
        reply_markup=get_main_menu(WEBAPP_URL)
    )

@dp.message(lambda message: message.content_type == ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    """
    Этот хэндлер принимает данные, отправленные из Web App
    """
    try:
        data = json.loads(message.web_app_data.data)
        # Пример данных: {'items': [{'id': 1, 'title': '...'}], 'total_price': 1500}
        
        # Формируем сообщение для пользователя
        order_details = "✅ Ваш заказ принят!\n\nСостав заказа:\n"
        for item in data.get('items', []):
            order_details += f"- {item.get('title', 'Неизвестно')} (x{item.get('quantity', 1)})\n"
        order_details += f"\nИтого: {data.get('total_price', 0)} руб."

        await message.answer(order_details)

        # Здесь можно добавить логику сохранения заказа в БД,
        # отправку уведомления администратору и т.д.
        # await notify_admin(data)
        
    except json.JSONDecodeError:
        await message.answer("❗️ Произошла ошибка при обработке вашего заказа.")
    except Exception as e:
        await message.answer(f"❗️ Что-то пошло не так: {e}")
