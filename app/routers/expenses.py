from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseOut

# Expenses are internal cost data (not shown to storefront customers), so
# every endpoint here -- including reads -- requires admin auth, unlike
# the public product/category endpoints.
router = APIRouter(
    prefix="/api/expenses", tags=["expenses"], dependencies=[Depends(get_current_admin)]
)


def _get_expense_or_404(db: Session, expense_id: int) -> Expense:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.get("", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).order_by(Expense.expense_type, Expense.name).all()


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    return _get_expense_or_404(db, expense_id)


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    expense = Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)):
    expense = _get_expense_or_404(db, expense_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = _get_expense_or_404(db, expense_id)
    db.delete(expense)
    db.commit()
