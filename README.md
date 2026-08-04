# Storefront API (FastAPI)

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # edit SECRET_KEY at minimum
python3 create_admin.py admin yourpassword super_admin

uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Site branding: `/api/store-info`

A dedicated endpoint the frontend calls to get the homepage title,
description, and banner image -- so the storeowner can change these
without a code deploy.

- `GET /api/store-info` -- public. Returns `{title, description, banner_image_path}`.
  Never 404s -- returns nulls if nothing's been set yet.
- `PUT /api/store-info` -- admin only, **multipart form** (not JSON), so
  the banner image can be updated in the same request as the text:
  ```bash
  curl -X PUT $API/api/store-info \
    -H "Authorization: Bearer $TOKEN" \
    -F "title=My Store" \
    -F "description=Best pajamas in town" \
    -F "image=@banner.jpg"
  ```
  Send only the fields you're changing -- omitted fields are left as-is.

`banner_image_path` follows the same convention as product images: it's a
relative path, not a full URL. Build the real URL the same way:
`${API_BASE_URL}/uploads/${banner_image_path}`.

## Homepage sections: `/api/sections`

Lets the store owner create curated homepage blocks (e.g. "Summer
Collection", "New Arrivals"), each with a title and one or more
categories:

- `GET /api/sections` -- public. Returns e.g.:
  ```json
  [{"id": 1, "title": "Summer Collection", "display_order": 1,
    "categories": [{"id": 2, "name": "Pajamas"}, {"id": 5, "name": "Loungewear"}]}]
  ```
- `POST /api/sections` -- admin, `{"title": "...", "category_ids": [2, 5], "display_order": 1}`.
- `PUT /api/sections/{id}` / `DELETE /api/sections/{id}` -- admin.

A section only stores *which categories* it features, not products
directly -- the frontend fetches actual products per category via the
existing `GET /api/products?category_id=...`. This keeps sections
decoupled from product data (adding/removing products from a category
automatically updates what a section shows, with no extra step).

## Picking a product variant by image, not a color swatch

`ProductImage` now has a `color` field. Upload each color's photos
together, tagged with that color:
```bash
curl -X POST $API/api/products/{id}/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@red_front.jpg" -F "files=@red_back.jpg" -F "color=Red"

curl -X POST $API/api/products/{id}/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@green_front.jpg" -F "color=Green"
```

On `GET /api/products/{id}`, `images` now includes each image's `color`,
so the frontend can group them:
```jsx
const imagesByColor = {};
product.images.forEach(img => {
  (imagesByColor[img.color] ??= []).push(img);
});
```

Frontend flow this enables (matches how the store owner described it):
1. Show the images grouped by color -- the customer taps a photo, which
   *is* the color selection. No separate color dropdown/swatch needed,
   since the color is already visible in the photo.
2. Once a color is picked (via its image), filter `product.variants`
   where `variant.color === selectedColor` to get the sizes available
   **in that color specifically** -- sizes are the only thing the
   customer still explicitly chooses.

Note there's no foreign key between `ProductImage.color` and
`ProductVariant.color` -- both are just matching strings. This is
intentional: images and variants are uploaded/created independently
(you might upload a color's photos before deciding all its sizes), and
one "Red" image can apply to every Red/S, Red/M, Red/L variant without
needing a separate image per size.

**If you already have a deployed database from before this change**, run:
```bash
python3 migrate_add_image_color.py
```
(same rules as the other migration script below -- safe to re-run, run
once from Render's Shell tab after deploying).

## Product fields: material, season, discount

Products carry three extra fields beyond the original spec:

- **`material`** -- free text (e.g. "Cotton", "Wool", "100% Polyester").
- **`season`** -- one of `SUMMER`, `WINTER`, `SPRING`, `AUTUMN`, `ALL_SEASON`, or `null`.
- **`discount_percentage`** -- a ratio from `0` (no discount) to `1` (100% off),
  e.g. `0.20` = 20% off. Validated at the API layer (rejects anything outside 0-1).

Every product response also includes a computed **`final_price`**
(`price * (1 - discount_percentage)`, rounded to 2 decimals) -- use this as
the price to actually display, and show `price` crossed out only when
`discount_percentage > 0`.

To turn a discount on/off later, just `PUT` the product with a new
`discount_percentage` -- e.g. `{"discount_percentage": "0.30"}` to start a
30%-off sale, or `{"discount_percentage": "0"}` to end it. No separate
endpoint needed.

**If you already have a deployed database from before this change**, run
the migration once against it (adds the missing columns without touching
existing data):
```bash
python3 migrate_add_product_fields.py
```
On Render: run this from the Shell tab, once, after deploying the updated
code. Safe to run more than once (it skips columns that already exist).
Brand-new databases don't need this -- `create_all` already includes the
new columns.

## Creating the first admin

Two ways, pick whichever fits your setup:

1. **CLI script** (`create_admin.py`) -- run it manually, locally or via
   Render's Shell tab. Good for a one-time setup or adding more admins later.

2. **Auto-bootstrap via env vars** -- set `ADMIN_USERNAME` and
   `ADMIN_PASSWORD` (see `.env.example`) as environment variables (e.g. in
   Render's dashboard). On startup, `main.py` calls
   `auth_service.ensure_default_admin`, which creates that admin **only if
   the admins table is completely empty**. This is meant for platforms with
   an ephemeral filesystem (like Render without a persistent disk), where
   the database gets wiped on every redeploy and you don't want to open a
   shell each time.

   Safe to leave these env vars set permanently: once an admin exists,
   `ensure_default_admin` becomes a no-op on every subsequent startup. It
   will never overwrite an existing admin's password -- change passwords
   through the app itself, not by editing env vars.

## What's here

Matches the architecture doc's structure (`models/`, `schemas/`, `routers/`,
`services/`, `security/`) and all the endpoints it specifies. A few
deliberate deviations from the original spec, based on issues that would
have caused bugs in production:

- **`Product.stock` is computed, not stored.** It's a property that sums
  `ProductVariant.quantity`, so there's one source of truth for inventory
  instead of two numbers that can drift apart.
- **Stock is only touched on status transitions**, centralized in
  `services/order_service.py::update_order_status`. Placing an order
  (`POST /api/orders`) validates availability but doesn't reserve/deduct
  anything. Deduction happens the moment an order moves to `CONFIRMED`.
  If a confirmed (or later) order is then `CANCELLED`, the stock it had
  consumed is automatically restored.
- **Status transitions are restricted** to a defined graph (see
  `_ALLOWED_TRANSITIONS` in `order_service.py`) so you can't, e.g., move a
  `CANCELLED` order back to `CONFIRMED` by mistake.
- **Every status change is logged** to `order_status_history` (order id,
  from/to status, which admin made the change, optional note) — useful
  both for support/audit and for debugging stock discrepancies later.
- **Admin has a `role` field** (`super_admin` / `staff`) even though
  there's only one admin type in the spec — cheap to add now, painful to
  migrate in later once there's real data.
- Image upload has two endpoints, per the spec: a generic
  `POST /api/upload` (returns a path only) and
  `POST /api/products/{id}/images` which saves the file(s) *and* creates
  the `ProductImage` row in one step — safer, since it avoids the
  orphaned-file risk of uploading first and linking separately.

## Known limitations worth knowing about

- **SQLite has no row-level locking.** The availability check in
  `create_order` has a theoretical race window under concurrent orders
  for the last unit of a variant — the real deduction + hard check happens
  at confirmation time in `update_order_status`, which will correctly
  reject over-confirmation, but two PENDING orders can both be created
  for stock that only covers one. Fine for a low-concurrency single-admin
  storefront; if you move to Postgres/MySQL under real load, add
  `SELECT ... FOR UPDATE` in the confirm path.
- **No rate limiting** on the public `POST /api/orders` endpoint. Worth
  adding (e.g. `slowapi`, by IP or phone number) before going live, since
  it's an obvious target for spam.
- **JWT logout is client-side only** (stateless tokens, no server-side
  revocation list). Fine for an admin-only auth system with short-lived
  tokens; add a blocklist table if that ever matters.
- **Schema migrations use `create_all`**, not Alembic, for simplicity.
  Fine while the schema is still moving; switch to real Alembic
  migrations before you have production data you can't just wipe.

## Quick manual test

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -d "username=admin&password=yourpassword" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/api/products -H "Authorization: Bearer $TOKEN"
```
