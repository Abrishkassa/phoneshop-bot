from datetime import datetime

from sqlalchemy import ARRAY, JSON, Boolean, DateTime, Numeric, String, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # phone / earphone / accessory
    brand: Mapped[str | None] = mapped_column(String(60))
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    colors: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    specs: Mapped[dict] = mapped_column(JSON, default=dict)  # e.g. {"ram": "8GB", "storage": "128GB"}
    photo_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[time] = mapped_column(DateTime(timezone=True), server_default=func.now)

    @property
    def display_price(self) -> float:
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def in_stock(self) -> bool:
        return self.stock_qty > 0
