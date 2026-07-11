from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.security.hashing import verify_password
from app.security.jwt import create_access_token


def authenticate_admin(db: Session, username: str, password: str) -> Admin | None:
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return None
    return admin


def create_token_for_admin(admin: Admin) -> str:
    return create_access_token(subject=str(admin.id))
