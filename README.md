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
