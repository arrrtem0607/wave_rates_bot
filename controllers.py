from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import CurrencyRates

class CurrencyController:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_rates(self, ust: float, cny: float, date: date) -> CurrencyRates:
        # Convert to smallest units
        ust_cents = int(ust * 100)
        cny_fens = int(cny * 100)
        
        # Calculate additional values
        ust_plus1_cents = int((ust + 1) * 100)
        cny_plus2p_fens = int((cny * 1.02) * 100)

        rates = CurrencyRates(
            date=date,
            ust_rub_cents=ust_cents,
            cny_rub_fens=cny_fens,
            ust_rub_plus1_cents=ust_plus1_cents,
            cny_rub_plus2p_fens=cny_plus2p_fens
        )

        self.session.add(rates)
        await self.session.commit()
        await self.session.refresh(rates)
        return rates

    async def get_rates_by_date(self, date: date) -> CurrencyRates | None:
        query = select(CurrencyRates).where(CurrencyRates.date == date)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() 