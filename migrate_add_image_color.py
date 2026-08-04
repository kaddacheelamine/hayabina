"""
migrate_add_image_color.py

Adds the new `color` column to an EXISTING `product_images` table.

Needed because `Base.metadata.create_all()` (used in app/main.py) only
creates tables that don't exist yet -- it won't add a new column to a
table that's already there. The two brand-new tables added alongside this
change (`sections`, `section_categories`, `site_info`) don't need a
migration; create_all() creates those automatically since they didn't
exist before.

Safe to run more than once -- it checks first and skips if already applied.

Usage:
    python3 migrate_add_image_color.py

On Render: run from the Shell tab, once, after deploying the updated code.
"""

from sqlalchemy import inspect, text

from app.database import engine


def main():
    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("product_images")}

    if "color" in existing_columns:
        print("Skipping 'color' -- already exists.")
        return

    with engine.begin() as conn:
        print("Adding column 'color' to product_images...")
        conn.execute(text("ALTER TABLE product_images ADD COLUMN color VARCHAR(64)"))
        print("  done.")

    print("Migration complete.")


if __name__ == "__main__":
    main()
