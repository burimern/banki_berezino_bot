from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def get_main_menu(webapp_url: str):
    keyboard = InlineKeyboardMarkup(row_width=1)
    # Важно: URL для WebApp должен быть абсолютным (https://...)
    keyboard.add(
        InlineKeyboardButton(
            text="🔥 Открыть магазин",
            web_app=WebAppInfo(url=webapp_url)
        )
    )
    return keyboard
