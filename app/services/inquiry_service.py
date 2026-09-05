from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import generate_reference_code
from app.models.inquiry import Inquiry
from app.models.product import Product


async def create_inquiry(
    db: AsyncSession,
    *,
    customer_telegram_id: int,
    customer_username: str | None,
    product_id: int,
    preferred_color: str | None = None,
    note: str | None = None,
) -> Inquiry:
    inquiry = Inquiry(
        reference_code=generate_reference_code(),
        customer_telegram_id=customer_telegram_id,
        customer_username=customer_username,
        product_id=product_id,
        preferred_color=preferred_color,
        note=note,
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry


async def mark_contacted(db: AsyncSession, inquiry_id: int) -> Inquiry | None:
    result = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id))
    inquiry = result.scalar_one_or_none()
    if inquiry:
        inquiry.status = "contacted"
        await db.commit()
        await db.refresh(inquiry)
    return inquiry


async def mark_inquiry_sold(db: AsyncSession, inquiry_id: int, quantity: int = 1) -> Inquiry | None:
    """Closes the inquiry and decrements the linked product's stock — used
    when the owner confirms an actual sale happened."""
    result = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id))
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        return None

    product_result = await db.execute(select(Product).where(Product.id == inquiry.product_id))
    product = product_result.scalar_one_or_none()
    if product:
        product.stock_qty = max(0, product.stock_qty - quantity)

    inquiry.status = "closed"
    await db.commit()
    await db.refresh(inquiry)
    return inquiry