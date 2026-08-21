from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ExpenseType


class ExpenseBase(BaseModel):
    name: str = Field(min_length=1, max_length=255, examples=["Internet", "Packaging", "Electricity"])
    value: Decimal = Field(ge=0)
    expense_type: ExpenseType


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    value: Decimal | None = Field(default=None, ge=0)
    expense_type: ExpenseType | None = None


class ExpenseOut(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
