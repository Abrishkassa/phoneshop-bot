# Phone Shop Bot

A Telegram bot + Mini App for a phone shop, letting customers browse phones, laptops, earphones, and accessories, check real prices/specs/photos, and request delivery — without calling the shop for every question. The owner manages the whole catalog from inside Telegram.

## Problem

Phone shop owners spend a large chunk of their day answering the same phone calls: "Do you have this model?", "What colors?", "How much?". This project moves that entire browsing experience into a proper in-app shopping experience inside Telegram, so customers only call to finalize delivery and payment.

## Architecture

- **Customer-facing UI**: a [Telegram Mini App](https://core.telegram.org/bots/webapps) — a real web app (HTML/CSS/JS) that opens inside Telegram, not a chat-based bot flow. Product grid, category tabs, price/brand filters, search, a swipeable multi-photo product detail view, and side-by-side compare.
- **Backend API**: FastAPI, serving both the Mini App's static files and a small REST API (`/api/products`, `/api/brands`, `/api/inquiries`) that the Mini App calls.
- **Database**: PostgreSQL, hosted on [Supabase](https://supabase.com), accessed via the **Session pooler** connection (not the Transaction pooler — see Troubleshooting below for why).
- **File storage**: Supabase Storage, for product photos.
- **Owner-facing UI**: stays as Telegram bot commands (`/addproduct`, `/myproducts`, etc.) — simpler and faster for day-to-day catalog management than a separate admin panel.
- **Deployment**: the API + Mini App run on [Railway](https://railway.app) (Docker-based). The bot itself runs in polling mode, wherever you choose to run it (currently local, can be moved to a small always-on host later).

## Features

**Customers, via the Mini App:**
- Browse by category (Phones, Laptops, Earphones, Accessories)
- Filter by price range and brand, or search by name/brand
- View full product detail: multiple swipeable photos, specs (RAM/storage/processor/battery, or type/battery life for earphones), colors, stock status
- Compare two products side by side
- Request delivery — gets an instant confirmation with a reference code, and the owner is notified immediately

**Owner, via Telegram bot commands:**
- `/addproduct` — guided flow: name → category → brand → price → colors → stock → specs (branches by category) → up to 5 photos → a review screen with Confirm/Back/Cancel before anything saves. Type `back` at any step to correct a mistake without starting over.
- `/myproducts` — list everything in the catalog
- `/setstock <id> <qty>` / `/setprice <id> <price>` — quick updates
- `/addphoto <id>` — add more photos to an existing product (accepts several in a row)
- `/editspecs <id>` — update brand/specs on an existing product
- **Automatic stock updates**: every delivery request notification includes a "✅ Mark as Sold" button — tapping it decrements stock and closes the request, no manual bookkeeping needed
- A persistent "/" command menu in Telegram, so commands don't need to be memorized

## Tech stack

- **FastAPI** + **SQLAlchemy** (async) — backend API
- **PostgreSQL** via **Supabase** — database
- **Supabase Storage** — product photos
- **python-telegram-bot** (v21, async) — bot commands
- **Alembic** — database migrations
- **Docker** + **Railway** — deployment
- **GitHub Actions** — CI (lint with ruff, tests with pytest)
- Vanilla HTML/CSS/JS for the Mini App (no framework) — styled to match Telegram's native theme

## Project structure
app/
core/ # config, database engine, Supabase Storage upload, Telegram notify helper
models/ # SQLAlchemy models (Product, Inquiry)
migrations/ # Alembic migrations
routers/ # FastAPI routes (miniapp.py — the /api/* endpoints)
schemas/ # Pydantic schemas
services/ # DB query/update logic, shared by the bot and the API
bot/ # Telegram bot: owner commands, conversation flows
static/ # The Mini App itself (index.html, style.css, app.js)
tests/ # pytest suite


## Local development

Database is on Supabase — no local Postgres needed.

1. `cp .env.example .env` and fill in:
   - `DATABASE_URL` — Supabase **Session pooler** connection string (Project Settings → Database → Connect → Session pooler, port `5432`)
   - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_OWNER_ID` — from @BotFather and @userinfobot
   - `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` — for photo uploads (Project Settings → API → service_role key)
   - `MINIAPP_URL` — the public HTTPS URL serving the Mini App (your Railway domain)
2. Create a virtual environment (recommended on Windows to avoid permission issues):

python -m venv venv
venv\Scripts\activate # Windows

3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Start the API: `uvicorn app.main:app --reload`
6. In a separate terminal: `python -m app.bot.run` (bot runs in polling mode — no webhook needed for local dev)

## Deployment (Railway)

The API + Mini App are deployed on Railway, building from the repo's `Dockerfile`.

1. New Project → Deploy from GitHub repo
2. Add the same environment variables as your local `.env` in Railway's Variables tab (Settings → Variables → **Deploy** to apply pending changes)
3. Settings → Networking → Generate Domain
4. Set that domain as `MINIAPP_URL` in your local `.env` (the bot needs to know where to send customers)

The bot itself currently runs locally in polling mode — deploying it as a second always-on process is a natural next step.

## Troubleshooting / hard-won lessons

A few non-obvious things that cost real debugging time, documented here so they don't get re-discovered the hard way:

- **Supabase pooler + `DuplicatePreparedStatementError`**: Supabase's **Transaction pooler** (port 6543) does not properly support prepared statements, which SQLAlchemy's asyncpg driver uses by default — causing random `DuplicatePreparedStatementError` crashes. Fix: use the **Session pooler** (port 5432) instead, which fully supports the Postgres wire protocol.
- **Telegram Mini App caching**: Telegram's in-app browser caches Mini App pages and API responses aggressively — updates to `static/` files or product data can appear stale even after redeploying. Fixed with a cache-busting timestamp on the Mini App URL (`?v=<timestamp>`) and `cache: "no-store"` on all `fetch()` calls plus `Cache-Control: no-store` response headers on the API.
- **Telegram user IDs and `INTEGER` overflow**: newer Telegram accounts have user IDs that exceed Postgres's 32-bit `INTEGER` range. The `inquiries.customer_telegram_id` column must be `BIGINT`, not `INTEGER`, or inserts fail for a subset of real users while appearing to work fine in testing (if your own test account happens to have an older, smaller ID).

## Status

🟢 Feature-complete and pilot-tested with real inventory and outside testers, end to end (browse → filter → compare → request delivery → owner notification → mark as sold → automatic stock update).

## Roadmap

- [x] Project scaffold, Docker, CI
- [x] Postgres (Supabase) models + migrations
- [x] Telegram Mini App: browse, filter (price/brand/search), compare, multi-photo carousel
- [x] Owner flows: add product (with specs + multi-photo + review/confirm), edit stock/price/specs, add photos
- [x] Request Delivery → owner notification → Mark as Sold → automatic stock update
- [x] Deployed (Railway + Supabase)
- [x] Pilot tested with real inventory and an outside tester
- [ ] Deploy the bot process itself (currently local-only)
- [ ] Multi-shop / multi-tenant support (currently single pilot shop)