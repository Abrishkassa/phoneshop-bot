from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    category: str
    brand: str | None = None
    price: float
    colors: list[str] = []
    stock_qty: int = 0
