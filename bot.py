import os
import random
from datetime import date
from decimal import Decimal

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from database import get_session
from controllers import CurrencyController
from logger import setup_logger

# --- Setup ---

load_dotenv()
logger = setup_logger(__name__, level="WARNING")

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

ALLOWED_USERS = [int(id) for id in os.getenv("ALLOWED_USERS", "").split(",") if id]
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID"))
rate_messages = {}

# --- Utils ---

def is_allowed_user(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

# --- Task: send requests ---

async def request_currency_inputs():
    """Send messages requesting currency rates"""
    try:
        ust_msg = await bot.send_message(TARGET_GROUP_ID, "Введите курс UST/RUB на сегодня")
        cny_msg = await bot.send_message(TARGET_GROUP_ID, "Введите курс CNY/RUB на сегодня")

        rate_messages["ust"] = ust_msg.message_id
        rate_messages["cny"] = cny_msg.message_id

        logger.info("📩 Сообщения для ввода курса отправлены в группу")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке сообщений в Telegram: {e}")

# --- Message handler ---

@dp.message()
async def handle_message(message: Message):
    logger.info(f"📩 Получено сообщение от user_id={message.from_user.id}: {message.text}")

    if not message.reply_to_message:
        logger.info("↩️ Нет reply_to_message — сообщение пропущено")
        return

    logger.info(f"🔁 Reply to message_id={message.reply_to_message.message_id}")
    logger.info(f"🧠 В памяти: UST={rate_messages.get('ust')}, CNY={rate_messages.get('cny')}")

    if message.reply_to_message.message_id not in rate_messages.values():
        logger.info("❌ reply_to_message.message_id не совпадает с ожидаемыми ID")
        return

    if not is_allowed_user(message.from_user.id):
        await message.reply(random.choice([
            "Курсы может отправить только Макс 💼",
            "Я вообще-то у Максима спросил 🤔",
            "Жду ответ только от Максима, как всегда 😏",
            "Максим, ты где? Опять перепоручил?",
            "Это в компетенции только Макса 👔",
            "Курсы — это серьёзно. Максим, выведите ситуацию!"
        ]))
        logger.warning(f"⛔️ Неавторизованный пользователь {message.from_user.id} попытался ввести курс")
        return

    try:
        rate = Decimal(message.text.replace(",", "."))
    except Exception:
        logger.warning(f"❗ Не удалось распарсить число: {message.text}")
        await message.reply("Пожалуйста, введите корректное число")
        return

    async with get_session() as session:
        controller = CurrencyController(session)

        if message.reply_to_message.message_id == rate_messages.get("ust"):
            rate_messages["ust_value"] = float(rate)
            logger.info(f"💾 Получен курс UST: {rate}")
        elif message.reply_to_message.message_id == rate_messages.get("cny"):
            rate_messages["cny_value"] = float(rate)
            logger.info(f"💾 Получен курс CNY: {rate}")

        # Мемный ответ, если только один курс введён
        if (
            ("ust_value" in rate_messages and "cny_value" not in rate_messages) or
            ("cny_value" in rate_messages and "ust_value" not in rate_messages)
        ):
            await message.reply(random.choice([
                "Отлично! Осталось ввести второй курс 💹",
                "Жду второй курс... не тяни как Минфин с бюджетом 🕰️",
                "Курс один — не курс. Максим, добавь ещё цифру 📊",
                "Хорошее начало. А теперь второй курс, и будет вам экономика 😎",
                "Половину дела сделал — теперь доделай 💼"
            ]))

        # Если оба курса введены — сохраняем
        if "ust_value" in rate_messages and "cny_value" in rate_messages:
            try:
                existing = await controller.get_rates_by_date(date.today())
                if existing:
                    await message.reply(random.choice([
                        "Курсы на сегодня уже в базе 📚",
                        "Уже всё записано — вы опоздали на совещание 😅",
                        "Дважды одну и ту же экономику не спасают 💰",
                        "Сегодняшние курсы уже были занесены ✍️"
                    ]))
                    logger.warning("⚠️ Попытка повторной записи на ту же дату")
                    return

                await controller.add_rates(
                    ust=rate_messages["ust_value"],
                    cny=rate_messages["cny_value"],
                    date=date.today()
                )

                await message.reply(random.choice([
                    f"Курсы на {date.today()} успешно записаны 📈",
                    f"Максим передал — зафиксировали ✅",
                    f"По курсам всё чётко, как всегда 👍",
                    f"Готово. Экономика может спать спокойно 😎",
                    f"Сохранил. Центробанк может отдыхать 🏦",
                    f"Спасибо, Максим. Всё под контролем 📊"
                ]))

                logger.info("✅ Курсы сохранены в БД. Очистка состояния.")
                rate_messages.clear()
            except Exception as e:
                logger.error(f"❌ Ошибка при сохранении курсов: {e}")
                await message.reply("Произошла ошибка при сохранении курсов")

# --- Main loop ---

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        request_currency_inputs,
        CronTrigger(hour=16, minute=26, timezone="Europe/Moscow")
    )
    scheduler.start()

    logger.info("🚀 Бот запущен и слушает обновления...")
    await dp.start_polling(bot)

# --- Entry ---

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
