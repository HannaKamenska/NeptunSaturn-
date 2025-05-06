import logging
import os
import json
import threading
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from astro_calc import process_user_data
from ai_interpreter import generate_transit_message
from server import app  # импортируем Flask-приложение

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run():
    app.run(host="0.0.0.0", port=8080)

    # Запускаем Flask-сервер в отдельном потоке
    threading.Thread(target=run).start()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Я астробот.\n"
        "Отправь мне дату, время и город рождения в формате:\n\n"
        "<b>ДД.ММ.ГГГГ ЧЧ:ММ Город</b>\n\n"
        "Например: <i>15.08.1990 14:30 Женева</i>",
        parse_mode="HTML"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text
        user_id = update.message.from_user.id

        # 👇 Разбиваем текст на дату, время и город
        date_str, time_str, city = text.split(" ", 2)

        # 👇 Вызываем функцию с пятью аргументами
        username = update.message.from_user.username or update.message.from_user.full_name
        chart_path = process_user_data(
            telegram_id=user_id,
            username=username,
            date_str=date_str,
            time_str=time_str,
            city=city
        )

        await update.message.reply_text("✅ Данные сохранены! Натальная карта рассчитана.\nНажми на кнопку ниже, чтобы получить рекомендации:")

        keyboard = [[InlineKeyboardButton("🔮 Получить рекомендации", callback_data="get_recommendations")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👇 Нажми кнопку ниже, чтобы продолжить:", reply_markup=reply_markup)

    except ValueError as e:
        logging.error(f"❌ Ошибка обработки сообщения: {e}")
        await update.message.reply_text("⚠️ Убедись, что ты ввёл данные в правильном формате: ДД.ММ.ГГГГ ЧЧ:ММ Город")
    except Exception as e:
        logging.error(f"❌ Ошибка обработки сообщения: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")
        

async def handle_transit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = update.effective_chat.id
    chart_path = f"data/astro_user_{user_id}.json"

    try:
        # Сообщаем, что данные обрабатываются
        await query.message.reply_text("⏳ Подожди немного, я готовлю рекомендации на основе твоей натальной карты...")
        
        # Анимация "печатает..."
        await context.bot.send_chat_action(chat_id=chat_id, action="typing") 

        with open(chart_path, "r", encoding="utf-8") as f:
            chart = json.load(f)

        saturn = chart["planets"]["Сатурн"]
        mars = chart["planets"]["Марс"]
        jupiter = chart["planets"]["Юпитер"]
        aspects = chart["aspects"]

        logger.info(f"📌 Данные для анализа: Сатурн={saturn}, Марс={mars}, Юпитер={jupiter}, Аспекты={len(aspects)} шт.")

        message = generate_transit_message(
        neptune=chart["planets"]["Нептун"],
        saturn=saturn,
        mars=mars,
        jupiter=jupiter,
        aspects=aspects
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "❓ <b>Остались вопросы?</b>\n"
                "🔹 Напиши сообщение в Telegram-канал: <a href='https://t.me/lifeinastro'>@lifeinastro</a>\n"
                "🤖 Или задай вопрос нашему помощнику: <a href='https://t.me/lifeinastro_bot'>@lifeinastro_bot</a>"
            ),
            parse_mode="HTML",
            disable_web_page_preview=True
        )


    except Exception as e:
        logger.error("Ошибка анализа транзита: %s", e)
        await query.message.reply_text(f"❌ Ошибка анализа транзита: {e}")


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_transit))

    app.run_polling()


if __name__ == "__main__":
    main()
