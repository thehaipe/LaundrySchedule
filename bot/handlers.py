import telebot
from datetime import datetime, timedelta
from .database import BookingDatabase
from .keyboards import (
    create_date_keyboard, 
    create_time_slots_keyboard,
    create_user_bookings_keyboard,
    create_main_menu_keyboard
)
from .config import TIME_SLOTS, MAX_DAYS_AHEAD

class BotHandlers:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.db = BookingDatabase()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Налаштовує всі обробники"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            username = message.from_user.username
            if not username:
                self.bot.reply_to(message, 
                    "❌ Для використання бота потрібно встановити username в налаштуваннях Telegram!")
                return
                
            welcome_text = f"Привіт, @{username}! 👋\n\n" \
                          "Це бот для запису на прання в 21 гуртожитку.\n" \
                          "Виберіть дію:\n\n" \
                          "Знайшли помилку? Повідомте @luganskskyyyy\n" \
                          "Підтримати бота можна банкою: https://send.monobank.ua/jar/98JVYjBfM4"
                          

            keyboard = create_main_menu_keyboard()
            self.bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)
            
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            try:
                self.process_callback(call)
            except Exception as e:
                print(f"Error in callback handler: {e}")
                self.bot.answer_callback_query(call.id, "Виникла помилка. Спробуйте ще раз.")
                
    def process_callback(self, call):
        """Обробляє callback запити"""
        data = call.data
        username = call.from_user.username
        
        if not username:
            self.bot.answer_callback_query(call.id, 
                "❌ Встановіть username в налаштуваннях Telegram!")
            return
            
        # Головне меню
        if data == "new_booking":
            self.show_date_selection(call)
            
        elif data == "my_bookings":
            self.show_user_bookings(call, username)
            
        elif data == "refresh":
            # Оновлюємо те ж саме повідомлення замість створення нового
            pass
        elif data == "back_to_main":
            self.show_main_menu(call)
            
        elif data == "back_to_main":
            self.show_main_menu(call)
            
        elif data == "back_to_dates":
            self.show_date_selection(call)
            
        # Вибір дати
        elif data.startswith("date_"):
            date_key = data.replace("date_", "")
            self.show_time_slots(call, date_key)
            
        # Бронювання слоту
        elif data.startswith("book_"):
            parts = data.replace("book_", "").split("_", 1)
            if len(parts) == 2:
                date_key, time_slot = parts
                self.book_slot(call, date_key, time_slot, username)
                
        # Скасування бронювання
        elif data.startswith("cancel_"):
            parts = data.replace("cancel_", "").split("_", 1)
            if len(parts) == 2:
                date_key, time_slot = parts
                self.cancel_booking(call, date_key, time_slot, username)
                
        # Зайнятий слот
        elif data.startswith("occupied_"):
            self.bot.answer_callback_query(call.id, "❌ Цей час вже зайнятий!")
            
    def show_main_menu(self, call):
        """Показує головне меню"""
        welcome_text = f"Привіт, @{call.from_user.username}! 👋\n\n" \
                      "Це бот для запису на прання в 21 гуртожитку.\n" \
                        "Виберіть дію:\n\n" \
                        "Знайшли помилку? Повідомте @luganskskyyyy\n" \
                        "Підтримати бота можна банкою: https://send.monobank.ua/jar/98JVYjBfM4"
                      
        keyboard = create_main_menu_keyboard()
        self.edit_message(call, welcome_text, keyboard)
        
    def show_date_selection(self, call):
        """Показує вибір дат (сьогодні або завтра)"""
        text = "📅 Виберіть дату для запису на прання:"
        keyboard = create_date_keyboard()
        self.edit_message(call, text, keyboard)
        self.bot.answer_callback_query(call.id)
        
    def show_time_slots(self, call, date_key):
        """Показує доступні часові слоти для вибраної дати"""
        try:
            date = datetime.strptime(date_key, '%Y-%m-%d')
        except ValueError:
            self.bot.answer_callback_query(call.id, "❌ Неправильний формат дати!")
            return
            
        # Очищаємо старі записи
        self.db.cleanup_old_bookings()
        
        # Отримуємо розклад на день
        schedule = self.db.get_day_schedule(date, TIME_SLOTS)
        
        # Фільтруємо минулі інтервали для сьогодні
        now = datetime.now()
        available_slots = []
        
        if date.date() == now.date():  # Якщо сьогодні
            for time_slot in TIME_SLOTS:
                start_time_str = time_slot.split('-')[0]
                slot_datetime = datetime.strptime(f"{date_key} {start_time_str}", '%Y-%m-%d %H:%M')
                if slot_datetime > now:  # Тільки майбутні інтервали
                    available_slots.append(time_slot)
        else:  # Якщо завтра - всі інтервали доступні
            available_slots = TIME_SLOTS
            
        # Формуємо текст розкладу
        date_str = date.strftime('%d.%m.%Y')
        day_name = "сьогодні" if date.date() == datetime.now().date() else "завтра"
        text = f"📋 Розклад на {day_name} ({date_str}):\n\n"
        
        for time_slot in available_slots:
            username = schedule.get(time_slot)
            if username:
                text += f"{time_slot} - @{username}\n"
            else:
                text += f"{time_slot} - вільно\n"
                
        if not available_slots:
            text += "На сьогодні вже немає доступних інтервалів.\n"
            text += "Спробуйте записатись на завтра."
        else:
            text += "\n💡 Натисніть на інтервал щоб записатись:"
        
        keyboard = create_time_slots_keyboard(schedule, date_key, available_slots)
        self.edit_message(call, text, keyboard)
        self.bot.answer_callback_query(call.id)
        
    def book_slot(self, call, date_key, time_slot, username):
        """Записує користувача на слот"""
        try:
            date = datetime.strptime(date_key, '%Y-%m-%d')
        except ValueError:
            self.bot.answer_callback_query(call.id, "❌ Неправильний формат дати!")
            return
            
        # Намагаємось записати
        if self.db.book_slot(date, time_slot, username):
            date_str = date.strftime('%d.%m.%Y')
            success_text = f"✅ Успішно записано!\n\n" \
                          f"📅 Дата: {date_str}\n" \
                          f"🕐 Інтервал: {time_slot}\n" \
                          f"👤 Користувач: @{username}\n\n" \
                          f"Щоб скасувати запис, використайте \"Мої записи\"."
                          
            keyboard = create_main_menu_keyboard()
            self.edit_message(call, success_text, keyboard)
            self.bot.answer_callback_query(call.id, "✅ Записано!")
        else:
            self.bot.answer_callback_query(call.id, "❌ Цей час вже зайнятий!")
            # Оновлюємо розклад - потрібно повторити логіку фільтрації
            self.show_time_slots(call, date_key)
            
    def cancel_booking(self, call, date_key, time_slot, username):
        """Скасовує запис користувача"""
        try:
            date = datetime.strptime(date_key, '%Y-%m-%d')
        except ValueError:
            self.bot.answer_callback_query(call.id, "❌ Неправильний формат дати!")
            return
            
        if self.db.cancel_booking(date, time_slot, username):
            date_str = date.strftime('%d.%m.%Y')
            success_text = f"✅ Запис скасовано!\n\n" \
                          f"📅 Дата: {date_str}\n" \
                          f"🕐 Інтервал: {time_slot}\n\n" \
                          f"Інтервал тепер вільний для інших користувачів."
                          
            keyboard = create_main_menu_keyboard()
            self.edit_message(call, success_text, keyboard)
            self.bot.answer_callback_query(call.id, "✅ Скасовано!")
        else:
            self.bot.answer_callback_query(call.id, "❌ Помилка скасування!")
            
    def show_user_bookings(self, call, username):
        """Показує записи користувача"""
        user_bookings = self.db.get_user_bookings(username)
        
        # Фільтруємо тільки майбутні записи
        now = datetime.now()
        future_bookings = []
        
        for booking in user_bookings:
            booking_start_time = booking['time'].split('-')[0]  # Беремо початок інтервалу
            booking_datetime = datetime.strptime(f"{booking['date']} {booking_start_time}", '%Y-%m-%d %H:%M')
            if booking_datetime > now:
                future_bookings.append(booking)
        
        if not future_bookings:
            text = "📋 У вас немає активних записів.\n\n" \
                   "Натисніть \"📅 Записатись на прання\" щоб створити новий запис."
            keyboard = create_main_menu_keyboard()
        else:
            text = f"📋 Ваші записи (@{username}):\n\n"
            for booking in future_bookings:
                date_obj = datetime.strptime(booking['date'], '%Y-%m-%d')
                date_str = date_obj.strftime('%d.%m.%Y')
                day_name = "сьогодні" if date_obj.date() == datetime.now().date() else "завтра"
                text += f"📅 {day_name} ({date_str}) - {booking['time']}\n"
            
            text += "\n💡 Натисніть на запис щоб його скасувати:"
            keyboard = create_user_bookings_keyboard(future_bookings)
            
        self.edit_message(call, text, keyboard)
        self.bot.answer_callback_query(call.id)
        
    def edit_message(self, call, text, keyboard=None):
        """Редагує повідомлення з обробкою помилок"""
        try:
            self.bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        except Exception as e:
            error_msg = str(e)
            # Ігноруємо помилку "message is not modified" - це нормально
            if "message is not modified" not in error_msg:
                print(f"Error editing message: {e}")
                # Якщо не вдається редагувати, відправляємо нове повідомлення
                try:
                    self.bot.send_message(call.message.chat.id, text, reply_markup=keyboard)
                except Exception as e2:
                    print(f"Error sending new message: {e2}")