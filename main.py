import threading
import asyncio
import time

from server import app as flask_app
from bot import main as telegram_main

# Запускаем Flask-сервер
def run_flask():
    print("🚀 Flask запускается...")
    flask_app.run(host="0.0.0.0", port=8080)

# Запускаем Telegram-бота
def run_telegram():
    print("🤖 Telegram бот запускается...")
    asyncio.run(telegram_main())

if __name__ == "__main__":
    print("💡 Запуск приложения...")
    threading.Thread(target=run_flask).start()
    time.sleep(2)
    run_telegram()
