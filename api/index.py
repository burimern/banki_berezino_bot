import os
import json
import time
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Flask приложение ---
app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

# --- Настройки кэширования ---
CACHE = {'data': None, 'last_updated': 0}
CACHE_DURATION = 300  # 5 минут

# --- Функция получения данных из Google Sheets ---
def get_products_from_sheets():
    current_time = time.time()
    
    if CACHE['data'] and (current_time - CACHE['last_updated'] < CACHE_DURATION):
        print("INFO: Returning cached data.")
        return CACHE['data']

    print("INFO: Fetching new data from Google Sheets.")
    try:
        creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if not creds_json_str:
            raise ValueError("Environment variable GOOGLE_CREDENTIALS_JSON is not set.")
        
        creds_dict = json.loads(creds_json_str)
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        sheet_name = os.getenv('SHEET_NAME', 'banki_berezino')
        spreadsheet = client.open(sheet_name)
        worksheets = spreadsheet.worksheets()

        products_by_brand = {}

        for sheet in worksheets:
            brand_name = sheet.title
            rows_from_sheet = sheet.get_all_records()
            products_list = []

            for row_dict in rows_from_sheet:
                row = {key.lower(): value for key, value in row_dict.items()}

                if str(row.get('in_stock')).upper() != 'TRUE':
                    continue

                product_id = row.get('id', f"{brand_name.replace(' ', '_')}_{len(products_list)}")

                # Безопасное преобразование цены
                try:
                    price = int(float(row.get('price', 0)))
                except (ValueError, TypeError):
                    price = 0

                products_list.append({
                    'id': product_id,
                    'name': row.get('name', 'Без названия'),
                    'price': price
                })

            if products_list:
                products_by_brand[brand_name] = products_list

        CACHE['data'] = products_by_brand
        CACHE['last_updated'] = current_time
        print("INFO: Cache updated successfully.")

        return products_by_brand

    except Exception as e:
        print(f"ERROR: Failed to fetch data from Google Sheets. Details: {e}")
        if CACHE['data']:
            print("WARNING: Returning stale data from cache due to an error.")
            return CACHE['data']
        return {"error": "Could not fetch data from the source.", "details": str(e)}

# --- API маршруты ---
@app.route('/api/products', methods=['GET'])
def get_products():
    data = get_products_from_sheets()
    if "error" in data:
        return jsonify(data), 500
    return jsonify(data)

# --- Раздача статических файлов ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# --- Запуск приложения локально ---
if __name__ == '__main__':
    app.run(debug=True)

from fastapi.staticfiles import StaticFiles
