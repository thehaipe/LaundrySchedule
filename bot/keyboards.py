from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def create_date_keyboard() -> InlineKeyboardMarkup:
    """
    Створює клавіатуру з датами 
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Сьогодні
    today = datetime.now()
    today_str = today.strftime('%d.%m.%Y')
    today_key = today.strftime('%Y-%m-%d')
    
    # Завтра
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%d.%m.%Y')
    tomorrow_key = tomorrow.strftime('%Y-%m-%d')
    
    keyboard.add(
        InlineKeyboardButton(f"Сьогодні ({today_str})", callback_data=f"date_{today_key}"),
        InlineKeyboardButton(f"Завтра ({tomorrow_str})", callback_data=f"date_{tomorrow_key}")
    )
    
    # Кнопка повернення до головного меню
    keyboard.add(InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main"))
    
    return keyboard

def create_time_slots_keyboard(schedule: Dict[str, str], date_key: str, available_slots: Optional[List[str]] = None) -> InlineKeyboardMarkup:
    """
    Створює клавіатуру з часовими інтервалами (тільки доступні)
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Якщо available_slots не передано, використовує всі слоти зі schedule
    if available_slots is None:
        available_slots = list(schedule.keys())
    
    for time_slot in available_slots:
        username = schedule.get(time_slot)
        if username is None:  # Вільний інтервал
            button_text = f"✅ {time_slot}"
            callback_data = f"book_{date_key}_{time_slot}"
        else:  # Зайнятий інтервал
            button_text = f"❌ {time_slot} - @{username}"
            callback_data = f"occupied_{date_key}_{time_slot}"
            
        keyboard.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Кнопки навігації
    keyboard.add(
        InlineKeyboardButton("◀️ Назад до дат", callback_data="back_to_dates"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="back_to_main")
    )
    
    return keyboard

def create_user_bookings_keyboard(user_bookings: List[Dict]) -> InlineKeyboardMarkup:
    """
    Створює клавіатуру з записами користувача для скасування
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for booking in user_bookings:
        date_obj = datetime.strptime(booking['date'], '%Y-%m-%d')
        date_str = date_obj.strftime('%d.%m.%Y')
        button_text = f"❌ Скасувати {date_str} ({booking['time']})"
        callback_data = f"cancel_{booking['date']}_{booking['time']}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    keyboard.add(InlineKeyboardButton("◀️ Головне меню", callback_data="back_to_main"))
    
    return keyboard

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Створює головне меню
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton("📅 Записатись на прання", callback_data="new_booking"),
        InlineKeyboardButton("📋 Мої записи", callback_data="my_bookings"),
        InlineKeyboardButton("🔄 Оновити", callback_data="refresh")
    )
    
    return keyboard