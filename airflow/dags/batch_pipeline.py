"""Airflow DAG for the clickstream batch analytics pipeline."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

SPARK_SUBMIT = (
    "docker exec spark-master spark-submit "
    "--master spark://spark-master:7077 "
    "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
    "org.postgresql:postgresql:42.7.3 "
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="clickstream_batch_pipeline",
    default_args=default_args,
    description="E-Commerce clickstream batch analytics pipeline",
    schedule="@daily",
    start_date=datetime(2019, 10, 1),
    catchup=False,
    tags=["clickstream", "batch"],
) as dag:

    spark_batch_analytics = BashOperator(
        task_id="spark_batch_analytics",
        bash_command=f"{SPARK_SUBMIT}/spark/jobs/batch_analytics.py",
    )

    spark_funnel_analysis = BashOperator(
        task_id="spark_funnel_analysis",
        bash_command=f"{SPARK_SUBMIT}/spark/jobs/funnel_analysis.py",
    )

    spark_cart_abandonment = BashOperator(
        task_id="spark_cart_abandonment",
        bash_command=f"{SPARK_SUBMIT}/spark/jobs/cart_abandonment.py",
    )

    spark_product_affinity = BashOperator(
        task_id="spark_product_affinity",
        bash_command=f"{SPARK_SUBMIT}/spark/jobs/product_affinity.py",
    )

    spark_prepare_mapreduce = BashOperator(
        task_id="spark_prepare_mapreduce",
        bash_command=f"{SPARK_SUBMIT}/spark/jobs/prepare_mapreduce.py",
    )

    hadoop_mapreduce = BashOperator(
        task_id="hadoop_mapreduce",
        bash_command="docker exec namenode bash /hadoop/scripts/run_mapreduce.sh",
    )

    (
        spark_batch_analytics
        >> spark_funnel_analysis
        >> spark_cart_abandonment
        >> spark_product_affinity
        >> spark_prepare_mapreduce
        >> hadoop_mapreduce
    )
