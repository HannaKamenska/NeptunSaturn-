import threading
from server import app as flask_app
from bot import main as telegram_main

# Запускаем Flask-сервер
def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# Запускаем Telegram-бота
def run_telegram():
    import asyncio
    asyncio.run(telegram_main())

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_telegram()
