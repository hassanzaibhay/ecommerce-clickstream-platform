"""Product affinity: co-occurrence and lift for product pairs."""
import os
import sys

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
    print("=== ClickstreamProductAffinity: starting ===")
    sample_rate = 0.1
    if "--sample" in sys.argv:
        idx = sys.argv.index("--sample")
        if idx + 1 < len(sys.argv):
            sample_rate = float(sys.argv[idx + 1])

    spark = (
        SparkSession.builder.appName("ClickstreamProductAffinity")
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

    print(f"Reading events from s3a://{bucket}/raw/events.csv (sample={sample_rate}) ...")
    df = spark.read.csv(f"s3a://{bucket}/raw/events.csv", schema=SCHEMA, header=True)

    if df.isEmpty():
        print("WARNING: Source CSV is empty — nothing to process. Exiting.")
        spark.stop()
        return

    # Sample for performance
    df = df.sample(fraction=sample_rate, seed=42)

    # Distinct products per session
    session_products = (
        df.filter(F.col("event_type").isin("view", "cart"))
        .select("user_session", "product_id")
        .dropDuplicates()
    )

    total_sessions = df.select("user_session").distinct().count()

    # Product counts
    product_counts = session_products.groupBy("product_id").agg(
        F.count("*").alias("session_count")
    )

    # Self-join for pairs
    sp_a = session_products.withColumnRenamed("product_id", "product_a")
    sp_b = session_products.withColumnRenamed("product_id", "product_b")

    pairs = sp_a.join(sp_b, "user_session").filter(F.col("product_a") < F.col("product_b"))

    co_occur = pairs.groupBy("product_a", "product_b").agg(
        F.count("*").alias("co_occurrences")
    )

    pc_a = product_counts.withColumnRenamed("product_id", "product_a").withColumnRenamed(
        "session_count", "count_a"
    )
    pc_b = product_counts.withColumnRenamed("product_id", "product_b").withColumnRenamed(
        "session_count", "count_b"
    )

    result = co_occur.join(pc_a, "product_a").join(pc_b, "product_b")

    result = result.withColumn(
        "lift",
        (F.col("co_occurrences") * F.lit(total_sessions))
        / (F.col("count_a") * F.col("count_b")),
    )

    top_pairs = (
        result.select("product_a", "product_b", "co_occurrences", "lift")
        .orderBy(F.col("lift").desc())
        .limit(10000)
    )

    top_pairs.write.jdbc(jdbc_url, "product_affinity", mode="overwrite", properties=jdbc_props)

    spark.stop()
    print("=== ClickstreamProductAffinity: complete ===")


if __name__ == "__main__":
    main()
