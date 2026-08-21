from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ExpenseType


class Expense(Base):
    """
    A recurring or fixed store expense (rent, internet, electricity,
    packaging, etc.), kept separate from products/orders so it can be
    used for profit/margin reporting without touching sale data.

    `expense_type` controls how the expense should be applied when
    computing real profit:
      - OVERALL:   subtracted once from total revenue as a whole
                   (e.g. internet, electricity, rent).
      - PER_ORDER: subtracted once for every order placed
                   (e.g. a per-order delivery/handling fee).
      - PER_ITEM:  subtracted for every individual item/unit sold
                   (e.g. packaging material per piece).
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    expense_type: Mapped[ExpenseType] = mapped_column(
        SAEnum(ExpenseType, name="expense_type"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
