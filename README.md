# Currency Rates Telegram Bot

Telegram bot for manual collection and storage of currency rates with API access.

## Features

- Daily automatic requests for UST/RUB and CNY/RUB rates
- Whitelist-based access control
- Reply-based rate collection
- Automatic conversion to smallest units
- FastAPI backend for rate retrieval
- PostgreSQL storage
- Ability to overwrite today's rates by sending them again

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
   ALLOWED_USERS=123456789,987654321
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
  "ust_rub": 93.15,
  "cny_rub": 12.85,
  "ust_rub_plus1": 94.15,
  "cny_rub_plus2p": 13.107
}
```

## Bot Usage

1. The bot automatically sends two messages at 09:00 MSK on weekdays (Mon-Fri):
   - "Введите курс UST/RUB на сегодня"
   - "Введите курс CNY/RUB на сегодня"
2. If the rates are still not provided, the bot sends a reminder at 12:00 MSK on weekdays
3. Reply to these messages with the rates
4. Only messages from `TARGET_USER_ID` sent in a private chat with the bot are processed
5. After both rates are collected, they are automatically saved to the database
6. Sending new rates again on the same day overwrites the previous values

## Security

- Only whitelisted users can reply to rate collection messages
- API can be protected with API key (implementation required)
- All monetary values are stored as integers (cents/fens)
