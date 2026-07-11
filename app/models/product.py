from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    """
    NOTE ON STOCK:
    We intentionally do NOT store a separate `stock` column on Product.
    Total stock is always derived from the sum of its ProductVariant
    quantities, so there is a single source of truth and no risk of the
    product-level and variant-level numbers drifting apart. The `stock`
    property below is what gets serialized in API responses.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    @hybrid_property
    def stock(self) -> int:
        return sum(v.quantity for v in self.variants)

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock <= 0
