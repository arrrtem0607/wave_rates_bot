from sqlalchemy import Column, Integer, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CurrencyRates(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)

    ust_rub_cents = Column(Integer, nullable=False)         # USD/RUB * 100
    cny_rub_fens = Column(Integer, nullable=False)          # CNY/RUB * 100
    usdt_rub_cents = Column(Integer, nullable=False)        # USDT (USD/CNY) * 100

    # Legacy columns kept for compatibility with older dumps. They duplicate the
    # manually введённые значения и синхронизируются контроллером.
    ust_rub_plus1_cents = Column(Integer, nullable=False)
    cny_rub_plus2p_fens = Column(Integer, nullable=False)
    usdt_rub_plus1_cents = Column(Integer, nullable=False)

