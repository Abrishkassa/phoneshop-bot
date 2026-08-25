from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import generate_reference_code
from app.models.inquiry import Inquiry


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
