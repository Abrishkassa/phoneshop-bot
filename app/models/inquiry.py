from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    # BigInteger: Telegram user IDs can exceed the 32-bit INTEGER range for
    # newer accounts, which caused inserts to fail with "integer out of
    # range" for some customers while working fine for older/smaller IDs.
    customer_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    customer_username: Mapped[str | None] = mapped_column(String(60))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    preferred_color: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / contacted / closed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())