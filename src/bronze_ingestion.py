"""Ingest raw transaction CSV data into the Bronze Delta layer."""

from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import (
    DateType,
    DecimalType,
    StringType,
    StructField,
    StructType,
)

from src.config import DATA_DIR, bronze_path, spark


INPUT_PATH = Path(DATA_DIR) / "input"

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


def ingest_to_bronze(input_path: str | Path = INPUT_PATH) -> DataFrame:
    """Read transaction CSV files and append them to the Bronze Delta path."""
    transactions = (
        spark.read.schema(TRANSACTION_SCHEMA)
        .option("header", True)
        .option("dateFormat", "yyyy-MM-dd")
        .option("mode", "FAILFAST")
        .csv(str(input_path))
    )

    bronze_transactions = transactions.withColumn(
        "_bronze_insert_ts", current_timestamp()
    )

    bronze_transactions.write.format("delta").mode("append").save(bronze_path)
    return bronze_transactions


if __name__ == "__main__":
    ingested = ingest_to_bronze()
    print(f"Appended {ingested.count():,} rows to {bronze_path}")
