from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401  -- ensures all models are registered before create_all
from app.routers import auth, categories, products, variants, orders, uploads, dashboard, settings as settings_router
from app.services.auth_service import ensure_default_admin

# Creates tables if they don't exist yet. For real schema evolution over time,
# switch to Alembic migrations (scaffolding included in /alembic) instead of
# relying on create_all.
Base.metadata.create_all(bind=engine)

# Bootstraps a default admin from ADMIN_USERNAME/ADMIN_PASSWORD env vars, but
# only if the admins table is currently empty. See ensure_default_admin's
# docstring -- this is a no-op on every run after the first admin exists.
_db = SessionLocal()
try:
    ensure_default_admin(_db)
finally:
    _db.close()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(variants.router)
app.include_router(orders.router)
app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
