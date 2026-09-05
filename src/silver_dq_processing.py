"""Apply data-quality rules and promote Bronze data into Silver"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, current_date, current_timestamp

from src.config import bronze_path, quarantine_path, silver_path, spark


def apply_dq_rules(transactions: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Return deduplicated clean rows and rows failing the validation rules."""
    invalid_condition = (
        col("transaction_id").isNull()
        | col("transaction_amount").isNull()
        | (col("transaction_amount") <= 0)
        | (
            col("transaction_date").isNotNull()
            & (col("transaction_date") > current_date())
        )
    )

    quarantine_transactions = transactions.filter(invalid_condition)
    clean_transactions = transactions.filter(~invalid_condition).dropDuplicates()

    return clean_transactions, quarantine_transactions


def process_silver() -> tuple[DataFrame, DataFrame]:
    """Quarantine invalid rows and overwrite the Silver Delta output."""
    bronze_transactions = spark.read.format("delta").load(bronze_path)
    clean_transactions, quarantine_transactions = apply_dq_rules(bronze_transactions)

    quarantine_transactions.write.format("delta").mode("overwrite").save(
        quarantine_path
    )

    silver_transactions = clean_transactions.withColumn(
        "_silver_processed_ts", current_timestamp()
    )
    silver_transactions.write.format("delta").mode("overwrite").save(silver_path)

    return silver_transactions, quarantine_transactions


if __name__ == "__main__":
    silver, quarantine = process_silver()
    print(
        f"Wrote {silver.count():,} clean rows to {silver_path} and "
        f"{quarantine.count():,} quarantined rows to {quarantine_path}"
    )
