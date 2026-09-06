from datetime import date
from decimal import Decimal

from chispa import assert_df_equality
from pyspark.sql.types import (
    DateType,
    DecimalType,
    StringType,
    StructField,
    StructType,
)

from src.config import spark
from src.silver_dq_processing import apply_dq_rules


TRANSACTION_SCHEMA = StructType(
    [
        StructField("transaction_id", StringType(), nullable=True),
        StructField("customer_id", StringType(), nullable=True),
        StructField("product_category", StringType(), nullable=True),
        StructField("transaction_amount", DecimalType(10, 2), nullable=True),
        StructField("transaction_date", DateType(), nullable=True),
        StructField("payment_method", StringType(), nullable=True),
    ]
)


def test_silver_dq_filters_invalid_rows_and_deduplicates():
    valid_row = (
        "TXN-001",
        "CUST-001",
        "Electronics",
        Decimal("125.50"),
        date(2025, 1, 15),
        "Card",
    )
    input_rows = [
        valid_row,
        (None, "CUST-002", "Home", Decimal("75.00"), date(2025, 1, 16), "Wallet"),
        ("TXN-003", "CUST-003", "Sports", Decimal("-10.00"), date(2025, 1, 17), "Card"),
        valid_row,
    ]
    transactions = spark.createDataFrame(input_rows, TRANSACTION_SCHEMA)

    clean_rows, quarantine_rows = apply_dq_rules(transactions)

    expected_clean = spark.createDataFrame([valid_row], TRANSACTION_SCHEMA)
    expected_quarantine = spark.createDataFrame(input_rows[1:3], TRANSACTION_SCHEMA)

    assert_df_equality(
        clean_rows,
        expected_clean,
        ignore_nullable=True,
        ignore_row_order=True,
    )
    assert_df_equality(
        quarantine_rows,
        expected_quarantine,
        ignore_nullable=True,
        ignore_row_order=True,
    )
