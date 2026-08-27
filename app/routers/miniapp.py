from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.telegram_notify import notify_owner
from app.schemas.miniapp import InquiryCreate, InquiryOut, ProductOut
from app.services.inquiry_service import create_inquiry
from app.services.product_service import (
    get_product,
    list_products_by_category,
    list_products_by_category_and_price,
)

router = APIRouter(prefix="/api", tags=["miniapp"])


@router.get("/products", response_model=list[ProductOut])
async def get_products(
    category: str,
    price_range: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if price_range:
        products = await list_products_by_category_and_price(db, category, price_range)
    else:
        products = await list_products_by_category(db, category)
    return products


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/inquiries", response_model=InquiryOut)
async def submit_inquiry(payload: InquiryCreate, db: AsyncSession = Depends(get_db)):
    product = await get_product(db, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inquiry = await create_inquiry(
        db,
        customer_telegram_id=payload.telegram_id,
        customer_username=payload.telegram_username,
        product_id=payload.product_id,
        preferred_color=payload.preferred_color,
        note=payload.note,
    )

    username_note = f"@{payload.telegram_username}" if payload.telegram_username else f"id {payload.telegram_id}"
    await notify_owner(
        f"🔔 New delivery request (Mini App)\n"
        f"Product: {product.name}\n"
        f"Customer: {username_note}\n"
        f"Color: {payload.preferred_color or 'any'}\n"
        f"Reference: #{inquiry.reference_code}"
    )

    return inquiry
