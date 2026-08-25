from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def create_product(db: AsyncSession, **fields) -> Product:
    product = Product(**fields)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def list_products_by_category(db: AsyncSession, category: str) -> list[Product]:
    result = await db.execute(
        select(Product).where(Product.category == category).order_by(Product.is_featured.desc(), Product.id.desc())
    )
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def set_stock(db: AsyncSession, product_id: int, stock_qty: int) -> Product | None:
    product = await get_product(db, product_id)
    if product:
        product.stock_qty = stock_qty
        await db.commit()
        await db.refresh(product)
    return product
