#!/bin/bash
set -euo pipefail

export HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-11-openjdk-amd64}
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

DATA_DIR=/hadoop/dfs/data

# Fix ownership — volume is mounted as root, hadoop user needs write access.
# Must run as root first, then re-exec as hadoop.
if [ "$(id -u)" = "0" ]; then
    mkdir -p "$DATA_DIR"
    chown -R hadoop:hadoop "$DATA_DIR"
    exec su -s /bin/bash hadoop "$0" "$@"
fi

# Now running as hadoop user
mkdir -p "$DATA_DIR"

echo "Waiting for NameNode..."
sleep 20

echo "Starting HDFS DataNode..."
$HADOOP_HOME/bin/hdfs datanode &

echo "Starting YARN NodeManager..."
$HADOOP_HOME/bin/yarn nodemanager &

echo "DataNode and NodeManager started."
wait
