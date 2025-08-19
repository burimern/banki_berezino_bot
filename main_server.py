import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from bot.main import dp, bot  # Импортируем объекты из нашего файла с ботом

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Создаем приложение FastAPI
app = FastAPI()

# "Примонтируем" нашу папку webapp, чтобы FastAPI мог отдавать HTML/CSS/JS файлы
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")


# Функция для запуска бота в режиме polling
async def run_bot():
    await dp.start_polling(bot)

# При старте приложения FastAPI, запускаем бота в фоновом режиме
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(run_bot())

# Можно добавить API эндпоинты, например, для получения товаров
@app.get("/api/products")
async def get_products():
    # Здесь в будущем будет логика получения товаров из БД
    return [
        {"id": 1, "title": "Жидкость 'Лесные ягоды'", "price": 500, "description": "Сладкий микс лесных ягод"},
        {"id": 2, "title": "Жидкость 'Холодный манго'", "price": 550, "description": "Тропический манго с холодком"},
        {"id": 3, "title": "Жидкость 'Табак с вишней'", "price": 480, "description": "Классический вкус с ноткой вишни"}
    ]

# Корневой эндпоинт для проверки
@app.get("/")
def read_root():
    return {"message": "Server is running. Bot is polling."}
