#!/bin/bash
set -euo pipefail

KAFKA_HOME=/opt/kafka
LOG_DIR="${KAFKA_LOG_DIRS:-/var/lib/kafka/data}"

mkdir -p "$LOG_DIR"

# Generate server.properties FIRST so both format and start use the same log.dirs.
# If kafka-storage.sh formats with a different log.dirs than what the server starts
# with, Kafka will refuse to start (metadata directory mismatch).
cat > /tmp/kafka-server.properties <<EOF
node.id=${KAFKA_NODE_ID:-1}
process.roles=${KAFKA_PROCESS_ROLES:-broker,controller}
listeners=${KAFKA_LISTENERS:-PLAINTEXT://:9092,CONTROLLER://:9093}
advertised.listeners=${KAFKA_ADVERTISED_LISTENERS:-PLAINTEXT://kafka:9092}
controller.listener.names=${KAFKA_CONTROLLER_LISTENER_NAMES:-CONTROLLER}
listener.security.protocol.map=${KAFKA_LISTENER_SECURITY_PROTOCOL_MAP:-CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT}
controller.quorum.voters=${KAFKA_CONTROLLER_QUORUM_VOTERS:-1@kafka:9093}
offsets.topic.replication.factor=${KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR:-1}
transaction.state.log.replication.factor=${KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR:-1}
transaction.state.log.min.isr=${KAFKA_TRANSACTION_STATE_LOG_MIN_ISR:-1}
auto.create.topics.enable=${KAFKA_AUTO_CREATE_TOPICS_ENABLE:-true}
log.dirs=${LOG_DIR}
EOF

# Format storage only if not already formatted.
# Use /tmp/kafka-server.properties as the config so that log.dirs matches
# what the server will use — avoids "Log directory ... was formatted with a
# different cluster ID" errors on restart.
if [ ! -f "$LOG_DIR/meta.properties" ]; then
  echo "Formatting Kafka KRaft storage with cluster ID ${KAFKA_CLUSTER_ID:-MkU3OEVBNTcwNTJENDM2Qk} ..."
  "$KAFKA_HOME/bin/kafka-storage.sh" format \
    -t "${KAFKA_CLUSTER_ID:-MkU3OEVBNTcwNTJENDM2Qk}" \
    -c /tmp/kafka-server.properties
fi

echo "Starting Kafka..."
exec "$KAFKA_HOME/bin/kafka-server-start.sh" /tmp/kafka-server.properties
