from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.variant import ProductVariant


class InsufficientStockError(Exception):
    def __init__(self, variant_id: int, requested: int, available: int):
        self.variant_id = variant_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Variant {variant_id}: requested {requested}, only {available} available"
        )


def get_variant_or_404(db: Session, variant_id: int) -> ProductVariant:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    return variant


def check_availability(db: Session, variant_id: int, quantity: int) -> None:
    """Raise if there isn't enough quantity for this variant.
    Does NOT lock rows -- see note in order_service about concurrency."""
    variant = get_variant_or_404(db, variant_id)
    if variant.quantity < quantity:
        raise InsufficientStockError(variant_id, quantity, variant.quantity)


def deduct_stock(db: Session, variant_id: int, quantity: int) -> ProductVariant:
    """Reduce a variant's quantity. Raises InsufficientStockError if not enough stock.
    Caller is responsible for committing the transaction."""
    variant = get_variant_or_404(db, variant_id)
    if variant.quantity < quantity:
        raise InsufficientStockError(variant_id, quantity, variant.quantity)
    variant.quantity -= quantity
    db.add(variant)
    return variant


def restore_stock(db: Session, variant_id: int, quantity: int) -> ProductVariant:
    """Add quantity back to a variant (used on cancellation after confirmation)."""
    variant = get_variant_or_404(db, variant_id)
    variant.quantity += quantity
    db.add(variant)
    return variant
