from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str | None
    price: float
    discount_price: float | None
    colors: list[str]
    stock_qty: int
    is_featured: bool
    specs: dict
    photo_urls: list[str]

    model_config = {"from_attributes": True}


class InquiryCreate(BaseModel):
    telegram_id: int
    telegram_username: str | None = None
    product_id: int
    preferred_color: str | None = None
    note: str | None = None


class InquiryOut(BaseModel):
    reference_code: str

    model_config = {"from_attributes": True}
