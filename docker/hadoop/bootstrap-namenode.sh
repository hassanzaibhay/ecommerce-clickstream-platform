#!/bin/bash
set -euo pipefail

export HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-11-openjdk-amd64}
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

NAME_DIR=/hadoop/dfs/name

# Fix ownership — volume is mounted as root, hadoop user needs write access.
# Must run as root first, then re-exec as hadoop.
if [ "$(id -u)" = "0" ]; then
    mkdir -p "$NAME_DIR"
    chown -R hadoop:hadoop "$NAME_DIR"
    exec su -s /bin/bash hadoop "$0" "$@"
fi

# Now running as hadoop user
mkdir -p "$NAME_DIR"

if [ ! -d "$NAME_DIR/current" ]; then
    echo "Formatting namenode..."
    $HADOOP_HOME/bin/hdfs namenode -format -force -nonInteractive
fi

echo "Starting HDFS NameNode..."
$HADOOP_HOME/bin/hdfs namenode &

echo "Waiting for NameNode to be ready..."
sleep 15

echo "Starting YARN ResourceManager..."
$HADOOP_HOME/bin/yarn resourcemanager &

echo "NameNode and ResourceManager started."
wait
