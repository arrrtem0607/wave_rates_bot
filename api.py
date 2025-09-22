from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date, timedelta
from typing import Optional, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_session
from controllers import CurrencyController

app = FastAPI(title="Currency Rates API")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session() as session:
        yield session

class CurrencyRatesResponse(BaseModel):
    date: date
    ust_rub: float
    usdt_rub: float
    cny_rub: float

    class Config:
        from_attributes = True


@app.get("/rates/today", response_model=CurrencyRatesResponse)
async def get_today_rates(session: AsyncSession = Depends(get_db_session)):
    today = date.today()
    controller = CurrencyController(session)
    rates = await controller.get_rates_by_date(today)

    if not rates:
        raise HTTPException(status_code=404, detail="Rates not found for today")

    return {
        "date": rates.date,
        "ust_rub": rates.ust_rub_cents / 100,
        "usdt_rub": rates.usdt_rub_cents / 100,
        "cny_rub": rates.cny_rub_fens / 100,
    }


@app.get("/rates/{date_str}", response_model=CurrencyRatesResponse)
async def get_rates_by_date(
    date_str: str,
    session: AsyncSession = Depends(get_db_session)
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
        "usdt_rub": rates.usdt_rub_cents / 100,
        "cny_rub": rates.cny_rub_fens / 100,
    }


@app.get("/rates", response_model=List[CurrencyRatesResponse])
async def get_rates_range(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db_session)
):
    controller = CurrencyController(session)
    result = await controller.get_rates_range(from_date, to_date)

    return [
        {
            "date": r.date,
            "ust_rub": r.ust_rub_cents / 100,
            "usdt_rub": r.usdt_rub_cents / 100,
            "cny_rub": r.cny_rub_fens / 100,
        }
        for r in result
    ]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: AsyncSession = Depends(get_db_session)):
    today = date.today()
    week_ago = today - timedelta(days=6)
    controller = CurrencyController(session)
    week_rates_models = await controller.get_rates_range(week_ago, today)
    week_rates = [
        {
            "date": r.date,
            "ust_rub": r.ust_rub_cents / 100,
            "usdt_rub": r.usdt_rub_cents / 100,
            "cny_rub": r.cny_rub_fens / 100,
        }
        for r in week_rates_models
    ]

    latest = await controller.get_latest_rate()
    latest_data = None
    if latest:
        latest_data = {
            "date": latest.date,
            "ust_rub": latest.ust_rub_cents / 100,
            "usdt_rub": latest.usdt_rub_cents / 100,
            "cny_rub": latest.cny_rub_fens / 100,
        }

    context = {
        "request": request,
        "default_rates": week_rates,
        "latest_rate": latest_data,
        "from_date": week_ago.isoformat(),
        "to_date": today.isoformat(),
    }
    return templates.TemplateResponse("index.html", context)
