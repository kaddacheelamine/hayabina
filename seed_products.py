"""
seed_products.py

Connects to the Storefront API and creates random test products
(with description, category, color/size variants, and 2-3 generated
placeholder images per product) for demo/testing purposes.

No external image service needed -- images are generated locally with
Pillow (a solid color background + the product name + an angle label),
so this works even with no internet access beyond your own API.

Usage:
    pip install requests pillow
    python3 seed_products.py --api-url https://your-api.onrender.com --username admin --password yourpassword --count 10

Options:
    --api-url        Base URL of the API (default: http://127.0.0.1:8000)
    --username       Admin username (required)
    --password       Admin password (required)
    --count          Number of products to create (default: 10)
    --images-per-product  Fixed image count per product (default: random 2-3)
    --seed           Random seed, for reproducible runs (optional)
"""

import argparse
import io
import random
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

ADJECTIVES = [
    "Comfort", "Classic", "Premium", "Cozy", "Elegant", "Casual",
    "Modern", "Soft", "Luxury", "Essential", "Everyday", "Deluxe",
]
NOUNS = [
    "Pajama Set", "T-Shirt", "Hoodie", "Bathrobe", "Nightgown",
    "Sweatpants", "Slippers", "Cardigan", "Sleep Shirt", "Jogger Set",
]
CATEGORIES = ["Pajamas", "Loungewear", "Outerwear", "Accessories", "Footwear"]
COLORS = ["Black", "White", "Pink", "Navy", "Grey", "Beige", "Red"]
SIZES = ["S", "M", "L", "XL"]
MATERIALS = ["Cotton", "Wool", "Polyester", "Linen", "Cotton Blend", "Fleece", "Silk"]
SEASONS = ["SUMMER", "WINTER", "SPRING", "AUTUMN", "ALL_SEASON"]

DESCRIPTION_TEMPLATES = [
    "Made from breathable, ultra-soft fabric designed for all-day comfort.",
    "A wardrobe staple that pairs easily with anything you own.",
    "Lightweight and durable, perfect for everyday wear or relaxing at home.",
    "Crafted with attention to detail and a focus on lasting comfort.",
    "Soft to the touch with a relaxed fit that moves with you.",
]

IMAGE_BG_COLORS = [
    (230, 200, 200), (200, 220, 235), (215, 230, 200),
    (235, 225, 190), (220, 205, 230), (200, 235, 225),
]

# Each generated image gets one of these labels stamped on it, so multiple
# images for the same product are visibly distinguishable in the UI.
IMAGE_ANGLE_LABELS = ["Front", "Back", "Side", "Detail", "On model"]


def log(msg: str) -> None:
    print(msg, flush=True)


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def login(self, username: str, password: str) -> None:
        resp = self.session.post(
            f"{self.base_url}/api/auth/login",
            data={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        log(f"Logged in as '{username}'.")

    def get_or_create_category(self, name: str) -> int:
        resp = self.session.get(f"{self.base_url}/api/categories")
        resp.raise_for_status()
        for cat in resp.json():
            if cat["name"] == name:
                return cat["id"]

        resp = self.session.post(f"{self.base_url}/api/categories", json={"name": name})
        resp.raise_for_status()
        return resp.json()["id"]

    def create_product(
        self,
        name: str,
        description: str,
        price: float,
        category_id: int,
        material: str,
        season: str,
        discount_percentage: float,
    ) -> int:
        payload = {
            "name": name,
            "description": description,
            "price": price,
            "category_id": category_id,
            "material": material,
            "season": season,
            "discount_percentage": discount_percentage,
        }
        resp = self.session.post(f"{self.base_url}/api/products", json=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def create_variant(self, product_id: int, color: str, size: str, quantity: int) -> None:
        payload = {"color": color, "size": size, "quantity": quantity}
        resp = self.session.post(
            f"{self.base_url}/api/products/{product_id}/variants", json=payload
        )
        resp.raise_for_status()

    def upload_images(self, product_id: int, images: list[tuple[bytes, str]]) -> None:
        """Uploads several images for the same product in a single request.
        `images` is a list of (image_bytes, filename) tuples."""
        files = [
            ("files", (filename, image_bytes, "image/png"))
            for image_bytes, filename in images
        ]
        resp = self.session.post(
            f"{self.base_url}/api/products/{product_id}/images", files=files
        )
        resp.raise_for_status()


def generate_placeholder_image(text: str, label: str) -> bytes:
    """Generates a simple 600x600 PNG: solid random background + product
    name + a small angle label (e.g. 'Front', 'Back') so multiple images
    for the same product are visibly distinct."""
    bg = random.choice(IMAGE_BG_COLORS)
    img = Image.new("RGB", (600, 600), color=bg)
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        label_font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = title_font

    # Wrap product name across a couple of lines if it's long.
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=title_font) > 520:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    total_height = len(lines) * 44
    y = (600 - total_height) // 2 - 20
    for line in lines:
        w = draw.textlength(line, font=title_font)
        draw.text(((600 - w) / 2, y), line, fill=(40, 40, 40), font=title_font)
        y += 44

    # Angle label near the bottom, e.g. "Front" / "Detail".
    label_w = draw.textlength(label, font=label_font)
    draw.text(((600 - label_w) / 2, 520), label, fill=(90, 90, 90), font=label_font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def random_product_name() -> str:
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"


def random_description() -> str:
    return random.choice(DESCRIPTION_TEMPLATES)


def random_price() -> float:
    return round(random.uniform(9.99, 89.99), 2)


def random_discount() -> float:
    """70% of products have no discount; the rest get a random markdown,
    so seeded data actually exercises the discount/final_price behavior."""
    if random.random() < 0.7:
        return 0.0
    return round(random.choice([0.10, 0.15, 0.20, 0.25, 0.30, 0.50]), 2)


def seed(client: ApiClient, count: int, images_per_product: int | None) -> None:
    category_ids = {name: client.get_or_create_category(name) for name in CATEGORIES}
    log(f"Categories ready: {list(category_ids.keys())}")

    for i in range(1, count + 1):
        name = random_product_name()
        description = random_description()
        price = random_price()
        category_name = random.choice(CATEGORIES)
        category_id = category_ids[category_name]
        material = random.choice(MATERIALS)
        season = random.choice(SEASONS)
        discount_percentage = random_discount()

        product_id = client.create_product(
            name, description, price, category_id, material, season, discount_percentage
        )
        discount_note = f", {int(discount_percentage * 100)}% off" if discount_percentage else ""
        log(
            f"[{i}/{count}] Created product #{product_id}: '{name}' "
            f"({category_name}, {material}, {season}, ${price}{discount_note})"
        )

        # 1-3 random color/size variants per product, no duplicates.
        num_variants = random.randint(1, 3)
        used_combos = set()
        for _ in range(num_variants):
            color = random.choice(COLORS)
            size = random.choice(SIZES)
            if (color, size) in used_combos:
                continue
            used_combos.add((color, size))
            quantity = random.randint(0, 20)
            client.create_variant(product_id, color, size, quantity)
            log(f"    variant: {color}/{size} x{quantity}")

        # 2-3 images per product by default (fixed count if --images-per-product given),
        # each with a different angle label, uploaded together in one request.
        num_images = images_per_product if images_per_product else random.randint(2, 3)
        labels = random.sample(IMAGE_ANGLE_LABELS, k=min(num_images, len(IMAGE_ANGLE_LABELS)))
        images = [
            (generate_placeholder_image(name, label), f"product_{product_id}_{j}.png")
            for j, label in enumerate(labels)
        ]
        client.upload_images(product_id, images)
        log(f"    uploaded {len(images)} images: {', '.join(labels)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--images-per-product", type=int, default=None,
                         help="Fixed number of images per product (default: random 2-3)")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    client = ApiClient(args.api_url)
    try:
        client.login(args.username, args.password)
    except requests.HTTPError as exc:
        log(f"Login failed: {exc}")
        sys.exit(1)

    try:
        seed(client, args.count, args.images_per_product)
    except requests.HTTPError as exc:
        log(f"Request failed: {exc}")
        if exc.response is not None:
            log(f"Response body: {exc.response.text}")
        sys.exit(1)

    log(f"\nDone. Created {args.count} products.")


if __name__ == "__main__":
    main()
