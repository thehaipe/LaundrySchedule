import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class BookingDatabase:
    def __init__(self, db_file='data/bookings.json'):
        self.db_file = db_file
        self.ensure_data_dir()
        self.bookings = self.load_bookings()
        
    def ensure_data_dir(self):
        """Створює папку data якщо її немає"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
    def load_bookings(self) -> Dict:
        """Завантажує записи з файлу"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def save_bookings(self):
        """Зберігає записи у файл"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.bookings, f, ensure_ascii=False, indent=2)
            
    def get_date_key(self, date: datetime) -> str:
        """Повертає ключ дати у форматі YYYY-MM-DD"""
        return date.strftime('%Y-%m-%d')
        
    def book_slot(self, date: datetime, time_slot: str, username: str) -> bool:
        """
        Записує користувача на слот
        Повертає True якщо запис успішний, False якщо слот зайнятий
        """
        date_key = self.get_date_key(date)
        
        if date_key not in self.bookings:
            self.bookings[date_key] = {}
            
        if time_slot in self.bookings[date_key]:
            return False  # Слот вже зайнятий
            
        self.bookings[date_key][time_slot] = {
            'username': username,
            'booked_at': datetime.now().isoformat()
        }
        self.save_bookings()
        return True
        
    def cancel_booking(self, date: datetime, time_slot: str, username: str) -> bool:
        """
        Скасовує запис користувача
        Повертає True якщо скасування успішне
        """
        date_key = self.get_date_key(date)
        
        if date_key in self.bookings and time_slot in self.bookings[date_key]:
            if self.bookings[date_key][time_slot]['username'] == username:
                del self.bookings[date_key][time_slot]
                
                # Видаляємо пустий день
                if not self.bookings[date_key]:
                    del self.bookings[date_key]
                    
                self.save_bookings()
                return True
        return False
        
    def get_day_schedule(self, date: datetime, time_slots: List[str]) -> Dict:
        """
        Повертає розклад на день
        """
        date_key = self.get_date_key(date)
        day_bookings = self.bookings.get(date_key, {})
        
        schedule = {}
        for slot in time_slots:
            if slot in day_bookings:
                schedule[slot] = day_bookings[slot]['username']
            else:
                schedule[slot] = None
                
        return schedule
        
    def get_user_bookings(self, username: str) -> List[Dict]:
        """
        Повертає всі записи користувача
        """
        user_bookings = []
        
        for date_key, day_bookings in self.bookings.items():
            for time_slot, booking_info in day_bookings.items():
                if booking_info['username'] == username:
                    user_bookings.append({
                        'date': date_key,
                        'time': time_slot,
                        'booked_at': booking_info['booked_at']
                    })
                    
        return user_bookings
        
    def cleanup_old_bookings(self, days_to_keep: int = 1):
        """
        Видаляє старі записи
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_key = self.get_date_key(cutoff_date)
        
        dates_to_remove = []
        for date_key in self.bookings.keys():
            if date_key < cutoff_key:
                dates_to_remove.append(date_key)
                
        for date_key in dates_to_remove:
            del self.bookings[date_key]
            
        if dates_to_remove:
            self.save_bookings()