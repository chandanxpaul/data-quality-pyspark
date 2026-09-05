from pathlib import Path

from pyspark.sql import SparkSession


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

bronze_path = str(DATA_DIR / "bronze")
silver_path = str(DATA_DIR / "silver")
gold_path = str(DATA_DIR / "gold")
quarantine_path = str(DATA_DIR / "quarantine")


spark = (
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
    .getOrCreate()
)
