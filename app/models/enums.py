import enum


class DeliveryType(str, enum.Enum):
    HOME = "HOME"
    OFFICE = "OFFICE"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    STAFF = "staff"


class Season(str, enum.Enum):
    SUMMER = "SUMMER"
    WINTER = "WINTER"
    SPRING = "SPRING"
    AUTUMN = "AUTUMN"
    ALL_SEASON = "ALL_SEASON"


class ExpenseType(str, enum.Enum):
    # Deducted from overall revenue as a whole -- doesn't scale with orders
    # or items (e.g. internet bill, electricity, rent).
    OVERALL = "OVERALL"
    # Charged once per order, regardless of how many items are in it
    # (e.g. a delivery/shipping handling fee).
    PER_ORDER = "PER_ORDER"
    # Charged per individual item/unit sold (e.g. packaging material).
    PER_ITEM = "PER_ITEM"
