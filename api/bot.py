import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import gspread

# --- НАСТРОЙКА GOOGLE SHEETS ---
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON', '{}')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME')

try:
    SERVICE_ACCOUNT_INFO = json.loads(GOOGLE_CREDENTIALS_JSON)
except json.JSONDecodeError:
    SERVICE_ACCOUNT_INFO = {}

# Хранилище корзин пользователей
user_carts = {}

def get_spreadsheet():
    """Подключается к Google и возвращает объект всей таблицы."""
    try:
        gc = gspread.service_account_from_dict(SERVICE_ACCOUNT_INFO)
        return gc.open(GOOGLE_SHEET_NAME)
    except Exception as e:
        print(f"Ошибка подключения к Google Sheets: {e}")
        return None

# --- ОБРАБОТЧИКИ КОМАНД И ОСНОВНЫХ КНОПОК ---

def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение при команде /start или возврате в меню."""
    keyboard = [
        [InlineKeyboardButton("📚 Каталог фирм", callback_data='catalog_brands')],
        [InlineKeyboardButton("🛒 Моя корзина", callback_data='cart_view')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = '👋 Добро пожаловать в наш магазин!\n\nВыберите действие:'
    
    query = update.callback_query
    if query:
        query.answer()
        query.edit_message_text(text=message_text, reply_markup=reply_markup)
    else:
        update.message.reply_text(text=message_text, reply_markup=reply_markup)

def show_brands(update: Update, context: CallbackContext) -> None:
    """Показывает список фирм (листов в таблице) как кнопки."""
    query = update.callback_query
    query.answer()
    
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        query.edit_message_text("Не удалось загрузить каталог. Попробуйте позже.")
        return
        
    worksheets = spreadsheet.worksheets()
    keyboard = [[InlineKeyboardButton(sheet.title, callback_data=f"brand:{sheet.title}")] for sheet in worksheets]
    keyboard.append([InlineKeyboardButton("⬅️ Назад в меню", callback_data='start_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("Выберите интересующую фирму:", reply_markup=reply_markup)

def show_products_by_brand(update: Update, context: CallbackContext, brand_name: str) -> None:
    """Показывает товары для выбранной фирмы, фильтруя по полю 'in_stock'."""
    query = update.callback_query
    query.answer()
    
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        query.edit_message_text("Ошибка загрузки товаров.")
        return
        
    try:
        sheet = spreadsheet.worksheet(brand_name)
        all_products = sheet.get_all_records()
        # Фильтруем товары: оставляем только те, у которых in_stock = TRUE
        available_products = [p for p in all_products if p.get('in_stock') == True]
    except gspread.WorksheetNotFound:
        query.edit_message_text("Такая фирма не найдена.")
        return
        
    if not available_products:
        query.edit_message_text("В этой категории пока нет товаров в наличии.")
        return
        
    query.edit_message_text(f"Ассортимент фирмы: <b>{brand_name}</b>", parse_mode='HTML')

    # Используем enumerate для получения индекса, который будет служить временным ID
    for idx, product in enumerate(available_products):
        text = (
            f"<b>{product['name']}</b>\n\n"
            f"<b>Цена:</b> {product['price']} ₽"
        )
        # В callback_data передаем индекс товара в отфильтрованном списке
        callback_data = f"cart_add:{brand_name}:{idx}"
        keyboard = [[InlineKeyboardButton("➕ Добавить в корзину", callback_data=callback_data)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.bot.send_message(
            chat_id=query.message.chat_id, text=text,
            reply_markup=reply_markup, parse_mode='HTML'
        )
    
    back_keyboard = [[InlineKeyboardButton("⬅️ К списку фирм", callback_data='catalog_brands')]]
    context.bot.send_message(
        chat_id=query.message.chat_id, text="Чтобы вернуться, нажмите кнопку ниже.",
        reply_markup=InlineKeyboardMarkup(back_keyboard)
    )

def view_cart(update: Update, context: CallbackContext) -> None:
    """Показывает содержимое корзины, восстанавливая данные по индексу."""
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, {})
    
    if not cart:
        keyboard = [[InlineKeyboardButton("⬅️ В каталог", callback_data='catalog_brands')]]
        query.edit_message_text("Ваша корзина пуста.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
        
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        query.edit_message_text("Ошибка при загрузке данных о товарах.")
        return
        
    total_price = 0
    cart_text = "<b>🛒 Ваша корзина:</b>\n\n"
    sheets_data_cache = {}

    for cart_key, quantity in cart.items():
        try:
            brand_name, product_index_str = cart_key.split(':', 1)
            product_index = int(product_index_str)
            
            if brand_name not in sheets_data_cache:
                sheet = spreadsheet.worksheet(brand_name)
                all_products = sheet.get_all_records()
                sheets_data_cache[brand_name] = [p for p in all_products if p.get('in_stock') == True]
            
            available_products = sheets_data_cache[brand_name]
            
            if product_index < len(available_products):
                product = available_products[product_index]
                item_price = int(product['price']) * quantity
                total_price += item_price
                cart_text += f"▪️ {product['name']} ({quantity} шт.) - {item_price} ₽\n"
            else:
                cart_text += f"▪️ <i>Один из товаров стал недоступен</i>\n"

        except (gspread.WorksheetNotFound, ValueError, IndexError):
            cart_text += f"▪️ <i>Ошибка при загрузке одного из товаров</i>\n"
            continue

    cart_text += f"\n<b>Итого: {total_price} ₽</b>"
    
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data='checkout')],
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data='cart_clear')],
        [InlineKeyboardButton("⬅️ В каталог", callback_data='catalog_brands')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=cart_text, reply_markup=reply_markup, parse_mode='HTML')

# --- ГЛАВНЫЙ ОБРАБОТЧИК КНОПОК ---

def button_callback_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает все нажатия на inline-кнопки."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    if data == 'start_menu':
        start(update, context)
    elif data == 'catalog_brands':
        show_brands(update, context)
    elif data.startswith('brand:'):
        brand_name = data.split(':', 1)[1]
        show_products_by_brand(update, context, brand_name)
    elif data.startswith('cart_add:'):
        _, brand_name, product_index = data.split(':', 2)
        cart_key = f"{brand_name}:{product_index}"
        cart = user_carts.get(user_id, {})
        cart[cart_key] = cart.get(cart_key, 0) + 1
        user_carts[user_id] = cart
        query.answer(text="✅ Добавлено в корзину!")
    elif data == 'cart_view':
        view_cart(update, context)
    elif data == 'cart_clear':
        if user_id in user_carts:
            del user_carts[user_id]
        query.answer("Корзина очищена!")
        keyboard = [[InlineKeyboardButton("⬅️ В каталог", callback_data='catalog_brands')]]
        query.edit_message_text("Ваша корзина пуста.", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'checkout':
        query.answer()
        query.edit_message_text("Спасибо за заказ! Для подтверждения с вами свяжется менеджер @username.")
        if user_id in user_carts:
            del user_carts[user_id]
