#!/bin/bash
set -euo pipefail

export HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-11-openjdk-amd64}
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# Search tools/lib first (standard location), fall back to full tree scan
STREAMING_JAR=$(find "$HADOOP_HOME/share/hadoop/tools/lib" -name "hadoop-streaming-*.jar" 2>/dev/null | head -1)
if [ -z "$STREAMING_JAR" ]; then
  STREAMING_JAR=$(find "$HADOOP_HOME" -name "hadoop-streaming-*.jar" 2>/dev/null | head -1)
fi

if [ -z "$STREAMING_JAR" ]; then
  echo "ERROR: hadoop-streaming jar not found"
  exit 1
fi

echo "Using streaming jar: $STREAMING_JAR"

echo "=== HDFS contents ==="
$HADOOP_HOME/bin/hdfs dfs -ls -R /user/hadoop/clickstream/csv/ || echo "WARNING: CSV directory empty or missing"

# Note: -files is a Hadoop generic option and MUST come before streaming options
# (-input, -output, -mapper, -reducer).

echo "Running category_events MapReduce..."
$HADOOP_HOME/bin/hdfs dfs -rm -r -f /user/hadoop/clickstream/output/category_events || true

$HADOOP_HOME/bin/hadoop jar "$STREAMING_JAR" \
  -files /opt/hadoop/mapreduce/category_events/mapper.py,/opt/hadoop/mapreduce/category_events/reducer.py \
  -input /user/hadoop/clickstream/csv/category_events \
  -output /user/hadoop/clickstream/output/category_events \
  -mapper mapper.py \
  -reducer reducer.py

echo "Running brand_revenue MapReduce..."
$HADOOP_HOME/bin/hdfs dfs -rm -r -f /user/hadoop/clickstream/output/brand_revenue || true

$HADOOP_HOME/bin/hadoop jar "$STREAMING_JAR" \
  -files /opt/hadoop/mapreduce/brand_revenue/mapper.py,/opt/hadoop/mapreduce/brand_revenue/reducer.py \
  -input /user/hadoop/clickstream/csv/brand_revenue \
  -output /user/hadoop/clickstream/output/brand_revenue \
  -mapper mapper.py \
  -reducer reducer.py

echo "MapReduce complete."
$HADOOP_HOME/bin/hdfs dfs -ls /user/hadoop/clickstream/output/
