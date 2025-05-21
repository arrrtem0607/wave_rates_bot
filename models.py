from sqlalchemy import Column, Integer, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CurrencyRates(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)

    ust_rub_cents = Column(Integer, nullable=False)         # UST/RUB * 100
    cny_rub_fens = Column(Integer, nullable=False)          # CNY/RUB * 100

    ust_rub_plus1_cents = Column(Integer, nullable=False)   # (UST+1) * 100
    cny_rub_plus2p_fens = Column(Integer, nullable=False)   # (CNY*1.02) * 100 