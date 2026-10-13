from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import miniapp

app = FastAPI(title=f"{settings.shop_name} Bot API")

# The Mini App is served from Telegram's in-app browser, which needs to call
# this API cross-origin. Locked down to * for now since there are no cookies/
# auth headers involved — every request is scoped by the data sent, not by origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(miniapp.router)


@app.middleware("http")
async def miniapp_cache_headers(request: Request, call_next):
    """Keep the Mini App from going stale in Telegram's in-app browser.

    - /app/vendor/* files are versioned by filename (lucide-<ver>.min.js),
      so they can be cached forever.
    - Every other /app asset is served no-store: Telegram caches aggressively,
      and a stale index.html paired with a fresh app.js (or vice versa) can
      break the page on mobile devices.
    """
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/app/vendor/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/app"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "shop": settings.shop_name}


# Serves the Mini App frontend (static/index.html + assets) at /app
app.mount("/app", StaticFiles(directory="static", html=True), name="miniapp")
