import os
from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


BASE_DIR = Path(__file__).resolve().parent.parent

# Set this before importing src.config in Databricks, for example:
# /Volumes/<catalog>/<schema>/<volume>
DATABRICKS_DATA_DIR_ENV = "/Volumes/workspace/default/test-poc-volume/"
configured_data_dir = os.getenv(DATABRICKS_DATA_DIR_ENV)
IS_DATABRICKS = bool(os.getenv("DATABRICKS_RUNTIME_VERSION")) or bool(
    configured_data_dir
)

if IS_DATABRICKS:
    if not configured_data_dir:
        raise RuntimeError(
            f"Set {DATABRICKS_DATA_DIR_ENV} to a Unity Catalog Volume path "
            "before importing src.config."
        )
    DATA_DIR = Path(configured_data_dir)
else:
    DATA_DIR = BASE_DIR / "data"

bronze_path = str(DATA_DIR / "bronze")
silver_path = str(DATA_DIR / "silver")
gold_path = str(DATA_DIR / "gold")
quarantine_path = str(DATA_DIR / "quarantine")
dq_metrics_path = str(DATA_DIR / "dq_metrics")


active_spark = SparkSession.getActiveSession()
if active_spark is not None:
    # Databricks already provides a configured Spark session and Delta runtime.
    spark = active_spark
else:
    spark_builder = (
        SparkSession.builder.appName("pyspark-databricks-poc")
        .master("local[*]")
        .config(
            "spark.sql.extensions",
            "io.delta.sql.DeltaSparkSessionExtension",
        )
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
    )
    spark = configure_spark_with_delta_pip(spark_builder).getOrCreate()
