from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # Which color this image represents (e.g. "Red", "Green"). Lets the
    # frontend group a product's images by color and let the customer pick
    # a color by tapping an image, rather than a separate color swatch --
    # the color is visible IN the photo, so no separate selector is needed.
    # Nullable because a product might have generic (non-color-specific)
    # images too. Not a foreign key to ProductVariant on purpose: images
    # and variants are uploaded/created independently and a variant's
    # color+size combinations don't need a 1:1 image per combination --
    # one "Red" image can apply to all Red/S, Red/M, Red/L variants.
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="images")
