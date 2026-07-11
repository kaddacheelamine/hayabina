from pydantic import BaseModel, Field


class VariantBase(BaseModel):
    color: str = Field(min_length=1, max_length=64)
    size: str = Field(min_length=1, max_length=32)
    quantity: int = Field(ge=0)


class VariantCreate(VariantBase):
    pass


class VariantUpdate(BaseModel):
    color: str | None = Field(default=None, min_length=1, max_length=64)
    size: str | None = Field(default=None, min_length=1, max_length=32)
    quantity: int | None = Field(default=None, ge=0)


class VariantOut(VariantBase):
    id: int
    product_id: int
    is_out_of_stock: bool

    model_config = {"from_attributes": True}
