"""Spark Structured Streaming consumer for Kafka clickstream events."""
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

EVENT_SCHEMA = StructType(
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


def main() -> None:
    spark = SparkSession.builder.appName("ClickstreamConsumer").master("local[2]").getOrCreate()

    kafka_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.environ.get("KAFKA_TOPIC_EVENTS", "clickstream-events")

    db = os.environ.get("POSTGRES_DB", "clickstream")
    user = os.environ.get("POSTGRES_USER", "clickstream")
    pw = os.environ.get("POSTGRES_PASSWORD", "clickstream")
    jdbc_url = f"jdbc:postgresql://postgres:5432/{db}"
    jdbc_props = {"driver": "org.postgresql.Driver", "user": user, "password": pw}

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = raw.selectExpr("CAST(value AS STRING) as json_str").select(
        F.from_json(F.col("json_str"), EVENT_SCHEMA).alias("data")
    ).select("data.*")

    parsed = parsed.withColumn(
        "event_ts", F.to_timestamp("event_time", "yyyy-MM-dd'T'HH:mm:ss'Z'")
    )

    sessions = parsed.groupBy("user_session").agg(
        F.first("user_id").alias("user_id"),
        F.max("event_ts").alias("last_event_time"),
        F.count("*").alias("event_count"),
        F.max(F.when(F.col("event_type") == "cart", F.lit(True)).otherwise(F.lit(False))).alias("has_cart"),
        F.max(F.when(F.col("event_type") == "purchase", F.lit(True)).otherwise(F.lit(False))).alias("has_purchase"),
        F.last("product_id").alias("last_product_id"),
        F.last("category_code").alias("last_category"),
    ).withColumnRenamed("user_session", "session_id").withColumn(
        "updated_at", F.current_timestamp()
    )

    def write_batch(batch_df, epoch_id):
        if batch_df.isEmpty():
            return
        batch_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", "live_sessions") \
            .option("driver", "org.postgresql.Driver") \
            .option("user", user) \
            .option("password", pw) \
            .option("truncate", "true") \
            .mode("overwrite") \
            .save()

    query = (
        sessions.writeStream.outputMode("complete")
        .foreachBatch(write_batch)
        .trigger(processingTime="5 seconds")
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
