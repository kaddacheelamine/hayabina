"""
migrate_add_purchase_price.py

Adds the new `purchase_price` column to an EXISTING `products` table. This
is needed because SQLAlchemy's `Base.metadata.create_all()` (used in
app/main.py) only creates tables that don't exist yet -- it does NOT add
new columns to a table that's already there. Without running this, a
database created before this update will be missing this column and every
product read/write will error.

Safe to run multiple times: it checks whether the column already exists
first and only adds it if missing.

Usage (run once, against whichever database you're updating):
    python3 migrate_add_purchase_price.py

On Render: open the Shell tab for your service and run the same command --
it uses the same DATABASE_URL your app already runs with.
"""

from sqlalchemy import inspect, text

from app.database import engine

COLUMN_NAME = "purchase_price"
COLUMN_DEF = "NUMERIC(10, 2)"


def main():
    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("products")}

    if COLUMN_NAME in existing_columns:
        print(f"Skipping '{COLUMN_NAME}' -- already exists.")
        return

    with engine.begin() as conn:
        print(f"Adding column '{COLUMN_NAME}'...")
        conn.execute(text(f"ALTER TABLE products ADD COLUMN {COLUMN_NAME} {COLUMN_DEF}"))
        print("  done.")

    print("Migration complete.")


if __name__ == "__main__":
    main()
