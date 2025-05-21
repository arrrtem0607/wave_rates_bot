from fastapi import FastAPI, Depends, HTTPException
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from controllers import CurrencyController
from pydantic import BaseModel

app = FastAPI(title="Currency Rates API")

class CurrencyRatesResponse(BaseModel):
    date: date
    ust_rub: float
    cny_rub: float
    ust_rub_plus1: float
    cny_rub_plus2p: float

    class Config:
        from_attributes = True

@app.get("/rates/{date_str}", response_model=CurrencyRatesResponse)
async def get_rates(
    date_str: str,
    session: AsyncSession = Depends(get_session)
):
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    controller = CurrencyController(session)
    rates = await controller.get_rates_by_date(target_date)
    
    if not rates:
        raise HTTPException(status_code=404, detail="Rates not found for this date")

    return {
        "date": rates.date,
        "ust_rub": rates.ust_rub_cents / 100,
        "cny_rub": rates.cny_rub_fens / 100,
        "ust_rub_plus1": rates.ust_rub_plus1_cents / 100,
        "cny_rub_plus2p": rates.cny_rub_plus2p_fens / 100
    } 