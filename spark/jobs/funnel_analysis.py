"""Funnel analysis: view -> cart -> purchase rates per date and category."""
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

SCHEMA = StructType(
    [
        StructField("event_time", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("product_id", LongType(), True),
        StructField("category_id", LongType(), True),
        StructField("category_code", StringType(), True),
        StructField("brand", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("user_id", LongType(), True),
        StructField("user_session", StringType(), True),
    ]
)


def configure_s3a(spark: SparkSession) -> None:
    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.endpoint", os.environ.get("MINIO_ENDPOINT", "http://minio:9000"))
    hadoop_conf.set("fs.s3a.access.key", os.environ.get("MINIO_ROOT_USER", "minioadmin"))
    hadoop_conf.set("fs.s3a.secret.key", os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"))
    hadoop_conf.set("fs.s3a.path.style.access", "true")
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")


def main() -> None:
    print("=== ClickstreamFunnelAnalysis: starting ===")
    spark = (
        SparkSession.builder.appName("ClickstreamFunnelAnalysis")
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )

    configure_s3a(spark)
    bucket = os.environ.get("MINIO_BUCKET", "clickstream-data")

    db = os.environ.get("POSTGRES_DB", "clickstream")
    user = os.environ.get("POSTGRES_USER", "clickstream")
    pw = os.environ.get("POSTGRES_PASSWORD", "clickstream")
    jdbc_url = f"jdbc:postgresql://postgres:5432/{db}"
    jdbc_props = {"driver": "org.postgresql.Driver", "user": user, "password": pw}

    print(f"Reading events from s3a://{bucket}/raw/events.csv ...")
    df = spark.read.csv(f"s3a://{bucket}/raw/events.csv", schema=SCHEMA, header=True)

    if df.isEmpty():
        print("WARNING: Source CSV is empty — nothing to process. Exiting.")
        spark.stop()
        return

    df = df.withColumn(
        "event_ts", F.to_timestamp("event_time", "yyyy-MM-dd HH:mm:ss 'UTC'")
    ).withColumn("date", F.to_date("event_ts")).withColumn(
        "root_category",
        F.when(
            F.col("category_code").isNotNull(),
            F.split(F.col("category_code"), "\\.")[0],
        ).otherwise("unknown"),
    )

    funnel = df.groupBy("date", "root_category").agg(
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("views"),
        F.sum(F.when(F.col("event_type") == "cart", 1).otherwise(0)).alias("carts"),
        F.sum(F.when(F.col("event_type") == "purchase", 1).otherwise(0)).alias("purchases"),
    ).withColumnRenamed("root_category", "category")

    funnel = funnel.withColumn(
        "view_to_cart_rate",
        F.when(F.col("views") > 0, F.col("carts") / F.col("views")).otherwise(0),
    ).withColumn(
        "cart_to_purchase_rate",
        F.when(F.col("carts") > 0, F.col("purchases") / F.col("carts")).otherwise(0),
    )

    funnel.write.jdbc(jdbc_url, "funnel_stats", mode="overwrite", properties=jdbc_props)

    spark.stop()
    print("=== ClickstreamFunnelAnalysis: complete ===")


if __name__ == "__main__":
    main()
