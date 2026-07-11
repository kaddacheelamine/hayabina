from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.schemas.variant import VariantUpdate, VariantOut
from app.services import product_service

router = APIRouter(prefix="/api/variants", tags=["variants"])


@router.put("/{variant_id}", response_model=VariantOut)
def update_variant(
    variant_id: int, payload: VariantUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    variant = product_service.get_variant_or_404(db, variant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(variant_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    variant = product_service.get_variant_or_404(db, variant_id)
    db.delete(variant)
    db.commit()
