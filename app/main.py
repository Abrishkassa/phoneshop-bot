from fastapi import FastAPI
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


@app.get("/health")
async def health():
    return {"status": "ok", "shop": settings.shop_name}


# Serves the Mini App frontend (static/index.html + assets) at /app
app.mount("/app", StaticFiles(directory="static", html=True), name="miniapp")
