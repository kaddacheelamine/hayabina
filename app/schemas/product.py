from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import Season
from app.schemas.variant import VariantOut
from app.schemas.category import CategoryOut


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=0)
    category_id: int | None = None
    material: str | None = Field(default=None, max_length=128, examples=["Cotton", "Wool", "100% Polyester"])
    season: Season | None = None
    discount_percentage: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=1,
        description="Ratio from 0 (no discount) to 1 (100% off), e.g. 0.20 = 20% off.",
    )


class ProductCreate(ProductBase):
    # Cost/purchase price. Kept off ProductBase (and so off the public
    # ProductOut/ProductListOut below) so it's never returned by the public,
    # unauthenticated GET endpoints -- only accepted here on admin-only
    # create/update, and surfaced back via ProductAdminOut.
    purchase_price: Decimal | None = Field(default=None, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    purchase_price: Decimal | None = Field(default=None, ge=0)
    category_id: int | None = None
    material: str | None = Field(default=None, max_length=128)
    season: Season | None = None
    discount_percentage: Decimal | None = Field(default=None, ge=0, le=1)


class ProductOut(ProductBase):
    id: int
    stock: int
    is_out_of_stock: bool
    final_price: Decimal
    colors: list[str] = []
    created_at: datetime
    updated_at: datetime
    category: CategoryOut | None = None
    variants: list[VariantOut] = []

    model_config = {"from_attributes": True}


class ProductAdminOut(ProductOut):
    """Same as ProductOut but also includes cost/profit data. Only used as
    the response_model for admin-protected endpoints (create/update), never
    for the public list/get endpoints."""

    purchase_price: Decimal | None = None
    profit: Decimal | None = None


class ProductListOut(BaseModel):
    """Lighter payload for list views."""

    id: int
    name: str
    price: Decimal
    final_price: Decimal
    discount_percentage: Decimal
    stock: int
    is_out_of_stock: bool
    category_id: int | None
    material: str | None = None
    season: Season | None = None
    colors: list[str] = []
    thumbnail: str | None = None

    model_config = {"from_attributes": True}
