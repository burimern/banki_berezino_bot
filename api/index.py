import os
import asyncio
from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types
from bot_utils.handlers import router as main_router # Импортируем наш роутер

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
# URL, который Telegram будет вызывать. Vercel предоставит его.
WEBHOOK_URL = os.getenv("VERCEL_URL") 
WEBHOOK_PATH = f"/api/webhook/{BOT_TOKEN}"
WEBHOOK_FULL_URL = f"{WEBHOOK_URL}{WEBHOOK_PATH}"

# --- Инициализация ---
app = FastAPI()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(main_router) # Подключаем наши хэндлеры

# --- Логика вебхука ---
@app.on_event("startup")
async def on_startup():
    # Устанавливаем вебхук при старте приложения
    await bot.set_webhook(WEBHOOK_FULL_URL)

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    # Эта функция будет вызываться Telegram'ом
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)
    return {"ok": True}

@app.on_event("shutdown")
async def on_shutdown():
    # Удаляем вебхук при остановке
    await bot.delete_webhook()

# --- Логика для WebApp ---
# Добавим API для получения товаров, чтобы не хранить их в JS
@app.get("/api/products")
async def get_products():
    return [
        {"id": 1, "title": "Жидкость 'Лесные ягоды'", "price": 500},
        {"id": 2, "title": "Жидкость 'Холодный манго'", "price": 550},
    ]

# Отдаем статику (наш WebApp)
# Vercel сделает это сам, если файлы в папке public,
# но этот эндпоинт для FastAPI на случай, если что-то пойдет не так с роутингом.
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="public", html=True), name="static")
