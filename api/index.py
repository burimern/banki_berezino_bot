import os
import json
import time
from flask import Flask, jsonify
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Инициализация Flask приложения ---
# Это стандартная часть для запуска веб-сервера на Vercel.
app = Flask(__name__)
# CORS(app) разрешает вашему Web App (который работает на другом домене)
# безопасно запрашивать данные с этого API.
CORS(app)


# --- Настройки кэширования ---
# Чтобы не обращаться к Google Sheets при каждом открытии каталога,
# мы будем хранить данные в памяти 5 минут. Это сильно ускоряет
# работу и экономит лимиты Google API.
CACHE = {
    'data': None,
    'last_updated': 0
}
CACHE_DURATION = 300  # 5 минут в секундах


def get_products_from_sheets():
    """
    Основная функция для получения и обработки данных из Google Sheets.
    Включает в себя логику аутентификации, чтения, форматирования и кэширования.
    """
    current_time = time.time()
    # 1. Проверяем кэш. Если данные свежие (младше 5 минут), отдаем их сразу.
    if CACHE['data'] and (current_time - CACHE['last_updated'] < CACHE_DURATION):
        print("INFO: Returning cached data.")
        return CACHE['data']

    print("INFO: Cache is old. Fetching new data from Google Sheets.")
    try:
        # 2. Аутентификация в Google API.
        # Данные для входа берутся из переменных окружения Vercel,
        # чтобы не хранить секретный ключ в коде.
        creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if not creds_json_str:
            raise ValueError("Environment variable GOOGLE_CREDENTIALS_JSON is not set.")
        
        creds_dict = json.loads(creds_json_str)
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 3. Открываем нужную таблицу по имени.
        # Имя таблицы также берется из переменной окружения.
        sheet_name = os.getenv('SHEET_NAME', 'banki_berezino') # Укажите имя по умолчанию, если нужно
        spreadsheet = client.open(sheet_name)
        
        # 4. Получаем ВСЕ листы (вкладки) из этой таблицы.
        worksheets = spreadsheet.worksheets()
        
        products_by_brand = {}
        
        # 5. Перебираем каждый лист.
        for sheet in worksheets:
            brand_name = sheet.title  # Название листа - это название нашей "папки"-фирмы
            print(f"INFO: Processing sheet: '{brand_name}'")
            
            products_list = []
            # get_all_records() удобно преобразует строки в словари, используя первую строку как ключи.
            rows_from_sheet = sheet.get_all_records()
            
            for row_dict in rows_from_sheet:
                # ВАЖНЫЙ ШАГ: приводим все ключи (названия колонок) к нижнему регистру.
                # Теперь неважно, как вы напишете в таблице: "NAME", "Name" или "name".
                row = {key.lower(): value for key, value in row_dict.items()}

                # 6. Фильтруем товары: показываем только те, что в наличии.
                if str(row.get('in_stock')).upper() != 'TRUE':
                    continue

                # Генерируем ID для каждого товара, если его нет в таблице.
                product_id = row.get('id', f"{brand_name.replace(' ', '_')}_{len(products_list)}")

                # 7. Формируем объект товара и добавляем его в список.
                products_list.append({
                    'id': product_id,
                    'name': row.get('name', 'Без названия'),
                    'price': int(row.get('price', 0)) # Превращаем цену в число
                })
            
            # Добавляем бренд в итоговый словарь, только если у него есть товары в наличии.
            if products_list:
                products_by_brand[brand_name] = products_list
        
        # 8. Обновляем кэш свежими данными.
        CACHE['data'] = products_by_brand
        CACHE['last_updated'] = current_time
        print("INFO: Cache updated successfully.")
        
        return products_by_brand
        
    except Exception as e:
        # В случае любой ошибки выводим ее в лог Vercel.
        print(f"ERROR: Failed to fetch data from Google Sheets. Details: {e}")
        # Если что-то пошло не так, но в кэше есть старые данные, лучше отдать их, чем ничего.
        if CACHE['data']:
            print("WARNING: Returning stale data from cache due to an error.")
            return CACHE['data']
        # Если и кэша нет, возвращаем ошибку.
        return {"error": "Could not fetch data from the source.", "details": str(e)}


# --- API Endpoint ---
# Это "адрес", по которому будет обращаться ваш Web App.
@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Единственный API-маршрут. Вызывает функцию получения данных и возвращает их в формате JSON.
    """
    products_data = get_products_from_sheets()
    
    # Если функция вернула ошибку, отправляем клиенту ответ с кодом 500 (Server Error).
    if "error" in products_data:
        return jsonify(products_data), 500
        
    return jsonify(products_data)

# Если вы запускаете этот файл локально для тестов, этот блок не будет выполняться на Vercel.
if __name__ == '__main__':
    app.run(debug=True)
# Отдаем статику (наш WebApp)
from fastapi.staticfiles import StaticFiles
