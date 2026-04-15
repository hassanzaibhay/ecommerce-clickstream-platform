# Prompt — ecommerce-clickstream-platform

> Paste this entire file as your first message to Claude Code.

---

You are building **ecommerce-clickstream-platform** — a production-grade portfolio data engineering project by Hassan Zaib Hayat. Generate the **complete, working scaffold** in one pass. Every file must be production-ready. Do not leave TODOs, stubs, or placeholder logic. Do not ask clarifying questions — follow this spec exactly.

---

## PROJECT OVERVIEW

E-Commerce Clickstream Analytics Platform processing the Kaggle "eCommerce behavior data from multi category store" dataset (~285M events, 14 GB, Oct–Nov 2019, fields: event_time, event_type, product_id, category_id, category_code, brand, price, user_id, user_session).

**Domain analytics:** funnel analysis (view→cart→purchase), cart abandonment detection, product affinity/recommendations, session analytics, real-time live monitor.

**13 Docker services:** namenode, datanode, spark-master, spark-worker, kafka, airflow-webserver, airflow-scheduler, airflow-init, postgres, minio, redis, api, frontend.

---

## ABSOLUTE CONSTRAINTS — READ BEFORE WRITING ANY CODE

1. **Pin ALL Docker image versions** — no `:latest`. Use EXACTLY these images:
   - `apache/hadoop:3.4.1` (custom Dockerfile — install python3 via apt-get)
   - `bitnamilegacy/spark:3.5.6` (Bitnami moved versioned tags to bitnamilegacy namespace in Aug 2025)
   - `apache/kafka:3.9.0` (KRaft mode — NOT bitnami/kafka)
   - `apache/airflow:2.9.3`
   - `postgres:16.3`
   - `minio/minio:RELEASE.2024-11-07T00-52-20Z`
   - `redis:7.4.1-alpine`
   - `python:3.11-slim` (for FastAPI)
   - `node:20-alpine` + `nginx:1.27-alpine` (multi-stage frontend)

2. **Kafka KRaft mode**: Use `apache/kafka:3.9.0`. Create `docker/kafka/start-kafka.sh` that: sets `KAFKA_CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk` (fixed UUID), calls `kafka-storage.sh format` only if not already formatted, then starts `kafka-server-start.sh`. Never use bitnami/kafka.

3. **Hadoop python3**: `apache/hadoop:3.4.1` has no python3. `docker/hadoop/Dockerfile` must install it: `RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*`

4. **Hadoop bootstrap — namenode**: `docker/hadoop/bootstrap-namenode.sh` must: format namenode (if fresh), start `hdfs namenode`, start `yarn resourcemanager`. Both daemons must be running.

5. **Hadoop bootstrap — datanode**: `docker/hadoop/bootstrap-datanode.sh` must: start `hdfs datanode`, start `yarn nodemanager`. Both daemons must be running.

6. **MapReduce scripts mounted on BOTH nodes**: mapper.py and reducer.py must be COPYed into the hadoop Dockerfile (shared by both namenode and datanode containers). Both containers extend the same `docker/hadoop/Dockerfile`.

7. **YARN memory**: `yarn-site.xml` must set `yarn.nodemanager.resource.memory-mb` to `8192`, `yarn.scheduler.minimum-allocation-mb` to `512`, `yarn.scheduler.maximum-allocation-mb` to `8192`.

8. **MapReduce reads CSV only**: Hadoop Streaming cannot read Parquet. `spark/jobs/prepare_mapreduce.py` converts Parquet on MinIO → CSV and uploads to HDFS `/user/hadoop/clickstream/csv/` before MapReduce runs.

9. **asyncpg query parameters**: Never use `$1 IS NULL OR column >= $1`. All API query parameters are required. Use `$1`, `$2`, ... placeholders with named Python function arguments matching parameter position exactly.

10. **Spark Streaming restart safety**: In `clickstream_consumer.py`, every micro-batch write to PostgreSQL uses `mode("overwrite").option("truncate", "true")` on the `live_sessions` table to prevent duplicate key errors on restart.

11. **Frontend date anchoring**: `Overview.tsx`, `FunnelAnalysis.tsx`, `ProductAnalytics.tsx` must call `GET /api/data-range` on mount and set the default date range to the last 30 days of the actual data (not today's date). Anchor all date pickers to `min_date`/`max_date` from the response.

12. **Number formatting**: All React components must use `Intl.NumberFormat` helpers. Show `3.2M` not `3211175`, `$42.50` not `42.5`, `14.3%` not `0.143`. Define formatters once in `src/api/client.ts` and import everywhere.

13. **Makefile — Windows-compatible**: No `grep`, `sed`, `awk`, `cat`, `wc`, or bash for-loops at the Makefile level. Help target uses `@echo` for each target manually. Delegate ALL shell logic to scripts inside containers via `docker compose exec`.

14. **All bash scripts**: First line after shebang must be `set -euo pipefail`.

15. **docker-compose.override.yml**: gitignored.

16. **Secrets**: All in `.env` (gitignored). `.env.example` committed with blank sensitive values. Non-secret defaults (ports, topic names) can have values in `.env.example`.

17. **`.dockerignore`**: Exclude `.env`, `.git`, `data/`, `node_modules/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `terraform/`.

18. **GitHub Actions CI**: Runs `ruff check`, `mypy --strict` (api/ only), `pytest` with `httpx` and `pytest-asyncio`. All DB calls mocked with `unittest.mock.AsyncMock`. No docker compose in CI. Install ALL needed packages: `pip install fastapi asyncpg pytest pytest-asyncio httpx mypy ruff types-requests`.

19. **FastAPI `data-range` endpoint**: Returns `{"min_date": "2019-10-01", "max_date": "2019-11-30"}` (hardcoded from dataset knowledge — do not query DB for this).

20. **Spark packages flag**: All spark-submit calls include `--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3`.

21. **MinIO S3A config in Spark**: Each Spark job that reads from MinIO must configure `spark._jsc.hadoopConfiguration()` with: `fs.s3a.endpoint`, `fs.s3a.access.key`, `fs.s3a.secret.key`, `fs.s3a.path.style.access=true`, `fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem`.

22. **Explicit Spark schemas**: Define `StructType` with all fields for CSV reads. Never use `inferSchema=True` on large files.

23. **SSE Live Monitor**: `/api/live/sessions` returns `text/event-stream`. React `LiveMonitor.tsx` uses `EventSource` with reconnect on error (exponential backoff, max 30s).

---

## COMPLETE FILE TREE — CREATE ALL OF THESE

```
ecommerce-clickstream-platform/
├── .github/
│   └── workflows/
│       └── ci.yml
├── airflow/
│   ├── dags/
│   │   └── batch_pipeline.py
│   └── requirements.txt
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── overview.py
│   │   ├── funnel.py
│   │   ├── products.py
│   │   └── live.py
│   └── tests/
│       ├── conftest.py
│       ├── test_overview.py
│       ├── test_funnel.py
│       └── test_products.py
├── docker/
│   ├── hadoop/
│   │   ├── Dockerfile
│   │   ├── bootstrap-namenode.sh
│   │   ├── bootstrap-datanode.sh
│   │   ├── core-site.xml
│   │   ├── hdfs-site.xml
│   │   ├── yarn-site.xml
│   │   └── mapred-site.xml
│   └── kafka/
│       └── start-kafka.sh
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── api/
│       │   └── client.ts
│       ├── components/
│       │   ├── Layout.tsx
│       │   └── KPICard.tsx
│       └── pages/
│           ├── Overview.tsx
│           ├── FunnelAnalysis.tsx
│           ├── ProductAnalytics.tsx
│           └── LiveMonitor.tsx
├── hadoop/
│   ├── mapreduce/
│   │   ├── category_events/
│   │   │   ├── mapper.py
│   │   │   └── reducer.py
│   │   └── brand_revenue/
│   │       ├── mapper.py
│   │       └── reducer.py
│   └── scripts/
│       ├── upload_to_hdfs.sh
│       └── run_mapreduce.sh
├── kafka/
│   └── producer/
│       └── clickstream_producer.py
├── scripts/
│   ├── upload_to_minio.py
│   ├── init_db.sql
│   └── load_sample.py
├── spark/
│   ├── jobs/
│   │   ├── batch_analytics.py
│   │   ├── funnel_analysis.py
│   │   ├── cart_abandonment.py
│   │   ├── product_affinity.py
│   │   └── prepare_mapreduce.py
│   └── streaming/
│       └── clickstream_consumer.py
├── terraform/
│   ├── aws/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── gcp/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── .env.example
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## DETAILED FILE SPECIFICATIONS

### `.env.example`
```env
# PostgreSQL
POSTGRES_DB=clickstream
POSTGRES_USER=clickstream
POSTGRES_PASSWORD=
DATABASE_URL=postgresql+asyncpg://clickstream:@postgres:5432/clickstream

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=
MINIO_ENDPOINT=http://minio:9000
MINIO_BUCKET=clickstream-data

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_EVENTS=clickstream-events
KAFKA_CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk

# Airflow
AIRFLOW_UID=50000
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://clickstream:@postgres:5432/airflow
AIRFLOW__CORE__FERNET_KEY=
AIRFLOW__WEBSERVER__SECRET_KEY=
AIRFLOW__CORE__LOAD_EXAMPLES=False

# Spark
SPARK_MASTER_URL=spark://spark-master:7077

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### `.gitignore`
```
.env
data/
*.egg-info/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
dist/
build/
docker-compose.override.yml
terraform/.terraform/
terraform/**/*.tfstate
terraform/**/*.tfstate.backup
terraform/**/.terraform.lock.hcl
CLAUDE.md
```

### `.dockerignore`
```
.env
.git
data/
node_modules/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
terraform/
*.md
```

---

### `docker-compose.yml`

13 services. Use the exact image versions specified in constraints. All services use `env_file: .env`. Health checks on postgres, minio, kafka, redis. Services that depend on postgres use `condition: service_healthy`.

**Service details:**

**postgres:**
- image: `postgres:16.3`
- environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD from .env
- volumes: `postgres_data:/var/lib/postgresql/data`, `./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql:ro`
- healthcheck: `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}`
- ports: `5432:5432`

**minio:**
- image: `minio/minio:RELEASE.2024-11-07T00-52-20Z`
- command: `server /data --console-address ":9001"`
- ports: `9000:9000`, `9001:9001`
- volumes: `minio_data:/data`
- healthcheck: `curl -f http://localhost:9000/minio/health/live`

**redis:**
- image: `redis:7.4.1-alpine`
- ports: `6379:6379`
- healthcheck: `redis-cli ping`

**kafka:**
- build: `context: .`, `dockerfile: docker/kafka/Dockerfile` — BUT there is no kafka Dockerfile; use image `apache/kafka:3.9.0` directly and override entrypoint with `docker/kafka/start-kafka.sh`. Actually: use `image: apache/kafka:3.9.0` and mount `start-kafka.sh` as a volume, setting the command to `bash /opt/kafka/start-kafka.sh`.
  
  CORRECTION: Create `docker/kafka/Dockerfile` that extends `apache/kafka:3.9.0` and COPYs `start-kafka.sh`, setting `CMD ["bash", "/opt/kafka/start-kafka.sh"]`. This avoids bind-mount path issues.

  Environment:
  ```
  KAFKA_NODE_ID: 1
  KAFKA_PROCESS_ROLES: broker,controller
  KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
  KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
  KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
  KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
  KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
  KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
  KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
  KAFKA_LOG_DIRS: /var/lib/kafka/data
  ```
  - ports: `9092:9092`
  - healthcheck: test `kafka-topics.sh --bootstrap-server localhost:9092 --list` exits 0

**namenode:**
- build: `context: .`, `dockerfile: docker/hadoop/Dockerfile`
- command: `bash /hadoop-bootstrap/bootstrap-namenode.sh`
- volumes: `namenode_data:/hadoop/dfs/name`, `./docker/hadoop/bootstrap-namenode.sh:/hadoop-bootstrap/bootstrap-namenode.sh:ro`
- Also mount hadoop config XMLs into `/opt/hadoop/etc/hadoop/`
- ports: `9870:9870` (HDFS UI), `8088:8088` (YARN UI)
- environment: `HADOOP_ROLE=namenode`

**datanode:**
- build: same Dockerfile as namenode
- command: `bash /hadoop-bootstrap/bootstrap-datanode.sh`
- volumes: `datanode_data:/hadoop/dfs/data`
- depends_on: namenode
- environment: `HADOOP_ROLE=datanode`

**spark-master:**
- image: `bitnamilegacy/spark:3.5.6`
- environment: `SPARK_MODE=master`, `SPARK_RPC_AUTHENTICATION_ENABLED=no`, `SPARK_RPC_ENCRYPTION_ENABLED=no`, `SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no`, `SPARK_SSL_ENABLED=no`
- volumes: `./spark:/spark`, `./data:/data` (for local fallback)
- ports: `8081:8080`, `7077:7077`

**spark-worker:**
- image: `bitnamilegacy/spark:3.5.6`
- environment: `SPARK_MODE=worker`, `SPARK_MASTER_URL=spark://spark-master:7077`, `SPARK_WORKER_MEMORY=4G`, `SPARK_WORKER_CORES=2`
- depends_on: spark-master
- volumes: `./spark:/spark`

**airflow-init:**
- image: `apache/airflow:2.9.3`
- entrypoint: `/bin/bash`
- command: `-c "airflow db migrate && airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin"`
- depends_on postgres (healthy)
- env_file: .env

**airflow-webserver:**
- image: `apache/airflow:2.9.3`
- command: webserver
- ports: `8080:8080`
- volumes: `./airflow/dags:/opt/airflow/dags`, `./airflow/requirements.txt:/requirements.txt`
- depends_on: airflow-init (via restart: on-failure workaround), postgres
- healthcheck: `curl -f http://localhost:8080/health`

**airflow-scheduler:**
- image: `apache/airflow:2.9.3`
- command: scheduler
- volumes: `./airflow/dags:/opt/airflow/dags`
- depends_on: airflow-webserver

**api:**
- build: `context: ./api`
- ports: `8000:8000`
- depends_on: postgres (healthy), redis (healthy)
- volumes: (none — code is baked in image)

**frontend:**
- build: `context: ./frontend`
- ports: `3000:80`
- depends_on: api

**Volumes:** `postgres_data`, `minio_data`, `namenode_data`, `datanode_data`

**Networks:** single `clickstream-net` bridge network, all services attached.

---

### `docker/hadoop/Dockerfile`

```dockerfile
FROM apache/hadoop:3.4.1

USER root

RUN apt-get update && \
    apt-get install -y python3 && \
    rm -rf /var/lib/apt/lists/*

# Copy Hadoop config
COPY docker/hadoop/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml
COPY docker/hadoop/hdfs-site.xml /opt/hadoop/etc/hadoop/hdfs-site.xml
COPY docker/hadoop/yarn-site.xml /opt/hadoop/etc/hadoop/yarn-site.xml
COPY docker/hadoop/mapred-site.xml /opt/hadoop/etc/hadoop/mapred-site.xml

# Copy MapReduce scripts — must be on BOTH namenode AND datanode
COPY hadoop/mapreduce /opt/hadoop/mapreduce

RUN chmod +x /opt/hadoop/mapreduce/category_events/mapper.py \
             /opt/hadoop/mapreduce/category_events/reducer.py \
             /opt/hadoop/mapreduce/brand_revenue/mapper.py \
             /opt/hadoop/mapreduce/brand_revenue/reducer.py

USER hadoop
```

### `docker/hadoop/core-site.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://namenode:9000</value>
  </property>
  <property>
    <name>hadoop.tmp.dir</name>
    <value>/tmp/hadoop-${user.name}</value>
  </property>
</configuration>
```

### `docker/hadoop/hdfs-site.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>/hadoop/dfs/name</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/hadoop/dfs/data</value>
  </property>
  <property>
    <name>dfs.namenode.datanode.registration.ip-hostname-check</name>
    <value>false</value>
  </property>
</configuration>
```

### `docker/hadoop/yarn-site.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>yarn.resourcemanager.hostname</name>
    <value>namenode</value>
  </property>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
  <property>
    <name>yarn.nodemanager.aux-services.mapreduce_shuffle.class</name>
    <value>org.apache.hadoop.mapred.ShuffleHandler</value>
  </property>
  <property>
    <name>yarn.nodemanager.resource.memory-mb</name>
    <value>8192</value>
  </property>
  <property>
    <name>yarn.scheduler.minimum-allocation-mb</name>
    <value>512</value>
  </property>
  <property>
    <name>yarn.scheduler.maximum-allocation-mb</name>
    <value>8192</value>
  </property>
  <property>
    <name>yarn.nodemanager.vmem-check-enabled</name>
    <value>false</value>
  </property>
  <property>
    <name>yarn.nodemanager.pmem-check-enabled</name>
    <value>false</value>
  </property>
  <property>
    <name>yarn.resourcemanager.address</name>
    <value>namenode:8032</value>
  </property>
  <property>
    <name>yarn.resourcemanager.resource-tracker.address</name>
    <value>namenode:8031</value>
  </property>
  <property>
    <name>yarn.resourcemanager.scheduler.address</name>
    <value>namenode:8030</value>
  </property>
</configuration>
```

### `docker/hadoop/mapred-site.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
  <property>
    <name>mapreduce.application.classpath</name>
    <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
  </property>
  <property>
    <name>mapreduce.map.memory.mb</name>
    <value>512</value>
  </property>
  <property>
    <name>mapreduce.reduce.memory.mb</name>
    <value>512</value>
  </property>
  <property>
    <name>yarn.app.mapreduce.am.resource.mb</name>
    <value>512</value>
  </property>
</configuration>
```

### `docker/hadoop/bootstrap-namenode.sh`
```bash
#!/bin/bash
set -euo pipefail

HADOOP_HOME=/opt/hadoop
NAME_DIR=/hadoop/dfs/name

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
```

### `docker/hadoop/bootstrap-datanode.sh`
```bash
#!/bin/bash
set -euo pipefail

HADOOP_HOME=/opt/hadoop

echo "Waiting for NameNode..."
sleep 20

echo "Starting HDFS DataNode..."
$HADOOP_HOME/bin/hdfs datanode &

echo "Starting YARN NodeManager..."
$HADOOP_HOME/bin/yarn nodemanager &

echo "DataNode and NodeManager started."
wait
```

### `docker/kafka/Dockerfile`
```dockerfile
FROM apache/kafka:3.9.0
COPY docker/kafka/start-kafka.sh /opt/kafka/start-kafka.sh
RUN chmod +x /opt/kafka/start-kafka.sh
CMD ["bash", "/opt/kafka/start-kafka.sh"]
```

### `docker/kafka/start-kafka.sh`
```bash
#!/bin/bash
set -euo pipefail

KAFKA_HOME=/opt/kafka
LOG_DIR="${KAFKA_LOG_DIRS:-/var/lib/kafka/data}"

mkdir -p "$LOG_DIR"

# Format storage only if not already formatted
if [ ! -f "$LOG_DIR/meta.properties" ]; then
  echo "Formatting Kafka KRaft storage..."
  "$KAFKA_HOME/bin/kafka-storage.sh" format \
    -t "${KAFKA_CLUSTER_ID:-MkU3OEVBNTcwNTJENDM2Qk}" \
    -c "$KAFKA_HOME/config/kraft/server.properties"
fi

# Generate server.properties from environment
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

echo "Starting Kafka..."
exec "$KAFKA_HOME/bin/kafka-server-start.sh" /tmp/kafka-server.properties
```

---

### `scripts/init_db.sql`

Create all tables with IF NOT EXISTS. Exact schema:

```sql
-- Batch analytics tables
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    total_events BIGINT DEFAULT 0,
    unique_users BIGINT DEFAULT 0,
    total_views BIGINT DEFAULT 0,
    total_carts BIGINT DEFAULT 0,
    total_purchases BIGINT DEFAULT 0,
    total_revenue NUMERIC(14,2) DEFAULT 0,
    conversion_rate NUMERIC(6,4) DEFAULT 0,
    avg_order_value NUMERIC(10,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS funnel_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(255) NOT NULL,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    view_to_cart_rate NUMERIC(6,4) DEFAULT 0,
    cart_to_purchase_rate NUMERIC(6,4) DEFAULT 0,
    UNIQUE (date, category)
);

CREATE TABLE IF NOT EXISTS top_products (
    product_id BIGINT PRIMARY KEY,
    category VARCHAR(255),
    brand VARCHAR(255),
    price NUMERIC(10,2) DEFAULT 0,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    revenue NUMERIC(14,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS top_categories (
    category VARCHAR(255) PRIMARY KEY,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    revenue NUMERIC(14,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS top_brands (
    brand VARCHAR(255) PRIMARY KEY,
    views BIGINT DEFAULT 0,
    carts BIGINT DEFAULT 0,
    purchases BIGINT DEFAULT 0,
    revenue NUMERIC(14,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cart_abandonment (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(255) NOT NULL,
    abandoned_carts BIGINT DEFAULT 0,
    completed_purchases BIGINT DEFAULT 0,
    abandonment_rate NUMERIC(6,4) DEFAULT 0,
    UNIQUE (date, category)
);

CREATE TABLE IF NOT EXISTS product_affinity (
    id SERIAL PRIMARY KEY,
    product_a BIGINT NOT NULL,
    product_b BIGINT NOT NULL,
    co_occurrences BIGINT DEFAULT 0,
    lift NUMERIC(8,4) DEFAULT 0,
    UNIQUE (product_a, product_b)
);

CREATE TABLE IF NOT EXISTS category_events (
    category VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_count BIGINT DEFAULT 0,
    PRIMARY KEY (category, event_type)
);

CREATE TABLE IF NOT EXISTS brand_revenue (
    brand VARCHAR(255) PRIMARY KEY,
    total_revenue NUMERIC(14,2) DEFAULT 0,
    purchase_count BIGINT DEFAULT 0
);

-- Streaming table
CREATE TABLE IF NOT EXISTS live_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT,
    last_event_time TIMESTAMP,
    event_count INT DEFAULT 0,
    has_cart BOOLEAN DEFAULT FALSE,
    has_purchase BOOLEAN DEFAULT FALSE,
    last_product_id BIGINT,
    last_category VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Airflow uses a separate schema; create its DB
-- (Airflow init handles its own migrations)
```

---

### `api/requirements.txt`
```
fastapi==0.115.5
uvicorn[standard]==0.32.1
asyncpg==0.30.0
python-dotenv==1.0.1
pydantic==2.10.2
redis==5.2.0
```

### `api/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `api/database.py`

Async connection pool using asyncpg. Pool created in FastAPI lifespan. Expose `get_db()` dependency that yields a connection.

```python
import os
import asyncpg
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncGenerator

_pool: asyncpg.Pool | None = None

async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://"),
        min_size=2,
        max_size=10,
    )

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    assert _pool is not None, "DB pool not initialized"
    async with _pool.acquire() as conn:
        yield conn

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    _pool = await create_pool()
    yield
    await _pool.close()
```

### `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import lifespan
from routers import overview, funnel, products, live

app = FastAPI(title="Clickstream Analytics API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(funnel.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(live.router, prefix="/api")

@app.get("/api/health")
async def health():
    from datetime import datetime, timezone
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/data-range")
async def data_range():
    return {"min_date": "2019-10-01", "max_date": "2019-11-30"}
```

### `api/routers/overview.py`

Endpoint: `GET /api/overview?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Query `daily_metrics` table for the date range. Aggregate totals. Return:
```json
{
  "total_events": 12345678,
  "unique_users": 987654,
  "total_revenue": 4523187.50,
  "conversion_rate": 0.0342,
  "avg_order_value": 87.45,
  "total_views": 9876543,
  "total_carts": 876543,
  "total_purchases": 423187,
  "daily_trend": [
    {"date": "2019-10-01", "views": 123456, "carts": 12345, "purchases": 4231, "revenue": 98765.50}
  ]
}
```

SQL for aggregates uses `$1` and `$2` for start_date and end_date (required, never nullable).
SQL for daily trend: `SELECT date, total_views, total_carts, total_purchases, total_revenue FROM daily_metrics WHERE date >= $1 AND date <= $2 ORDER BY date`.

### `api/routers/funnel.py`

Endpoint: `GET /api/funnel?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&category=all`

When `category == "all"`: aggregate funnel_stats across all categories in range, sum views/carts/purchases, compute rates.
When `category` is specific: filter by that category.

Return:
```json
{
  "stages": [
    {"stage": "Views", "count": 9876543, "rate": 1.0},
    {"stage": "Cart Adds", "count": 876543, "rate": 0.0888},
    {"stage": "Purchases", "count": 423187, "rate": 0.0043}
  ],
  "categories": ["electronics", "computers", "appliances"],
  "view_to_cart_rate": 0.0888,
  "cart_to_purchase_rate": 0.0482,
  "overall_conversion": 0.0043,
  "top_abandonment": [
    {"category": "electronics", "abandonment_rate": 0.72, "abandoned_carts": 45678}
  ]
}
```

Category list comes from: `SELECT DISTINCT category FROM funnel_stats ORDER BY category`.

### `api/routers/products.py`

Three endpoints:

**`GET /api/products?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=20`**  
Query `top_products` (not date-filtered — these are global aggregates). Return top N by revenue.
```json
{"products": [{"product_id": 12345, "category": "electronics", "brand": "samsung", "price": 249.99, "views": 45678, "carts": 4321, "purchases": 1234, "revenue": 308426.66}]}
```

**`GET /api/brands?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=20`**  
Query `top_brands`. Return top N by revenue.
```json
{"brands": [{"brand": "samsung", "views": 876543, "carts": 87654, "purchases": 34567, "revenue": 8765432.10}]}
```

**`GET /api/categories?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`**  
Query `top_categories`. Return all, sorted by revenue desc.
```json
{"categories": [{"category": "electronics", "views": 3456789, "carts": 345678, "purchases": 123456, "revenue": 34567890.00}]}
```

### `api/routers/live.py`

**`GET /api/live/sessions`** — SSE endpoint
```python
from fastapi.responses import StreamingResponse
import asyncio, json

async def event_generator(db):
    while True:
        rows = await db.fetch("SELECT * FROM live_sessions ORDER BY updated_at DESC LIMIT 20")
        data = json.dumps([dict(r) for r in rows], default=str)
        yield f"data: {data}\n\n"
        await asyncio.sleep(2)

@router.get("/live/sessions")
async def live_sessions(db=Depends(get_db)):
    return StreamingResponse(event_generator(db), media_type="text/event-stream")
```

**`GET /api/live/events?limit=50`**  
Returns last N sessions from `live_sessions` ordered by `updated_at DESC`.

### `api/tests/conftest.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
def mock_db():
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=0)
    return conn

@pytest.fixture
async def client(mock_db):
    async def override_get_db():
        yield mock_db
    
    from database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

### `api/tests/test_overview.py`

```python
import pytest
from datetime import date

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_data_range(client):
    response = await client.get("/api/data-range")
    assert response.status_code == 200
    data = response.json()
    assert data["min_date"] == "2019-10-01"
    assert data["max_date"] == "2019-11-30"

@pytest.mark.asyncio
async def test_overview_empty(client, mock_db):
    mock_db.fetchrow.return_value = None
    mock_db.fetch.return_value = []
    response = await client.get("/api/overview?start_date=2019-10-01&end_date=2019-10-31")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_overview_missing_params(client):
    response = await client.get("/api/overview")
    assert response.status_code == 422
```

---

### `spark/jobs/batch_analytics.py`

- Creates SparkSession with master `spark://spark-master:7077`, appName `ClickstreamBatchAnalytics`
- Configures S3A for MinIO (read env vars: MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET)
- Reads CSV from MinIO `s3a://{bucket}/raw/events.csv` with explicit StructType schema:
  ```python
  from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, TimestampType
  schema = StructType([
      StructField("event_time", StringType(), True),
      StructField("event_type", StringType(), True),
      StructField("product_id", LongType(), True),
      StructField("category_id", LongType(), True),
      StructField("category_code", StringType(), True),
      StructField("brand", StringType(), True),
      StructField("price", DoubleType(), True),
      StructField("user_id", LongType(), True),
      StructField("user_session", StringType(), True),
  ])
  ```
- Parses `event_time` with `to_timestamp("event_time", "yyyy-MM-dd HH:mm:ss UTC")` → extract `date` column via `to_date()`
- Computes daily aggregations: total_events, unique_users, total_views, total_carts, total_purchases, total_revenue (sum price where event_type=purchase), conversion_rate (purchases/unique_users), avg_order_value (total_revenue/total_purchases)
- Writes to PostgreSQL `daily_metrics` table with JDBC mode `overwrite`, jdbc url `jdbc:postgresql://postgres:5432/{db}`
- Saves as Parquet to MinIO `s3a://{bucket}/processed/daily_metrics/` for downstream jobs

Also writes:
- `top_products`: group by product_id, category_code, brand, price → aggregate views/carts/purchases/revenue
- `top_categories`: group by root category (first segment of category_code, split on `.`)
- `top_brands`: group by brand

### `spark/jobs/funnel_analysis.py`

- Reads processed Parquet from MinIO `s3a://{bucket}/processed/daily_metrics/` or re-reads raw CSV
- Computes per-date, per-category: views, carts, purchases
- Derives view_to_cart_rate = carts/views, cart_to_purchase_rate = purchases/carts (handle division by zero with `when(views > 0, carts/views).otherwise(0)`)
- Writes to `funnel_stats` table with JDBC mode `overwrite`

### `spark/jobs/cart_abandonment.py`

- Groups sessions: find sessions that had `cart` event but NO `purchase` event (abandoned), vs sessions with both (converted)
- Computes per-date, per-root-category: abandoned_carts count, completed_purchases count, abandonment_rate
- Writes to `cart_abandonment` table with JDBC mode `overwrite`

### `spark/jobs/product_affinity.py`

- For each user_session, collect distinct product_ids viewed or carted
- Self-join sessions on product pairs (product_a < product_b to avoid duplicates)
- Count co-occurrences
- Compute lift: lift = (co_occurrences * total_sessions) / (count_a * count_b)
- Take top 10000 pairs by lift
- Write to `product_affinity` table with JDBC mode `overwrite`
- NOTE: This is computationally expensive; add a `--sample 0.1` argument to sample 10% of data for development

### `spark/jobs/prepare_mapreduce.py`

- Reads processed Parquet from MinIO
- Writes two CSV outputs to HDFS:
  1. `/user/hadoop/clickstream/csv/category_events/` — columns: category (root), event_type
  2. `/user/hadoop/clickstream/csv/brand_revenue/` — columns: brand, price (purchase events only)
- Use `df.write.mode("overwrite").csv(hdfs_path, header=False)` 
- HDFS path: `hdfs://namenode:9000/user/hadoop/clickstream/csv/...`

### `hadoop/mapreduce/category_events/mapper.py`

```python
#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split(',')
    if len(parts) < 2:
        continue
    category = parts[0].strip()
    event_type = parts[1].strip()
    if category and event_type:
        print(f"{category}\t{event_type}\t1")
```

### `hadoop/mapreduce/category_events/reducer.py`

```python
#!/usr/bin/env python3
import sys
from collections import defaultdict

counts: dict[tuple[str, str], int] = defaultdict(int)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split('\t')
    if len(parts) != 3:
        continue
    category, event_type, count_str = parts
    try:
        counts[(category, event_type)] += int(count_str)
    except ValueError:
        continue

for (category, event_type), count in sorted(counts.items()):
    print(f"{category}\t{event_type}\t{count}")
```

Similarly implement `brand_revenue/mapper.py` (emit `brand\tprice`) and `brand_revenue/reducer.py` (sum revenue per brand, count purchases).

### `hadoop/scripts/upload_to_hdfs.sh`

```bash
#!/bin/bash
set -euo pipefail

HADOOP_HOME=/opt/hadoop

echo "Creating HDFS directories..."
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /user/hadoop/clickstream/csv/category_events
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /user/hadoop/clickstream/csv/brand_revenue
$HADOOP_HOME/bin/hdfs dfs -mkdir -p /user/hadoop/clickstream/output

echo "HDFS directories created."
$HADOOP_HOME/bin/hdfs dfs -ls /user/hadoop/clickstream/
```

### `hadoop/scripts/run_mapreduce.sh`

```bash
#!/bin/bash
set -euo pipefail

HADOOP_HOME=/opt/hadoop
STREAMING_JAR=$(find $HADOOP_HOME -name "hadoop-streaming-*.jar" | head -1)

echo "Running category_events MapReduce..."
$HADOOP_HOME/bin/hdfs dfs -rm -r -f /user/hadoop/clickstream/output/category_events || true

$HADOOP_HOME/bin/hadoop jar "$STREAMING_JAR" \
  -input /user/hadoop/clickstream/csv/category_events \
  -output /user/hadoop/clickstream/output/category_events \
  -mapper /opt/hadoop/mapreduce/category_events/mapper.py \
  -reducer /opt/hadoop/mapreduce/category_events/reducer.py \
  -file /opt/hadoop/mapreduce/category_events/mapper.py \
  -file /opt/hadoop/mapreduce/category_events/reducer.py

echo "Running brand_revenue MapReduce..."
$HADOOP_HOME/bin/hdfs dfs -rm -r -f /user/hadoop/clickstream/output/brand_revenue || true

$HADOOP_HOME/bin/hadoop jar "$STREAMING_JAR" \
  -input /user/hadoop/clickstream/csv/brand_revenue \
  -output /user/hadoop/clickstream/output/brand_revenue \
  -mapper /opt/hadoop/mapreduce/brand_revenue/mapper.py \
  -reducer /opt/hadoop/mapreduce/brand_revenue/reducer.py \
  -file /opt/hadoop/mapreduce/brand_revenue/mapper.py \
  -file /opt/hadoop/mapreduce/brand_revenue/reducer.py

echo "MapReduce jobs complete."
$HADOOP_HOME/bin/hdfs dfs -ls /user/hadoop/clickstream/output/
```

---

### `kafka/producer/clickstream_producer.py`

- Reads raw CSV with `csv.DictReader` (standard library — no Spark needed)
- Sends events to Kafka topic `clickstream-events` with `kafka-python` (add `kafka-python==2.0.2` to producer requirements)
- Rate: configurable via `--rate` arg (default 100 events/second)
- Loops through dataset continuously (restart from beginning when EOF)
- Schema: serialize as JSON matching the event schema in CLAUDE.md
- Handles SIGINT gracefully (close producer cleanly)
- Reads env: KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_EVENTS, CSV path via `--csv-path` arg

### `spark/streaming/clickstream_consumer.py`

- SparkSession in local mode (for streaming): `SparkSession.builder.master("local[2]")`
- Reads from Kafka: `spark.readStream.format("kafka").option("kafka.bootstrap.servers", ...).option("subscribe", "clickstream-events")`
- Parses JSON value with schema matching event JSON structure
- Maintains session state: group by `user_session`, compute `event_count`, `has_cart`, `has_purchase`, `last_event_time`, `last_product_id`, `last_category`
- Uses `foreachBatch` to write to `live_sessions`:
  ```python
  def write_batch(batch_df, epoch_id):
      batch_df.write \
          .format("jdbc") \
          .option("url", jdbc_url) \
          .option("dbtable", "live_sessions") \
          .option("driver", "org.postgresql.Driver") \
          .mode("overwrite") \
          .option("truncate", "true") \
          .save()
  ```
- Trigger: `trigger(processingTime="5 seconds")`

---

### `airflow/dags/batch_pipeline.py`

DAG: `clickstream_batch_pipeline`
- Schedule: `@daily`
- Start date: `datetime(2019, 10, 1)`
- Catchup: False
- Tasks (in order, with dependencies):

```python
from airflow.providers.docker.operators.docker import DockerOperator
# OR use BashOperator with docker exec commands
```

Use `BashOperator` since Docker-in-Docker is complex. Tasks run `docker exec` on spark-master:

1. `spark_batch_analytics` — `docker exec spark-master spark-submit /spark/jobs/batch_analytics.py`
2. `spark_funnel_analysis` — same pattern
3. `spark_cart_abandonment`
4. `spark_product_affinity`
5. `spark_prepare_mapreduce`
6. `hadoop_mapreduce` — `docker exec namenode bash /hadoop/scripts/run_mapreduce.sh`

Dependencies: 1 → 2 → 3 → 4 → 5 → 6

### `airflow/requirements.txt`
```
apache-airflow-providers-docker==3.9.2
```

---

### `scripts/upload_to_minio.py`

```python
#!/usr/bin/env python3
"""Upload raw Kaggle CSV to MinIO."""
import os
import sys
import boto3
from botocore.client import Config

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "/data/events.csv"
    
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        config=Config(signature_version="s3v4"),
    )
    
    bucket = os.environ["MINIO_BUCKET"]
    
    # Create bucket if not exists
    existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    if bucket not in existing:
        s3.create_bucket(Bucket=bucket)
        print(f"Created bucket: {bucket}")
    
    print(f"Uploading {csv_path} to s3://{bucket}/raw/events.csv ...")
    s3.upload_file(csv_path, bucket, "raw/events.csv",
                   ExtraArgs={"ContentType": "text/csv"})
    print("Upload complete.")

if __name__ == "__main__":
    main()
```

### `scripts/load_sample.py`

Loads a random 1% sample of the raw CSV into MinIO as `raw/events_sample.csv` for development/testing. Takes same args as upload_to_minio.py but uses `pandas.read_csv(..., skiprows=...)` sampling logic.

---

### Frontend — React + TypeScript + Tailwind + Recharts

### `frontend/package.json`
```json
{
  "name": "clickstream-dashboard",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "recharts": "^2.13.3",
    "axios": "^1.7.9"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.7.2",
    "vite": "^6.0.5"
  }
}
```

### `frontend/src/api/client.ts`

```typescript
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface DataRange {
  min_date: string;
  max_date: string;
}

export interface OverviewData {
  total_events: number;
  unique_users: number;
  total_revenue: number;
  conversion_rate: number;
  avg_order_value: number;
  total_views: number;
  total_carts: number;
  total_purchases: number;
  daily_trend: Array<{
    date: string;
    views: number;
    carts: number;
    purchases: number;
    revenue: number;
  }>;
}

export interface FunnelData {
  stages: Array<{ stage: string; count: number; rate: number }>;
  categories: string[];
  view_to_cart_rate: number;
  cart_to_purchase_rate: number;
  overall_conversion: number;
  top_abandonment: Array<{ category: string; abandonment_rate: number; abandoned_carts: number }>;
}

export interface Product {
  product_id: number;
  category: string;
  brand: string;
  price: number;
  views: number;
  carts: number;
  purchases: number;
  revenue: number;
}

export interface Brand {
  brand: string;
  views: number;
  carts: number;
  purchases: number;
  revenue: number;
}

export interface Category {
  category: string;
  views: number;
  carts: number;
  purchases: number;
  revenue: number;
}

export interface LiveSession {
  session_id: string;
  user_id: number;
  last_event_time: string;
  event_count: number;
  has_cart: boolean;
  has_purchase: boolean;
  last_category: string;
}

// Formatters
export const fmtNum = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
};

export const fmtCurrency = (n: number): string =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);

export const fmtPercent = (n: number): string =>
  `${(n * 100).toFixed(2)}%`;

// API calls
export const getDataRange = (): Promise<DataRange> =>
  api.get('/data-range').then(r => r.data);

export const getOverview = (startDate: string, endDate: string): Promise<OverviewData> =>
  api.get('/overview', { params: { start_date: startDate, end_date: endDate } }).then(r => r.data);

export const getFunnel = (startDate: string, endDate: string, category = 'all'): Promise<FunnelData> =>
  api.get('/funnel', { params: { start_date: startDate, end_date: endDate, category } }).then(r => r.data);

export const getProducts = (startDate: string, endDate: string, limit = 20): Promise<{ products: Product[] }> =>
  api.get('/products', { params: { start_date: startDate, end_date: endDate, limit } }).then(r => r.data);

export const getBrands = (startDate: string, endDate: string, limit = 20): Promise<{ brands: Brand[] }> =>
  api.get('/brands', { params: { start_date: startDate, end_date: endDate, limit } }).then(r => r.data);

export const getCategories = (startDate: string, endDate: string): Promise<{ categories: Category[] }> =>
  api.get('/categories', { params: { start_date: startDate, end_date: endDate } }).then(r => r.data);

export const getLiveEvents = (limit = 50): Promise<LiveSession[]> =>
  api.get('/live/events', { params: { limit } }).then(r => r.data);
```

### `frontend/src/App.tsx`

React Router with 4 routes:
- `/` → Overview
- `/funnel` → FunnelAnalysis  
- `/products` → ProductAnalytics
- `/live` → LiveMonitor

Wrap in `<Layout>` component.

### `frontend/src/components/Layout.tsx`

Dark sidebar navigation (bg-gray-900) with links to all 4 pages. Page titles: "Overview", "Funnel Analysis", "Product Analytics", "Live Monitor". Each nav item shows an emoji icon + label.

### `frontend/src/components/KPICard.tsx`

```tsx
interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: number; // positive = up, negative = down
  color?: string; // tailwind bg class
}
```

Card with large value, title, optional trend arrow.

### `frontend/src/pages/Overview.tsx`

On mount: call `getDataRange()`, set default dates to last 30 days of data. Date picker inputs for start/end.

**KPI cards (top row, 4 cards):**
- Total Events (formatted with fmtNum)
- Unique Users (formatted)
- Total Revenue (formatted with fmtCurrency)
- Conversion Rate (formatted with fmtPercent)

**Daily trend chart** (AreaChart from recharts):
- X axis: date
- 3 areas: Views (blue), Cart Adds (orange), Purchases (green)
- Responsive container

**Second row KPIs:**
- Avg Order Value
- Total Views
- Total Cart Adds
- Total Purchases

### `frontend/src/pages/FunnelAnalysis.tsx`

- Date pickers (anchored to data range)
- Category selector dropdown (populated from funnel API `categories` array, plus "All Categories")
- **Funnel visualization** (custom SVG or BarChart in recharts):
  - 3 stages: Views → Cart Adds → Purchases
  - Show count (fmtNum) and conversion rate per stage
  - Use a horizontal funnel shape (wider bar for Views, narrower for Purchases)
- **Cart Abandonment table** (bottom): top 10 categories by abandonment rate — columns: Category, Abandoned Carts, Purchases, Abandonment Rate

### `frontend/src/pages/ProductAnalytics.tsx`

Three tabs: Products | Brands | Categories

**Products tab**: Table with columns: Rank, Product ID, Category, Brand, Price, Views, Cart Adds, Purchases, Revenue. Top 20 rows. Sortable by revenue (default).

**Brands tab**: BarChart (horizontal) — top 10 brands by revenue. Also a table below.

**Categories tab**: Treemap or PieChart + table of all categories by revenue.

### `frontend/src/pages/LiveMonitor.tsx`

- Connects to `/api/live/sessions` via `EventSource` on mount
- Displays real-time session table: Session ID (truncated), User ID, Last Event, Events Count, Has Cart (✓/✗), Has Purchase (✓/✗), Category
- Auto-scrolling list of last 20 active sessions
- Header: "Live Sessions" with green pulsing dot when connected, red when disconnected
- On component unmount, close `EventSource`
- **Reconnect logic**: if `EventSource` fires `onerror`, close it, wait (backoff: 1s → 2s → 4s → max 30s), reconnect

---

### `frontend/Dockerfile`

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://api:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        # SSE support
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

### `Makefile`

```makefile
.PHONY: help up down build logs ps \
        minio-upload hdfs-init \
        spark-batch spark-funnel spark-abandonment spark-affinity spark-prepare-mr \
        mapreduce-category mapreduce-brand mapreduce-load \
        kafka-produce spark-stream \
        pipeline-batch pipeline-all \
        lint typecheck test audit ci

help:
	@echo "ecommerce-clickstream-platform"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up               - Start all 13 Docker services"
	@echo "  make down             - Stop all services"
	@echo "  make build            - Rebuild Docker images (no cache)"
	@echo "  make logs             - Tail all service logs"
	@echo "  make ps               - Show service status"
	@echo ""
	@echo "Data Ingestion:"
	@echo "  make minio-upload     - Upload raw CSV to MinIO (set CSV_PATH env)"
	@echo "  make hdfs-init        - Create HDFS directory structure"
	@echo ""
	@echo "Spark Batch:"
	@echo "  make spark-batch      - Run batch_analytics.py"
	@echo "  make spark-funnel     - Run funnel_analysis.py"
	@echo "  make spark-abandonment - Run cart_abandonment.py"
	@echo "  make spark-affinity   - Run product_affinity.py (slow)"
	@echo "  make spark-prepare-mr - Run prepare_mapreduce.py (Parquet -> HDFS CSV)"
	@echo ""
	@echo "Hadoop MapReduce:"
	@echo "  make mapreduce-run    - Run all MapReduce jobs"
	@echo ""
	@echo "Live Pipeline:"
	@echo "  make kafka-produce    - Start clickstream Kafka producer"
	@echo "  make spark-stream     - Start Spark Streaming consumer"
	@echo ""
	@echo "Full Pipelines:"
	@echo "  make pipeline-batch   - Full batch pipeline (Spark + MapReduce)"
	@echo "  make pipeline-all     - Full pipeline + live streaming"
	@echo ""
	@echo "Quality:"
	@echo "  make lint             - Run ruff check"
	@echo "  make typecheck        - Run mypy --strict"
	@echo "  make test             - Run pytest"
	@echo "  make audit            - lint + typecheck + test"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

ps:
	docker compose ps

minio-upload:
	docker compose exec spark-master python3 /scripts/upload_to_minio.py $(CSV_PATH)

hdfs-init:
	docker compose exec namenode bash /hadoop/scripts/upload_to_hdfs.sh

spark-batch:
	docker compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
		/spark/jobs/batch_analytics.py

spark-funnel:
	docker compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
		/spark/jobs/funnel_analysis.py

spark-abandonment:
	docker compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
		/spark/jobs/cart_abandonment.py

spark-affinity:
	docker compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
		/spark/jobs/product_affinity.py

spark-prepare-mr:
	docker compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
		/spark/jobs/prepare_mapreduce.py

mapreduce-run:
	docker compose exec namenode bash /hadoop/scripts/run_mapreduce.sh

kafka-produce:
	docker compose exec spark-master python3 /kafka/producer/clickstream_producer.py \
		--csv-path /data/events.csv --rate 200

spark-stream:
	docker compose exec spark-master spark-submit \
		--master local[2] \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
		/spark/streaming/clickstream_consumer.py

pipeline-batch:
	$(MAKE) spark-batch
	$(MAKE) spark-funnel
	$(MAKE) spark-abandonment
	$(MAKE) spark-affinity
	$(MAKE) spark-prepare-mr
	$(MAKE) mapreduce-run

pipeline-all:
	$(MAKE) pipeline-batch
	$(MAKE) kafka-produce &
	$(MAKE) spark-stream

lint:
	cd api && pip install ruff --quiet && ruff check .

typecheck:
	cd api && pip install mypy --quiet && mypy . --strict

test:
	cd api && pip install pytest pytest-asyncio httpx --quiet && pytest tests/ -v

audit:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

ci:
	$(MAKE) audit
```

---

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install \
            fastapi==0.115.5 \
            asyncpg==0.30.0 \
            uvicorn==0.32.1 \
            pydantic==2.10.2 \
            python-dotenv==1.0.1 \
            redis==5.2.0 \
            pytest==8.3.4 \
            pytest-asyncio==0.24.0 \
            httpx==0.28.1 \
            mypy==1.13.0 \
            ruff==0.8.4 \
            types-requests==2.32.0.20241016
      
      - name: Lint with ruff
        run: ruff check api/
      
      - name: Type check with mypy
        run: mypy api/ --strict --ignore-missing-imports
      
      - name: Run tests
        run: pytest api/tests/ -v --asyncio-mode=auto
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
```

---

### `terraform/aws/main.tf`

Portfolio-grade Terraform for AWS:
- Provider: aws, region from var
- S3 bucket for raw data: `clickstream-raw-{random_id}`
- RDS PostgreSQL instance (db.t3.micro)
- ECS cluster for API service
- ECR repository for API image
- VPC with public/private subnets
- Security groups
- All tagged with `Project = "ecommerce-clickstream-platform"`, `Owner = "hassan-zaib-hayat"`

### `terraform/gcp/main.tf`

Portfolio-grade Terraform for GCP:
- Provider: google, project from var
- GCS bucket for raw data
- Cloud SQL PostgreSQL instance
- Cloud Run service for API
- Artifact Registry for Docker images
- All labeled with `project = "ecommerce-clickstream"`, `owner = "hassan-zaib-hayat"`

---

### `README.md`

Comprehensive README with:
1. Project title + badges (build passing, Python 3.11, Spark 3.5, Kafka 3.9)
2. Architecture diagram (ASCII)
3. Dataset description
4. Tech stack table
5. Prerequisites section
6. Quick start (numbered steps)
7. Service URLs table
8. Data pipeline explanation (each stage)
9. Dashboard pages description
10. Makefile reference (all targets)
11. Development notes
12. License: MIT
13. Author: Hassan Zaib Hayat

---

## GENERATION ORDER

Generate files in this exact order to avoid forward-reference issues:

1. `.env.example`, `.gitignore`, `.dockerignore`
2. `scripts/init_db.sql`
3. `docker/hadoop/core-site.xml`, `hdfs-site.xml`, `yarn-site.xml`, `mapred-site.xml`
4. `docker/hadoop/bootstrap-namenode.sh`, `bootstrap-datanode.sh`
5. `docker/hadoop/Dockerfile`
6. `docker/kafka/start-kafka.sh`, `docker/kafka/Dockerfile`
7. `hadoop/mapreduce/` (all 4 mapper/reducer files)
8. `hadoop/scripts/` (both shell scripts)
9. `api/requirements.txt`, `api/Dockerfile`
10. `api/database.py`, `api/main.py`
11. `api/routers/__init__.py`, `overview.py`, `funnel.py`, `products.py`, `live.py`
12. `api/tests/conftest.py`, `test_overview.py`, `test_funnel.py`, `test_products.py`
13. `scripts/upload_to_minio.py`, `scripts/load_sample.py`
14. `spark/jobs/` (all 5 jobs)
15. `spark/streaming/clickstream_consumer.py`
16. `kafka/producer/clickstream_producer.py`
17. `airflow/dags/batch_pipeline.py`, `airflow/requirements.txt`
18. `frontend/package.json`, `tsconfig.json`, `vite.config.ts`, `tailwind.config.js`, `postcss.config.js`
19. `frontend/src/index.css`, `main.tsx`, `App.tsx`
20. `frontend/src/api/client.ts`
21. `frontend/src/components/Layout.tsx`, `KPICard.tsx`
22. `frontend/src/pages/Overview.tsx`, `FunnelAnalysis.tsx`, `ProductAnalytics.tsx`, `LiveMonitor.tsx`
23. `frontend/Dockerfile`, `nginx.conf`
24. `terraform/aws/` (main.tf, variables.tf, outputs.tf)
25. `terraform/gcp/` (main.tf, variables.tf, outputs.tf)
26. `docker-compose.yml`
27. `Makefile`
28. `.github/workflows/ci.yml`
29. `README.md`

---

## FINAL VERIFICATION CHECKLIST

Before completing, verify:
- [ ] Every Docker image tag is pinned (no `:latest`)
- [ ] Kafka uses `apache/kafka:3.9.0` with KRaft via `start-kafka.sh`
- [ ] Hadoop Dockerfile installs python3 via apt-get
- [ ] bootstrap-namenode.sh starts BOTH hdfs namenode AND yarn resourcemanager
- [ ] bootstrap-datanode.sh starts BOTH hdfs datanode AND yarn nodemanager
- [ ] MapReduce scripts are COPYed in Dockerfile (available on both nodes)
- [ ] YARN yarn-site.xml has `yarn.nodemanager.resource.memory-mb=8192`
- [ ] prepare_mapreduce.py writes CSV (not Parquet) to HDFS
- [ ] No asyncpg `$1 IS NULL OR` patterns anywhere in API code
- [ ] Spark Streaming uses `mode("overwrite").option("truncate", "true")`
- [ ] Frontend calls `/api/data-range` and anchors date pickers to result
- [ ] All number displays use fmtNum/fmtCurrency/fmtPercent formatters
- [ ] Makefile uses `@echo` for help, no grep/sed/awk
- [ ] All bash scripts have `set -euo pipefail` on line 2
- [ ] `.env` and `docker-compose.override.yml` in `.gitignore`
- [ ] CI installs `httpx`, `types-requests`, `pytest-asyncio`
- [ ] nginx.conf proxies `/api/` to `http://api:8000/api/`
- [ ] `proxy_buffering off` in nginx for SSE support
- [ ] All Spark submit commands include `--packages` with kafka + postgresql jars
- [ ] Terraform resources tagged with project and owner
