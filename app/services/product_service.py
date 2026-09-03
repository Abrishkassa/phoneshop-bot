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


PRICE_RANGES = {
    "under10k": (None, 10000),
    "10to20k": (10000, 20000),
    "over20k": (20000, None),
    "all": (None, None),
}


async def list_products_by_category_and_price(
    db: AsyncSession,
    category: str,
    price_range_key: str,
    brand: str | None = None,
    search: str | None = None,
) -> list[Product]:
    low, high = PRICE_RANGES.get(price_range_key, (None, None))
    stmt = select(Product).where(Product.category == category)
    if low is not None:
        stmt = stmt.where(Product.price >= low)
    if high is not None:
        stmt = stmt.where(Product.price < high)
    if brand:
        stmt = stmt.where(Product.brand == brand)
    if search:
        like = f"%{search}%"
        stmt = stmt.where((Product.name.ilike(like)) | (Product.brand.ilike(like)))
    stmt = stmt.order_by(Product.is_featured.desc(), Product.id.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def list_all_products(db: AsyncSession) -> list[Product]:
    result = await db.execute(select(Product).order_by(Product.category, Product.id))
    return list(result.scalars().all())


async def set_stock(db: AsyncSession, product_id: int, stock_qty: int) -> Product | None:
    product = await get_product(db, product_id)
    if product:
        product.stock_qty = stock_qty
        await db.commit()
        await db.refresh(product)
    return product


async def set_price(db: AsyncSession, product_id: int, price: float) -> Product | None:
    product = await get_product(db, product_id)
    if product:
        product.price = price
        await db.commit()
        await db.refresh(product)
    return product


async def add_photo_url(db: AsyncSession, product_id: int, photo_url: str) -> Product | None:
    product = await get_product(db, product_id)
    if product:
        # Reassign (not .append) so SQLAlchemy detects the ARRAY column changed.
        product.photo_urls = [*(product.photo_urls or []), photo_url]
        await db.commit()
        await db.refresh(product)
    return product


async def set_brand_and_specs(
    db: AsyncSession, product_id: int, brand: str | None, specs: dict
) -> Product | None:
    product = await get_product(db, product_id)
    if product:
        if brand:
            product.brand = brand
        product.specs = {**(product.specs or {}), **specs}
        await db.commit()
        await db.refresh(product)
    return product


async def list_distinct_brands(db: AsyncSession, category: str) -> list[str]:
    result = await db.execute(
        select(Product.brand).where(Product.category == category, Product.brand.is_not(None)).distinct()
    )
    return sorted({b for b in result.scalars().all() if b})