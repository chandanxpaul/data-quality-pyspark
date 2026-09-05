from chispa import assert_df_equality

from src.config import bronze_path, gold_path, quarantine_path, silver_path, spark


def test_path_variables_point_to_data_directory():
    assert bronze_path.endswith("data/bronze")
    assert silver_path.endswith("data/silver")
    assert gold_path.endswith("data/gold")
    assert quarantine_path.endswith("data/quarantine")


def test_spark_session_uses_local_mode():
    assert spark.sparkContext.master == "local[*]"


def test_chispa_dataframe_comparison():
    expected = spark.createDataFrame([(1, "alpha")], ["id", "label"])
    actual = spark.createDataFrame([(1, "alpha")], ["id", "label"])

    assert_df_equality(actual, expected)
