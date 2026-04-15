#!/bin/bash
set -euo pipefail

# Usage: spark-submit.sh <job-path> [--master <url>]
# Default master is the Spark standalone cluster.
# spark-stream overrides with --master local[2].

JOB=$1
shift

MASTER="spark://spark-master:7077"
if [ "${1:-}" = "--master" ]; then
    MASTER=$2
    shift 2
fi

MSYS_NO_PATHCONV=1 docker compose exec spark-master spark-submit \
    --master "$MASTER" \
    --conf spark.hadoop.hadoop.security.authentication=simple \
    --conf spark.jars.ivy=/tmp/ivy2 \
    --conf "spark.driver.extraJavaOptions=-Duser.home=/tmp -Duser.name=spark" \
    --conf "spark.executor.extraJavaOptions=-Duser.home=/tmp -Duser.name=spark" \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
    "$JOB" "$@"
