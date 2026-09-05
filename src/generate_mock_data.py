"""Generate deliberately imperfect e-commerce transaction data for local testing."""

from __future__ import annotations

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path


RECORD_COUNT = 2_000
DUPLICATE_COUNT = 100
SEED = 42
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "input" / "mock_transactions.csv"
)


def _random_transaction(rng: random.Random, index: int) -> dict[str, object]:
    """Create one clean transaction row."""
    transaction_date = date(2024, 1, 1) + timedelta(days=rng.randint(0, 730))
    return {
        "transaction_id": f"TXN-{index:05d}-{uuid.UUID(int=rng.getrandbits(128))}",
        "customer_id": f"CUST-{rng.randint(1, 500):04d}",
        "product_category": rng.choice(
            ["Electronics", "Home", "Apparel", "Beauty", "Sports"]
        ),
        "transaction_amount": f"{rng.uniform(5, 1_000):.2f}",
        "transaction_date": transaction_date.isoformat(),
        "payment_method": rng.choice(["Card", "PayPal", "Bank Transfer", "Wallet"]),
    }


def generate_mock_data(output_path: Path = OUTPUT_PATH) -> Path:
    """Generate and save 2,000 transactions with known quality issues."""
    rng = random.Random(SEED)

    # Keep duplicate source rows clean so injected issue counts are exact.
    original_count = RECORD_COUNT - DUPLICATE_COUNT
    rows = [_random_transaction(rng, index) for index in range(original_count)]
    duplicate_sources = rows[:DUPLICATE_COUNT]
    rows.extend(row.copy() for row in duplicate_sources)

    # Use disjoint rows outside the duplicate pairs for the other quality issues.
    clean_indices = list(range(DUPLICATE_COUNT, original_count))
    rng.shuffle(clean_indices)
    null_indices = clean_indices[:100]
    negative_indices = clean_indices[100:300]
    future_indices = clean_indices[300:400]

    for index in null_indices:
        rows[index]["transaction_id"] = ""

    for index in negative_indices:
        amount = float(rows[index]["transaction_amount"])
        rows[index]["transaction_amount"] = f"{-amount:.2f}"

    for index in future_indices:
        future_date = date.today() + timedelta(days=rng.randint(1, 365))
        rows[index]["transaction_date"] = future_date.isoformat()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


if __name__ == "__main__":
    print(f"Generated {RECORD_COUNT:,} transactions at {generate_mock_data()}")
