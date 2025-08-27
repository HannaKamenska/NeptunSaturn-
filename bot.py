import logging
import os
import json
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from astro_calc import process_user_data
from ai_interpreter import generate_transit_message
from server import app  # импортируем Flask-приложение


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет!\n"
        "Я — AstroSNai, астробот для быстрого анализа твоей натальной карты.\n\n"
        "🌌 Что ты узнаешь:\n"
        "• Где твоя главная сила и зона роста\n"
        "• Смысл и направление твоего пути\n"
        "• Возможности и риски ближайшего периода\n\n"
        "Чтобы начать, просто отправь свои данные рождения в формате:\n"
        "<b>ДД.ММ.ГГГГ ЧЧ:ММ Город</b>\n\n"
        "📌 Например: <i>15.08.1990 14:30 Женева</i>\n\n"
        "Я на связи — готов построить твою карту ✨",
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
        await update.message.reply_text("⚠️ Убедись, что данные введены в правильном формате: ДД.ММ.ГГГГ ЧЧ:ММ Город")
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
        if not message or not message.strip():
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Не удалось сгенерировать рекомендации. Попробуйте ещё раз или обратитесь к поддержке.",
                parse_mode="HTML"
            )
        else:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "❓ <b>Остались вопросы?</b>\n"
                "🔹 Заполни короткую форму — и я отвечу, как только смогу 👉 <a href='https://forms.gle/YuCsqzEbuYAQ6eba8'>форма</a>\n"
                "🤖 Или задай вопрос нашему помощнику: <a href='https://t.me/lifeinastro_bot'>@lifeinastro_bot</a>"
            ),
            parse_mode="HTML",
            disable_web_page_preview=True
        )


    except Exception as e:
        logger.error("Ошибка анализа транзита: %s", e)
        await query.message.reply_text(f"❌ Ошибка анализа транзита: {e}")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("🛠️ Команда /about получена")

    text1 = (
        "🪐 <b>О чём этот бот и как он может помочь?</b>\n\n"
        "Мы живём в особенное время: сейчас в небе редкое соединение двух планет — <b>Сатурна и Нептуна в знаке Овна.</b> "
        "Это соединение символизирует <b>материализацию мечты, конец старых идеалов и духовное пробуждение через действие.</b>\n\n"
        "🔹 Нептун — вдохновение, мечты, духовные желания\n"
        "🔹 Сатурн — структура и шаги к воплощению\n\n"
        "Но влияние зависит от твоей натальной карты:"
    )

    text2 = (
        "— Положение планет в момент рождения\n"
        "— Их аспекты с другими точками\n\n"
        "✨ Бот анализирует твою карту и показывает:\n"
        "— 💡 Что нужно, чтобы получить возможность желаемого\n"
        "— ⚙️ Как действовать\n"
        "— 🧭 Ради чего всё это\n"
        "— 🔐 Как избежать ошибок\n\n"
        "<b>Это больше, чем прогноз. Это карта осознанного движения к себе.</b>\n\n"
        "<i>Создано с любовью к астрологии и силе внутренней трансформации 💛</i>"
    )

    await update.message.reply_text(text1, parse_mode="HTML")
    await update.message.reply_text(text2, parse_mode="HTML")
    

async def instruction_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧭 <b>Как использовать бота и зачем он вообще нужен?</b>\n\n"
        "✨ В 2025 году начинается редкое и мощное соединение Сатурна и Нептуна в знаке Овна — это важный "
        "астрологический момент, который запускает новый <b>36-летний цикл</b>. Такой шанс бывает нечасто.\n\n"
        "🔹 <b>13 июля 2025</b> — фаза сближения: обе планеты приближаются друг к другу в первых градусах Овна\n"
        "🔹 <b>Февраль 2026</b> — точное соединение в 0°45′ Овна\n"
        "🔹 <i>Весь 2025 год</i> — период подготовки и переосмысления, когда важно заложить правильные ориентиры\n\n"
        "🌌 Это время, когда мечты становятся планом, а туман начинает обретать форму.\n\n"
        "⚙️ <b>Как работает бот:</b>\n"
        "1️⃣ Ты отправляешь дату, время и город своего рождения\n"
        "2️⃣ Бот анализирует твою натальную карту\n"
        "3️⃣ Генерирует персональную стратегию: как, зачем и куда двигаться, чтобы реализовать свою мечту\n\n"
        "💫 <b>Что ты получишь:</b>\n"
        "— Подсказки, как действовать именно тебе в это время\n"
        "— Рекомендации, как сформулировать желания, чтобы они стали реальностью\n"
        "— Опору, когда кажется, что всё туманно\n\n"
        "<b>Какие желания загадывать?</b>\n"
        "🌱 Глубокие, зрелые, душевные — те, что идут изнутри, а не навязаны извне.\n"
        "🚫 Неэффективно сейчас гнаться за быстрыми результатами, статусом или чужими мечтами.\n\n"
        "<b>Как использовать данные от бота:</b>\n"
        "1️⃣ Прочитайте свою стратегию внимательно\n"
        "2️⃣ Запишите желания в тетрадь/дневник/заметки\n"
        "3️⃣ Сформулируйте 1–3 конкретных шага, которые можно сделать уже сейчас\n"
        "4️⃣ Сохраняйте спокойствие — у этого пути свои сроки\n"
        "5️⃣ Возвращайтесь к стратегии — как к карте 💛\n\n"
        "<i>Пусть мечта обретёт форму.</i>",
        parse_mode="HTML"
    )


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("instruction", instruction_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_transit))

    app.run_polling()


if __name__ == "__main__":
    main()
