import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- ВАЖНО: Получаем переменные из Vercel Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# --- Настраиваем Flask-сервер, который будет принимать запросы от Telegram ---
# Vercel будет запускать именно его
from flask import Flask, request

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Ваши хэндлеры (обработчики сообщений) ---
# Мы просто перенесли их сюда

def get_main_menu(url: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой Web App."""
    web_app = WebAppInfo(url=url)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог товаров", web_app=web_app)]
        ]
    )
    return keyboard

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение с кнопкой Web App."""
    if not WEBAPP_URL:
        await message.answer("Ошибка: URL для Web App не настроен.")
        return
    await message.answer(
        "👋 Добро пожаловать в наш магазин!",
        reply_markup=get_main_menu(WEBAPP_URL)
    )

# --- Главный обработчик вебхуков ---
# Это "входная дверь" для всех сообщений от Telegram
@app.route('/', methods=['POST'])
def process_webhook():
    # Запускаем асинхронную обработку обновления
    asyncio.run(handle_update())
    return 'ok', 200

async def handle_update():
    """Разбирает запрос и передает его в Aiogram."""
    update_data = request.get_json()
    update = types.Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

# Этот хэндлер НЕ НУЖЕН для вебхуков, но Vercel требует, чтобы что-то было на GET запросе
@app.route('/', methods=['GET'])
def home():
    return "Bot is running (webhook listener)."
