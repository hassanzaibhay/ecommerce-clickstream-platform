#!/bin/bash
set -euo pipefail

export HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
export PATH=$PATH:$HADOOP_HOME/bin

echo "Creating HDFS directories..."
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /user/hadoop/clickstream/csv/category_events
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /user/hadoop/clickstream/csv/brand_revenue
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /user/hadoop/clickstream/output

# Grant world-writable permissions so the spark user (running as 'spark', not
# 'hadoop') can write CSV output into these directories via spark-prepare-mr.
$HADOOP_HOME/bin/hdfs dfs -chmod -R 777 /user/hadoop/clickstream

echo "HDFS directories created."
$HADOOP_HOME/bin/hdfs dfs -ls /user/hadoop/clickstream/
