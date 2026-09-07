from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

bronze_path = str(DATA_DIR / "bronze")
silver_path = str(DATA_DIR / "silver")
gold_path = str(DATA_DIR / "gold")
quarantine_path = str(DATA_DIR / "quarantine")
dq_metrics_path = str(DATA_DIR / "dq_metrics")


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
spark.sparkContext.setLogLevel("ERROR")
