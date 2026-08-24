from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    customer_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_username: Mapped[str | None] = mapped_column(String(60))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    preferred_color: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / contacted / closed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
