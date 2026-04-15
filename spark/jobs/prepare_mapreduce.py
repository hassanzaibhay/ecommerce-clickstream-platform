"""Prepare CSV data on HDFS for Hadoop MapReduce jobs."""
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
    print("=== ClickstreamPrepareMapReduce: starting ===")
    spark = (
        SparkSession.builder.appName("ClickstreamPrepareMapReduce")
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )

    configure_s3a(spark)
    bucket = os.environ.get("MINIO_BUCKET", "clickstream-data")

    print(f"Reading events from s3a://{bucket}/raw/events.csv ...")
    df = spark.read.csv(f"s3a://{bucket}/raw/events.csv", schema=SCHEMA, header=True)

    if df.isEmpty():
        print("WARNING: Source CSV is empty — nothing to process. Exiting.")
        spark.stop()
        return

    df = df.withColumn(
        "root_category",
        F.when(
            F.col("category_code").isNotNull(),
            F.split(F.col("category_code"), "\\.")[0],
        ).otherwise("unknown"),
    )

    hdfs_base = "hdfs://namenode:9000/user/hadoop/clickstream/csv"

    # Category events CSV: root_category, event_type
    cat_df = df.select(
        F.col("root_category").alias("category"),
        F.col("event_type"),
    )
    cat_df.write.mode("overwrite").csv(f"{hdfs_base}/category_events", header=False)

    # Brand revenue CSV: brand, price (purchase events only)
    brand_df = df.filter(
        (F.col("event_type") == "purchase") & F.col("brand").isNotNull()
    ).select("brand", "price")
    brand_df.write.mode("overwrite").csv(f"{hdfs_base}/brand_revenue", header=False)

    spark.stop()
    print("=== ClickstreamPrepareMapReduce: complete ===")


if __name__ == "__main__":
    main()
