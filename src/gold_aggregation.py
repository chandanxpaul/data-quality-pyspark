"""Build reporting aggregates from the Silver and Quarantine Delta layers."""

from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.functions import count, sum

from src.config import gold_path, quarantine_path, silver_path, spark


DAILY_REVENUE_PATH = str(Path(gold_path) / "daily_revenue")
QUARANTINE_METRICS_PATH = str(Path(gold_path) / "quarantine_metrics")


def build_gold_tables() -> tuple[DataFrame, DataFrame]:
    """Create and overwrite the daily revenue and quarantine metric tables."""
    silver_transactions = spark.read.format("delta").load(silver_path)
    quarantine_transactions = spark.read.format("delta").load(quarantine_path)

    daily_revenue = silver_transactions.groupBy("transaction_date").agg(
        sum("transaction_amount").alias("total_revenue"),
        count("transaction_id").alias("transaction_count"),
    )

    quarantine_metrics = quarantine_transactions.groupBy("dq_failure_reason").agg(
        count("*").alias("quarantined_record_count")
    )

    (
        daily_revenue.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(DAILY_REVENUE_PATH)
    )
    (
        quarantine_metrics.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(QUARANTINE_METRICS_PATH)
    )

    return daily_revenue, quarantine_metrics


def run() -> tuple[DataFrame, DataFrame]:
    """Notebook-friendly entry point for Gold aggregation."""
    return build_gold_tables()


if __name__ == "__main__":
    revenue, quarantine = build_gold_tables()
    print(
        f"Wrote {revenue.count():,} daily revenue rows to {DAILY_REVENUE_PATH} and "
        f"{quarantine.count():,} quarantine metric rows to {QUARANTINE_METRICS_PATH}"
    )
