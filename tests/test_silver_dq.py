from datetime import date, timedelta
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
from src.silver_dq_processing import (
    RULE_DUPLICATES,
    RULE_TRANSACTION_AMOUNT,
    RULE_TRANSACTION_DATE,
    RULE_TRANSACTION_ID,
    apply_dq_rules,
    build_dq_metrics,
)


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
QUARANTINE_SCHEMA = StructType(
    TRANSACTION_SCHEMA.fields
    + [StructField("dq_failure_reason", StringType(), nullable=False)]
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
    expected_quarantine = spark.createDataFrame(
        [
            (*input_rows[1], "transaction_id_not_null"),
            (*input_rows[2], "transaction_amount_positive"),
        ],
        QUARANTINE_SCHEMA,
    )

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


def test_silver_dq_quarantines_future_dates():
    future_row = (
        "TXN-FUTURE",
        "CUST-004",
        "Beauty",
        Decimal("50.00"),
        date.today() + timedelta(days=1),
        "Card",
    )
    transactions = spark.createDataFrame([future_row], TRANSACTION_SCHEMA)

    clean_rows, quarantine_rows = apply_dq_rules(transactions)

    assert clean_rows.count() == 0
    assert quarantine_rows.select("dq_failure_reason").first()[0] == (
        "transaction_date_not_future"
    )


def test_silver_dq_logs_counts_for_each_rule():
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

    actual = build_dq_metrics(transactions)
    expected = spark.createDataFrame(
        [
            (RULE_TRANSACTION_ID, 1),
            (RULE_TRANSACTION_AMOUNT, 1),
            (RULE_TRANSACTION_DATE, 0),
            (RULE_DUPLICATES, 1),
        ],
        ["rule_name", "failed_record_count"],
    )

    assert_df_equality(actual, expected, ignore_nullable=True, ignore_row_order=True)
