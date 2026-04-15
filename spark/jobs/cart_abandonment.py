"""Cart abandonment analysis: sessions with cart but no purchase."""
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
    print("=== ClickstreamCartAbandonment: starting ===")
    spark = (
        SparkSession.builder.appName("ClickstreamCartAbandonment")
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

    # Per-session flags
    session_flags = df.groupBy("user_session", "date", "root_category").agg(
        F.max(F.when(F.col("event_type") == "cart", F.lit(True)).otherwise(F.lit(False))).alias("has_cart"),
        F.max(F.when(F.col("event_type") == "purchase", F.lit(True)).otherwise(F.lit(False))).alias("has_purchase"),
    )

    cart_sessions = session_flags.filter(F.col("has_cart"))

    abandonment = cart_sessions.groupBy("date", "root_category").agg(
        F.sum(
            F.when(~F.col("has_purchase"), 1).otherwise(0)
        ).alias("abandoned_carts"),
        F.sum(
            F.when(F.col("has_purchase"), 1).otherwise(0)
        ).alias("completed_purchases"),
    ).withColumnRenamed("root_category", "category")

    abandonment = abandonment.withColumn(
        "abandonment_rate",
        F.when(
            (F.col("abandoned_carts") + F.col("completed_purchases")) > 0,
            F.col("abandoned_carts") / (F.col("abandoned_carts") + F.col("completed_purchases")),
        ).otherwise(0),
    )

    abandonment.write.jdbc(jdbc_url, "cart_abandonment", mode="overwrite", properties=jdbc_props)

    spark.stop()
    print("=== ClickstreamCartAbandonment: complete ===")


if __name__ == "__main__":
    main()
