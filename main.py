#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import telebot
from bot.config import BOT_TOKEN
from bot.handlers import BotHandlers

def main():
    """Головна функція запуску бота"""
    if not BOT_TOKEN:
        print("❌ Помилка: BOT_TOKEN не знайдено в .env файлі!")
        return
    
    # Створюємо бота
    bot = telebot.TeleBot(BOT_TOKEN)
    # Ініціалізуємо обробники
    handlers = BotHandlers(bot)
    
    print("🤖 Бот запущено! Натисніть Ctrl+C для зупинки.")
    
    try:
        # Запускаємо polling
        bot.infinity_polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Бот зупинено користувачем.")
    except Exception as e:
        print(f"❌ Помилка запуску бота: {e}")

if __name__ == "__main__":
    main()