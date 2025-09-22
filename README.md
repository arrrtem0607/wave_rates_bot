# Currency Rates Telegram Bot

Telegram bot for manual collection and storage of currency rates with API access.

## Features

- Daily automatic requests for USD/RUB, CNY/RUB and USDT (USD/CNY) values
- Whitelist-based access control
- Reply-based rate collection
- Automatic conversion to smallest units
- FastAPI backend for rate retrieval
- PostgreSQL storage
- Manual values can be updated throughout the day

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   BOT_TOKEN=your_bot_token_here
   TARGET_GROUP_ID=your_group_id_here
   ALLOWED_USERS=78175979,6107771545,253738991
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/currency_rates
   ```

4. Create the database:
   ```sql
   CREATE DATABASE currency_rates;
   ```

5. Run database migrations (using Alembic or your preferred tool)

## Running the Application

1. Start the API server:
   ```bash
   uvicorn api:app --reload
   ```

2. Start the Telegram bot:
   ```bash
   python bot.py
   ```

## Web Interface

Open `http://localhost:8000/` in your browser after starting the API server.
The page is in Russian and immediately shows rates for the last 7 days.
The latest available rate is displayed above the form.
Select another date range and click **Загрузить** to update the table.

## API Usage

### Get Rates by Date

```
GET /rates/{date}
```

Example response:
```json
{
  "date": "2025-05-21",
  "usd_rub": 93.15,
  "cny_rub": 12.85,
  "usdt_usd_cny": 7.25,
  "ust_rub_plus1": 94.15,
  "cny_rub_plus2p": 13.107
}
```

## Bot Usage

1. The bot automatically sends a message at 10:00 MSK on weekdays (Mon-Fri) asking for three values: USD/RUB, CNY/RUB and USDT (USD/CNY)
2. If the rates are still not provided, the bot sends a reminder at 12:00 MSK on weekdays
3. Reply to the message with three numbers on separate lines (USD/RUB, CNY/RUB, USDT (USD/CNY))
4. Only messages from users listed in `ALLOWED_USERS` (and `TARGET_USER_ID` for backward compatibility) sent in a private chat with the bot are processed
5. After the values are collected, they are automatically saved to the database
6. Repeated submissions on the same day overwrite the previous entry

## Security

- Only whitelisted users can reply to rate collection messages
- API can be protected with API key (implementation required)
- All monetary values are stored as integers (cents/fens)
