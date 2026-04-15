"""Batch analytics: compute daily KPIs, top products, categories, brands."""
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

JDBC_PROPS = {
    "driver": "org.postgresql.Driver",
}


def configure_s3a(spark: SparkSession) -> None:
    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.endpoint", os.environ.get("MINIO_ENDPOINT", "http://minio:9000"))
    hadoop_conf.set("fs.s3a.access.key", os.environ.get("MINIO_ROOT_USER", "minioadmin"))
    hadoop_conf.set("fs.s3a.secret.key", os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"))
    hadoop_conf.set("fs.s3a.path.style.access", "true")
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")


def get_jdbc_url() -> str:
    db = os.environ.get("POSTGRES_DB", "clickstream")
    user = os.environ.get("POSTGRES_USER", "clickstream")
    pw = os.environ.get("POSTGRES_PASSWORD", "clickstream")
    return f"jdbc:postgresql://postgres:5432/{db}", {**JDBC_PROPS, "user": user, "password": pw}


def main() -> None:
    print("=== ClickstreamBatchAnalytics: starting ===")
    spark = (
        SparkSession.builder.appName("ClickstreamBatchAnalytics")
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )

    configure_s3a(spark)
    bucket = os.environ.get("MINIO_BUCKET", "clickstream-data")
    jdbc_url, jdbc_props = get_jdbc_url()

    print(f"Reading events from s3a://{bucket}/raw/events.csv ...")
    df = spark.read.csv(f"s3a://{bucket}/raw/events.csv", schema=SCHEMA, header=True)

    if df.isEmpty():
        print("WARNING: Source CSV is empty — nothing to process. Exiting.")
        spark.stop()
        return

    df = df.withColumn(
        "event_ts", F.to_timestamp("event_time", "yyyy-MM-dd HH:mm:ss 'UTC'")
    ).withColumn("date", F.to_date("event_ts"))

    df = df.withColumn(
        "root_category",
        F.when(
            F.col("category_code").isNotNull(),
            F.split(F.col("category_code"), "\\.")[0],
        ).otherwise("unknown"),
    )

    df.cache()

    # --- Daily Metrics ---
    daily = df.groupBy("date").agg(
        F.count("*").alias("total_events"),
        F.countDistinct("user_id").alias("unique_users"),
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("total_views"),
        F.sum(F.when(F.col("event_type") == "cart", 1).otherwise(0)).alias("total_carts"),
        F.sum(F.when(F.col("event_type") == "purchase", 1).otherwise(0)).alias("total_purchases"),
        F.sum(
            F.when(F.col("event_type") == "purchase", F.col("price")).otherwise(0)
        ).alias("total_revenue"),
    )

    daily = daily.withColumn(
        "conversion_rate",
        F.when(F.col("unique_users") > 0, F.col("total_purchases") / F.col("unique_users")).otherwise(0),
    ).withColumn(
        "avg_order_value",
        F.when(F.col("total_purchases") > 0, F.col("total_revenue") / F.col("total_purchases")).otherwise(0),
    )

    daily.write.jdbc(jdbc_url, "daily_metrics", mode="overwrite", properties=jdbc_props)
    daily.write.mode("overwrite").parquet(f"s3a://{bucket}/processed/daily_metrics/")

    # --- Top Products ---
    products = df.groupBy("product_id", "category_code", "brand", "price").agg(
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("views"),
        F.sum(F.when(F.col("event_type") == "cart", 1).otherwise(0)).alias("carts"),
        F.sum(F.when(F.col("event_type") == "purchase", 1).otherwise(0)).alias("purchases"),
        F.sum(F.when(F.col("event_type") == "purchase", F.col("price")).otherwise(0)).alias("revenue"),
    ).withColumnRenamed("category_code", "category")

    products.write.jdbc(jdbc_url, "top_products", mode="overwrite", properties=jdbc_props)

    # --- Top Categories ---
    categories = df.groupBy("root_category").agg(
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("views"),
        F.sum(F.when(F.col("event_type") == "cart", 1).otherwise(0)).alias("carts"),
        F.sum(F.when(F.col("event_type") == "purchase", 1).otherwise(0)).alias("purchases"),
        F.sum(F.when(F.col("event_type") == "purchase", F.col("price")).otherwise(0)).alias("revenue"),
    ).withColumnRenamed("root_category", "category")

    categories.write.jdbc(jdbc_url, "top_categories", mode="overwrite", properties=jdbc_props)

    # --- Top Brands ---
    brands = df.filter(F.col("brand").isNotNull()).groupBy("brand").agg(
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("views"),
        F.sum(F.when(F.col("event_type") == "cart", 1).otherwise(0)).alias("carts"),
        F.sum(F.when(F.col("event_type") == "purchase", 1).otherwise(0)).alias("purchases"),
        F.sum(F.when(F.col("event_type") == "purchase", F.col("price")).otherwise(0)).alias("revenue"),
    )

    brands.write.jdbc(jdbc_url, "top_brands", mode="overwrite", properties=jdbc_props)

    df.write.mode("overwrite").parquet(f"s3a://{bucket}/processed/events_enriched/")

    spark.stop()
    print("=== ClickstreamBatchAnalytics: complete ===")


if __name__ == "__main__":
    main()
