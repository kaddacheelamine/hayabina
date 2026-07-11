from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.product_image import ProductImage
from app.schemas.product import ProductImageOut
from app.services import upload_service, product_service

router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload")
def upload_generic_image(file: UploadFile = File(...), _=Depends(get_current_admin)):
    """Generic upload -- saves the file and returns its path only.
    Prefer POST /api/products/{id}/images below when the image belongs
    to a product, since that also persists it to the DB in one step and
    avoids orphaned files."""
    path = upload_service.save_product_image(file)
    return {"path": path}


@router.post(
    "/products/{product_id}/images",
    response_model=list[ProductImageOut],
    status_code=status.HTTP_201_CREATED,
)
def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    product = product_service.get_product_or_404(db, product_id)
    created = []
    for file in files:
        path = upload_service.save_product_image(file)
        image = ProductImage(product_id=product.id, image_path=path)
        db.add(image)
        created.append(image)
    db.commit()
    for image in created:
        db.refresh(image)
    return created


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    image = product_service.get_image_or_404(db, image_id)
    upload_service.delete_product_image_file(image.image_path)
    db.delete(image)
    db.commit()
