from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=f"{settings.shop_name} Bot API")


@app.get("/health")
async def health():
    return {"status": "ok", "shop": settings.shop_name}
