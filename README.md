# Phone Shop Bot

Telegram bot and backend for a phone shop, built with FastAPI and PostgreSQL.

## Setup

Copy `.env.example` to `.env` and configure the required environment variables.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For Docker:

```bash
docker compose up --build
```
