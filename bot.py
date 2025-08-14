import os
import re
import asyncio
from datetime import date
from decimal import Decimal

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

from database import get_session
from controllers import CurrencyController
from logger import setup_logger


load_dotenv()
logger = setup_logger(__name__, level="INFO")

bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


# --- Access control ---


def _parse_ids(env_value: str) -> set[int]:
    ids: set[int] = set()
    for raw in env_value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            ids.add(int(raw))
        except ValueError:
            logger.warning(f"⚠️ Невалидный ID: {raw}")
    return ids


allowed_users = _parse_ids(os.getenv("ALLOWED_USERS", ""))
_target = os.getenv("TARGET_USER_ID")
if _target:
    try:
        allowed_users.add(int(_target))
    except ValueError:
        logger.warning("⚠️ TARGET_USER_ID не число")
if not allowed_users:
    logger.error("❌ Пустой ALLOWED_USERS/TARGET_USER_ID")
    raise SystemExit(1)

logger.info(f"👥 Допущенные пользователи: {sorted(allowed_users)}")

MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID"))


CURRENCY_PROMPT = (
    "📥 Введите курс валют (USD и CNY) в две строки, с учётом вашей наценки:\n\n"
    "Пример:\n<code>93.15\n12.85</code>"
)


# --- Tasks ---


async def request_currency_inputs() -> None:
    for uid in allowed_users:
        try:
            await bot.send_message(uid, CURRENCY_PROMPT)
            logger.info(f"📩 Запрос курсов отправлен пользователю {uid}")
        except Exception as e:
            logger.error(f"❌ Не удалось отправить запрос пользователю {uid}: {e}")


async def check_repeat_request() -> None:
    async with get_session() as session:
        controller = CurrencyController(session)
        rates = await controller.get_rates_by_date(date.today())

    if rates is None:
        logger.info("🔁 Повторный запрос курсов в 12:00")
        await request_currency_inputs()


# --- Helpers ---


def _extract_two_decimals(text: str) -> tuple[Decimal, Decimal] | None:
    matches = re.findall(r"[0-9]+(?:[.,][0-9]+)?", text)
    if len(matches) != 2:
        return None
    return tuple(Decimal(m.replace(",", ".")) for m in matches)


# --- Handlers ---


@dp.message(F.text)
async def handle_currency_message(message: Message) -> None:
    if message.chat.type != ChatType.PRIVATE or message.from_user.id not in allowed_users:
        return

    async with get_session() as session:
        controller = CurrencyController(session)
        if await controller.has_rates_for_date(date.today()):
            logger.info(f"⛔ Повторный ввод от {message.from_user.id}")
            await message.reply("ℹ️ Курсы на сегодня уже зафиксированы.")
            return

        pair = _extract_two_decimals(message.text)
        if pair is None:
            logger.info(f"⚠️ Неверный формат от {message.from_user.id}: {message.text!r}")
            await message.reply("❌ Неверный формат. Введите два курса — например:\n<code>93.15 12.85</code>")
            return

        a, b = pair
        usd_markup, cny_markup = max(a, b), min(a, b)
        usd_base = (usd_markup - Decimal("1.00")).quantize(Decimal("0.0001"))
        cny_base = (cny_markup / Decimal("1.02")).quantize(Decimal("0.0001"))

        try:
            await controller.add_rates(ust=float(usd_base), cny=float(cny_base), date=date.today())
        except IntegrityError:
            await message.reply("ℹ️ Курсы на сегодня уже зафиксированы.")
            return
        except Exception as e:
            logger.warning(f"❌ Ошибка сохранения курсов от {message.from_user.id}: {e}")
            await message.reply("⚠️ Не удалось сохранить курсы.")
            return

        logger.info(f"💾 Курсы сохранены от пользователя {message.from_user.id}")

    author = (message.from_user.username and f"@{message.from_user.username}") or str(message.from_user.id)
    await bot.send_message(
        MANAGER_CHAT_ID,
        (
            f"<b>📊 Курсы на {date.today():%d.%m.%Y} (от {author}):</b>\n\n"
            f"🇺🇸 USD (введено): <b>{usd_markup:.2f}₽</b>\n"
            f"🇨🇳 CNY (введено): <b>{cny_markup:.2f}₽</b>\n\n"
            f"🧮 База:\n"
            f"• USD(base) = {usd_base:.4f}₽\n"
            f"• CNY(base) = {cny_base:.4f}₽"
        ),
    )
    await message.reply("✅ Курсы получены и сохранены. Спасибо!")


# --- Entry point ---


async def main() -> None:
    scheduler.add_job(
        request_currency_inputs,
        CronTrigger(hour=10, minute=0, day_of_week="mon-fri"),
    )
    scheduler.add_job(
        check_repeat_request,
        CronTrigger(hour=12, minute=0, day_of_week="mon-fri"),
    )
    scheduler.start()

    logger.info("🚀 Бот запущен и готов принимать сообщения")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

