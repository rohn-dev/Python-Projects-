"""Expense domain definitions with category-specific metadata fields."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    choices: tuple[str, ...] | None = None
    required: bool = False


@dataclass(frozen=True)
class CategorySpec:
    key: str
    label: str
    icon: str
    fields: tuple[FieldSpec, ...]
    description: str


PAYMENT_METHODS = ("cash", "debit", "credit", "upi", "bank_transfer", "other")

CATEGORIES: dict[str, CategorySpec] = {
    "food": CategorySpec(
        key="food",
        label="Food & Dining",
        icon="🍽",
        description="Groceries, restaurants, delivery, coffee",
        fields=(
            FieldSpec("subcategory", "Type", ("groceries", "restaurant", "delivery", "coffee", "snacks"), True),
            FieldSpec("vendor", "Vendor / Store"),
        ),
    ),
    "transport": CategorySpec(
        key="transport",
        label="Transportation",
        icon="🚗",
        description="Fuel, transit, rides, parking",
        fields=(
            FieldSpec("mode", "Mode", ("fuel", "public_transit", "ride_share", "taxi", "parking", "maintenance"), True),
            FieldSpec("distance_km", "Distance (km)"),
        ),
    ),
    "housing": CategorySpec(
        key="housing",
        label="Housing",
        icon="🏠",
        description="Rent, mortgage, utilities, repairs",
        fields=(
            FieldSpec("subcategory", "Type", ("rent", "mortgage", "electricity", "water", "gas", "internet", "repairs"), True),
            FieldSpec("provider", "Provider"),
        ),
    ),
    "entertainment": CategorySpec(
        key="entertainment",
        label="Entertainment",
        icon="🎬",
        description="Streaming, games, events, hobbies",
        fields=(
            FieldSpec("subcategory", "Type", ("streaming", "games", "events", "hobbies", "movies"), True),
            FieldSpec("platform", "Platform / Venue"),
        ),
    ),
    "shopping": CategorySpec(
        key="shopping",
        label="Shopping",
        icon="🛍",
        description="Clothing, electronics, home goods",
        fields=(
            FieldSpec("subcategory", "Type", ("clothing", "electronics", "home", "accessories", "gifts"), True),
            FieldSpec("store", "Store"),
        ),
    ),
    "health": CategorySpec(
        key="health",
        label="Health & Wellness",
        icon="💊",
        description="Medical, pharmacy, fitness, insurance",
        fields=(
            FieldSpec("subcategory", "Type", ("doctor", "pharmacy", "gym", "insurance", "therapy", "dental"), True),
            FieldSpec("provider", "Provider"),
        ),
    ),
    "education": CategorySpec(
        key="education",
        label="Education",
        icon="📚",
        description="Tuition, books, courses, certifications",
        fields=(
            FieldSpec("subcategory", "Type", ("tuition", "books", "courses", "certification", "supplies"), True),
            FieldSpec("institution", "Institution"),
        ),
    ),
    "travel": CategorySpec(
        key="travel",
        label="Travel",
        icon="✈",
        description="Flights, hotels, trips",
        fields=(
            FieldSpec("trip", "Trip Name", required=True),
            FieldSpec("destination", "Destination"),
        ),
    ),
    "personal": CategorySpec(
        key="personal",
        label="Personal Care",
        icon="💇",
        description="Salon, grooming, laundry",
        fields=(
            FieldSpec("subcategory", "Type", ("salon", "grooming", "laundry", "spa"), True),
            FieldSpec("vendor", "Vendor"),
        ),
    ),
    "bills": CategorySpec(
        key="bills",
        label="Bills & Subscriptions",
        icon="📱",
        description="Phone, subscriptions, memberships",
        fields=(
            FieldSpec("subcategory", "Type", ("phone", "subscription", "membership", "insurance", "other"), True),
            FieldSpec("service", "Service Name"),
        ),
    ),
    "income": CategorySpec(
        key="income",
        label="Income",
        icon="💰",
        description="Salary, freelance, refunds, investments",
        fields=(
            FieldSpec("source", "Source", ("salary", "freelance", "refund", "investment", "gift", "other"), True),
            FieldSpec("payer", "Payer / Client"),
        ),
    ),
    "other": CategorySpec(
        key="other",
        label="Other",
        icon="📦",
        description="Miscellaneous expenses",
        fields=(
            FieldSpec("reason", "Reason"),
        ),
    ),
}


def category_keys() -> list[str]:
    return list(CATEGORIES.keys())


def get_category(key: str) -> CategorySpec:
    normalized = key.lower().strip()
    if normalized not in CATEGORIES:
        valid = ", ".join(category_keys())
        raise ValueError(f"Unknown category '{key}'. Valid: {valid}")
    return CATEGORIES[normalized]


def resolve_category(query: str) -> CategorySpec:
    normalized = query.lower().strip()
    if normalized in CATEGORIES:
        return CATEGORIES[normalized]
    matches = [c for c in CATEGORIES.values() if normalized in c.label.lower() or normalized in c.key]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(m.key for m in matches)
        raise ValueError(f"Ambiguous category '{query}'. Matches: {names}")
    raise ValueError(f"Unknown category '{query}'")
