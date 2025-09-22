from typing import Optional
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models import CurrencyRates

class CurrencyController:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_rates(
        self,
        usd: Decimal,
        usdt: Decimal,
        cny: Decimal,
        date: date,
    ) -> tuple[CurrencyRates, bool]:
        usd = usd.quantize(Decimal("0.01"))
        usdt = usdt.quantize(Decimal("0.01"))
        cny = cny.quantize(Decimal("0.01"))

        usd_cents = int(usd * 100)
        usdt_cents = int(usdt * 100)
        cny_fens = int(cny * 100)

        existing = await self.get_rates_by_date(date)
        if existing:
            existing.ust_rub_cents = usd_cents
            existing.usdt_rub_cents = usdt_cents
            existing.cny_rub_fens = cny_fens
            existing.ust_rub_plus1_cents = usd_cents
            existing.usdt_rub_plus1_cents = usdt_cents
            existing.cny_rub_plus2p_fens = cny_fens

            await self.session.commit()
            await self.session.refresh(existing)
            return existing, False

        rates = CurrencyRates(
            date=date,
            ust_rub_cents=usd_cents,
            usdt_rub_cents=usdt_cents,
            cny_rub_fens=cny_fens,
            ust_rub_plus1_cents=usd_cents,
            usdt_rub_plus1_cents=usdt_cents,
            cny_rub_plus2p_fens=cny_fens,
        )

        self.session.add(rates)
        await self.session.commit()
        await self.session.refresh(rates)
        return rates, True

    async def get_rates_by_date(self, date: date) -> CurrencyRates | None:
        query = select(CurrencyRates).where(CurrencyRates.date == date)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def has_rates_for_date(self, date: date) -> bool:
        query = select(func.count()).select_from(CurrencyRates).where(CurrencyRates.date == date)
        result = await self.session.execute(query)
        return result.scalar_one() > 0

    async def get_rates_range(self, from_date: Optional[date], to_date: Optional[date]):
        query = select(CurrencyRates)
        if from_date:
            query = query.where(CurrencyRates.date >= from_date)
        if to_date:
            query = query.where(CurrencyRates.date <= to_date)
        query = query.order_by(CurrencyRates.date)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_latest_rate(self) -> CurrencyRates | None:
        query = select(CurrencyRates).order_by(CurrencyRates.date.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
