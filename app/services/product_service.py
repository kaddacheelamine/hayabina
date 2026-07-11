from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.product_image import ProductImage


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = (
        db.query(Product)
        .options(joinedload(Product.variants), joinedload(Product.images), joinedload(Product.category))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def list_products(
    db: Session,
    category_id: int | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Product]:
    query = db.query(Product).options(joinedload(Product.variants), joinedload(Product.images))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


def create_variant(db: Session, product_id: int, color: str, size: str, quantity: int) -> ProductVariant:
    get_product_or_404(db, product_id)
    existing = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product_id,
            ProductVariant.color == color,
            ProductVariant.size == size,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A variant with this color/size already exists for this product",
        )
    variant = ProductVariant(product_id=product_id, color=color, size=size, quantity=quantity)
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def get_variant_or_404(db: Session, variant_id: int) -> ProductVariant:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    return variant


def get_image_or_404(db: Session, image_id: int) -> ProductImage:
    image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image
