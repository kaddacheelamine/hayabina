from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.variant import VariantOut
from app.schemas.category import CategoryOut


class ProductImageOut(BaseModel):
    id: int
    image_path: str

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=0)
    category_id: int | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    category_id: int | None = None


class ProductOut(ProductBase):
    id: int
    stock: int
    is_out_of_stock: bool
    created_at: datetime
    updated_at: datetime
    category: CategoryOut | None = None
    images: list[ProductImageOut] = []
    variants: list[VariantOut] = []

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    """Lighter payload for list views."""

    id: int
    name: str
    price: Decimal
    stock: int
    is_out_of_stock: bool
    category_id: int | None
    thumbnail: str | None = None

    model_config = {"from_attributes": True}
