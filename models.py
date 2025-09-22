from sqlalchemy import Column, Integer, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CurrencyRates(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)

    ust_rub_cents = Column(Integer, nullable=False)         # USD/RUB base * 100
    usdt_rub_cents = Column(Integer, nullable=False)        # USDT/RUB base * 100
    cny_rub_fens = Column(Integer, nullable=False)          # CNY/RUB base * 100

    ust_rub_plus1_cents = Column(Integer, nullable=False)   # (USD + 1) * 100
    usdt_rub_plus1_cents = Column(Integer, nullable=False)  # (USDT + 1) * 100
    cny_rub_plus2p_fens = Column(Integer, nullable=False)   # (CNY * 1.02) * 100

