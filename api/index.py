# api/index.py
import os
import json
import time
import asyncio
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

# --- Начало конфигурации ---
load_dotenv()

# Переменные для бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL") # URL вашего фронтенда на Vercel
if not BOT_TOKEN or not WEBAPP_URL:
    raise RuntimeError("Переменные BOT_TOKEN и WEBAPP_URL должны быть установлены")

# Переменные для Google Sheets
SHEET_NAME = os.getenv('SHEET_NAME', 'banki_berezino')
ORDERS_SHEET_NAME = "Orders" # Название листа для заказов. Убедитесь, что он существует!

# --- Инициализация ---
app = Flask(__name__, static_folder='../public', static_url_path='') # Указываем путь к public
CORS(app)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

CACHE = {'data': None, 'last_updated': 0}
CACHE_DURATION = 300  # 5 минут

# --- Логика Google Sheets ---
def get_gspread_client():
    creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not creds_json_str:
        raise ValueError("Переменная GOOGLE_CREDENTIALS_JSON не установлена.")
    creds_dict = json.loads(creds_json_str)
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_products_from_sheets():
    # ... (Ваш код получения продуктов остается без изменений) ...
    current_time = time.time()
    if CACHE['data'] and (current_time - CACHE['last_updated'] < CACHE_DURATION):
        return CACHE['data']
    try:
        client = get_gspread_client()
        spreadsheet = client.open(SHEET_NAME)
        products_by_brand = {}
        for sheet in spreadsheet.worksheets():
            if sheet.title == ORDERS_SHEET_NAME: continue # Пропускаем лист с заказами
            brand_name = sheet.title
            rows = sheet.get_all_records()
            products_list = []
            for row_dict in rows:
                row = {key.lower(): value for key, value in row_dict.items()}
                if str(row.get('in_stock')).upper() != 'TRUE': continue
                try: price = int(float(row.get('price', 0)))
                except (ValueError, TypeError): price = 0
                products_list.append({
                    'id': row.get('id', f"{brand_name}_{len(products_list)}"),
                    'name': row.get('name', 'Без названия'), 'price': price
                })
            if products_list: products_by_brand[brand_name] = products_list
        CACHE['data'] = products_by_brand
        CACHE['last_updated'] = time.time()
        return products_by_brand
    except Exception as e:
        print(f"ERROR fetching from Google Sheets: {e}")
        return {"error": "Could not fetch data", "details": str(e)}

def add_order_to_sheet(user_data, order_data):
    """Записывает данные о заказе в Google Таблицу"""
    try:
        client = get_gspread_client()
        spreadsheet = client.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(ORDERS_SHEET_NAME) # Открываем лист "Orders"

        # Формируем строку для записи
        user_id = user_data.get('id')
        username = user_data.get('username', 'N/A')
        first_name = user_data.get('first_name', 'N/A')
        total_price = order_data.get('totalPrice', 0)
        items_json = json.dumps(order_data.get('items', []), ensure_ascii=False)

        new_row = [time.strftime('%Y-%m-%d %H:%M:%S'), user_id, username, first_name, total_price, items_json]
        worksheet.append_row(new_row, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        print(f"ERROR writing order to Google Sheet: {e}")
        return False

# --- Обработчики Aiogram (Логика Бота) ---
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Каталог", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("Добро пожаловать в магазин! 👋\nНажмите кнопку ниже, чтобы открыть каталог.", reply_markup=keyboard)

# Обработчик данных от Web App
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    """Получает данные из WebApp, когда пользователь оформляет заказ"""
    user = message.from_user
    data_str = message.web_app_data.data
    try:
        order_data = json.loads(data_str) # Данные из JS приходят в виде JSON-строки
        
        # Записываем в Google Sheet
        success = add_order_to_sheet(user.model_dump(), order_data)

        if success:
            # Формируем красивое сообщение о заказе
            items_text = "\n".join([f"- {item['name']} ({item['quantity']} шт.)" for item in order_data.get('items', [])])
            total_price = order_data.get('totalPrice', 0)
            
            response_text = (
                f"✅ Ваш заказ принят!\n\n"
                f"<b>Состав заказа:</b>\n{items_text}\n\n"
                f"<b>Итого:</b> {total_price} руб.\n\n"
                f"Мы скоро свяжемся с вами для подтверждения."
            )
            await message.answer(response_text, parse_mode="HTML")
        else:
            await message.answer("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.")

    except Exception as e:
        print(f"ERROR processing WebApp data: {e}")
        await message.answer("Некорректные данные заказа. Попробуйте снова.")

# --- Маршруты Flask (API и Webhook) ---
@app.route('/api/products', methods=['GET'])
def get_products_endpoint():
    data = get_products_from_sheets()
    if "error" in data:
        return jsonify(data), 500
    return jsonify(data)

@app.route('/api/bot', methods=['POST'])
async def webhook_handler():
    """Этот маршрут принимает обновления от Telegram"""
    update_data = request.get_json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return "ok", 200

# Раздача статики (фронтенд)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
