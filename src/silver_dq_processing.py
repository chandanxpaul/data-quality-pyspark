"""Apply data-quality rules and promote Bronze data into Silver"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    coalesce,
    col,
    concat_ws,
    count,
    current_date,
    current_timestamp,
    greatest,
    lit,
    sum,
    when,
)

from src.config import bronze_path, dq_metrics_path, quarantine_path, silver_path, spark


RULE_TRANSACTION_ID = "transaction_id_not_null"
RULE_TRANSACTION_AMOUNT = "transaction_amount_positive"
RULE_TRANSACTION_DATE = "transaction_date_not_future"
RULE_DUPLICATES = "duplicate_rows_removed"


def _rule_conditions(transactions: DataFrame) -> dict[str, object]:
    """Build the named DQ conditions used for filtering and metrics."""
    return {
        RULE_TRANSACTION_ID: col("transaction_id").isNull(),
        RULE_TRANSACTION_AMOUNT: (
            col("transaction_amount").isNull()
            | (col("transaction_amount") <= 0)
        ),
        RULE_TRANSACTION_DATE: (
            col("transaction_date").isNotNull()
            & (col("transaction_date") > current_date())
        ),
    }


def apply_dq_rules(transactions: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Return deduplicated clean rows and rows failing the validation rules."""
    conditions = _rule_conditions(transactions)
    invalid_condition = next(iter(conditions.values()))
    for condition in list(conditions.values())[1:]:
        invalid_condition = invalid_condition | condition

    failure_reason = concat_ws(
        "; ",
        *[
            when(condition, lit(rule_name))
            for rule_name, condition in conditions.items()
        ],
    )
    quarantine_transactions = transactions.filter(invalid_condition).withColumn(
        "dq_failure_reason", failure_reason
    )
    clean_transactions = transactions.filter(~invalid_condition).dropDuplicates()

    return clean_transactions, quarantine_transactions


def build_dq_metrics(transactions: DataFrame) -> DataFrame:
    """Count records failing each rule, including duplicate rows removed."""
    conditions = _rule_conditions(transactions)
    metrics = [
        transactions.filter(condition)
        .agg(count("*").cast("long").alias("failed_record_count"))
        .select(lit(rule_name).alias("rule_name"), "failed_record_count")
        for rule_name, condition in conditions.items()
    ]

    duplicate_groups = transactions.groupBy(*transactions.columns).agg(
        count("*").alias("_row_count")
    )
    duplicate_count = duplicate_groups.agg(
        coalesce(
            sum(greatest(col("_row_count") - lit(1), lit(0))),
            lit(0),
        )
        .cast("long")
        .alias("failed_record_count")
    ).select(lit(RULE_DUPLICATES).alias("rule_name"), "failed_record_count")
    metrics.append(duplicate_count)

    result = metrics[0]
    for metric in metrics[1:]:
        result = result.unionByName(metric)
    return result


def process_silver() -> tuple[DataFrame, DataFrame, DataFrame]:
    """Quarantine invalid rows and overwrite the Silver Delta output."""
    bronze_transactions = spark.read.format("delta").load(bronze_path)
    clean_transactions, quarantine_transactions = apply_dq_rules(bronze_transactions)
    dq_metrics = build_dq_metrics(bronze_transactions).withColumn(
        "_dq_logged_ts", current_timestamp()
    )

    (
        quarantine_transactions.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(quarantine_path)
    )
    dq_metrics.write.format("delta").mode("overwrite").save(dq_metrics_path)

    silver_transactions = clean_transactions.withColumn(
        "_silver_processed_ts", current_timestamp()
    )
    silver_transactions.write.format("delta").mode("overwrite").save(silver_path)

    return silver_transactions, quarantine_transactions, dq_metrics


if __name__ == "__main__":
    silver, quarantine, metrics = process_silver()
    duplicate_rows_removed = (
        metrics.filter(col("rule_name") == RULE_DUPLICATES)
        .select("failed_record_count")
        .first()["failed_record_count"]
    )
    print(
        f"Wrote {silver.count():,} clean rows to {silver_path}, "
        f"{quarantine.count():,} quarantined rows to {quarantine_path}, "
        f"and removed {duplicate_rows_removed:,} duplicate rows"
    )
