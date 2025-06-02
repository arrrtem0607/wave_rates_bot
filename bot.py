import os
import asyncio
from datetime import date
from decimal import Decimal
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from database import get_session
from controllers import CurrencyController
from logger import setup_logger

load_dotenv()
logger = setup_logger(__name__, level="INFO")

bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID"))

rate_cache = {"requested": False}

# --- Tasks ---

async def request_currency_inputs():
    try:
        await bot.send_message(TARGET_USER_ID,
            "📥 Введите курс валют (USD и CNY) в две строки, с учётом вашей наценки:\n\n"
            "Пример:\n<code>93.15\n12.85</code>")
        rate_cache["requested"] = True
        logger.info("📩 Запрошены курсы у пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке сообщения: {e}")

async def check_repeat_request():
    if not rate_cache.get("usd") or not rate_cache.get("cny"):
        logger.info("🔁 Повторный запрос курсов в 12:00")
        await request_currency_inputs()

# --- Handlers ---

@dp.message(F.text)
async def handle_currency_message(message: Message):
    if message.from_user.id != TARGET_USER_ID or not rate_cache.get("requested"):
        return

    lines = message.text.strip().splitlines()
    if len(lines) != 2:
        await message.reply("❌ Введите два курса — USD и CNY — в отдельных строках.")
        return

    try:
        # Пользователь вводит с наценкой
        usd_markup = Decimal(lines[0].replace(",", "."))
        cny_markup = Decimal(lines[1].replace(",", "."))

        # Пересчитываем базовые курсы
        usd_base = (usd_markup - Decimal("1.00")).quantize(Decimal("0.0001"))
        cny_base = (cny_markup / Decimal("1.02")).quantize(Decimal("0.0001"))

        # Обновляем кэш
        rate_cache.update({
            "usd": usd_base,
            "cny": cny_base,
            "requested": False
        })

        async with get_session() as session:
            controller = CurrencyController(session)
            await controller.add_rates(
                ust=float(usd_base),
                cny=float(cny_base),
                date=date.today()
            )

        logger.info("💾 Курсы успешно сохранены")

        # Отправляем С ИСХОДНЫМИ ЗНАЧЕНИЯМИ (то есть с наценкой)
        await bot.send_message(
            MANAGER_CHAT_ID,
            f"<b>📊 Курсы на {date.today().strftime('%d.%m.%Y')}:</b>\n\n"
            f"🇺🇸 USD: <b>{usd_markup:.2f}₽</b>\n"
            f"🇨🇳 CNY: <b>{cny_markup:.4f}₽</b>"
        )

        await message.reply("✅ Курсы получены и сохранены.")
    except Exception as e:
        logger.warning(f"Ошибка обработки курсов: {e}")
        await message.reply("❌ Ошибка. Убедитесь, что формат — два числа, каждая на новой строке.")


# --- Entry point ---

async def main():
    scheduler.add_job(request_currency_inputs, CronTrigger(hour=1, minute=9))
    scheduler.add_job(check_repeat_request, CronTrigger(hour=1, minute=10))
    scheduler.start()

    logger.info("🚀 Бот запущен и готов принимать сообщения")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())