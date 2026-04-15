.PHONY: help up down build build-clean build-hadoop build-app logs ps \
        minio-upload hdfs-init \
        spark-batch spark-funnel spark-abandonment spark-affinity spark-prepare-mr \
        mapreduce-run \
        kafka-produce spark-stream \
        pipeline-batch pipeline-all \
        lint typecheck test audit ci

help:
	@echo ""
	@echo "ecommerce-clickstream-platform"
	@echo "================================"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up                - Start all 13 Docker services"
	@echo "  make down              - Stop all services"
	@echo "  make build             - Rebuild all Docker images (with cache)"
	@echo "  make build-clean       - Rebuild all Docker images (no cache)"
	@echo "  make build-hadoop      - Rebuild only namenode/datanode images"
	@echo "  make build-app         - Rebuild kafka/api/frontend images"
	@echo "  make logs              - Tail all service logs"
	@echo "  make ps                - Show service status"
	@echo ""
	@echo "Data Ingestion:"
	@echo "  make minio-upload      - Upload raw CSV to MinIO (set CSV_PATH)"
	@echo "  make hdfs-init         - Create HDFS directory structure"
	@echo ""
	@echo "Spark Batch:"
	@echo "  make spark-batch       - Run batch_analytics.py"
	@echo "  make spark-funnel      - Run funnel_analysis.py"
	@echo "  make spark-abandonment - Run cart_abandonment.py"
	@echo "  make spark-affinity    - Run product_affinity.py (slow)"
	@echo "  make spark-prepare-mr  - Run prepare_mapreduce.py (Parquet -> HDFS CSV)"
	@echo ""
	@echo "Hadoop MapReduce:"
	@echo "  make mapreduce-run     - Run all MapReduce jobs"
	@echo ""
	@echo "Live Pipeline:"
	@echo "  make kafka-produce     - Start clickstream Kafka producer"
	@echo "  make spark-stream      - Start Spark Streaming consumer"
	@echo ""
	@echo "Full Pipelines:"
	@echo "  make pipeline-batch    - Full batch pipeline (Spark + MapReduce)"
	@echo "  make pipeline-all      - Full pipeline + live streaming"
	@echo ""
	@echo "Quality:"
	@echo "  make lint              - Run ruff check"
	@echo "  make typecheck         - Run mypy --strict"
	@echo "  make test              - Run pytest"
	@echo "  make audit             - lint + typecheck + test"

up:
	docker compose up -d

down:
	docker compose down

build:
	bash scripts/build.sh

build-clean:
	bash scripts/build.sh --no-cache

build-hadoop:
	bash -c "DOCKER_BUILDKIT=1 docker compose build --no-cache namenode datanode"

build-app:
	bash -c "DOCKER_BUILDKIT=1 docker compose build --no-cache kafka api frontend spark-master spark-worker"

logs:
	docker compose logs -f

ps:
	docker compose ps

minio-upload:
	docker compose exec spark-master python3 /scripts/upload_to_minio.py $(CSV_PATH)

hdfs-init:
	docker compose exec -u hadoop namenode bash -c "bash /hadoop/scripts/upload_to_hdfs.sh"

spark-batch:
	bash scripts/spark-submit.sh /spark/jobs/batch_analytics.py

spark-funnel:
	bash scripts/spark-submit.sh /spark/jobs/funnel_analysis.py

spark-abandonment:
	bash scripts/spark-submit.sh /spark/jobs/cart_abandonment.py

spark-affinity:
	bash scripts/spark-submit.sh /spark/jobs/product_affinity.py

spark-prepare-mr:
	bash scripts/spark-submit.sh /spark/jobs/prepare_mapreduce.py

mapreduce-run:
	docker compose exec -u hadoop namenode bash -c "bash /hadoop/scripts/run_mapreduce.sh"

kafka-produce:
	docker compose exec spark-master python3 /kafka/producer/clickstream_producer.py \
		--csv-path /data/events.csv --rate 200

spark-stream:
	bash scripts/spark-submit.sh /spark/streaming/clickstream_consumer.py --master local[2]

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
	docker compose exec api sh -c "pip install --quiet ruff==0.8.4 && ruff check /app"

typecheck:
	docker compose exec api sh -c "pip install --quiet mypy==1.13.0 types-requests==2.32.0.20241016 && mypy /app --strict --ignore-missing-imports"

test:
	docker compose exec api sh -c "pip install --quiet pytest==8.3.4 pytest-asyncio==0.24.0 httpx==0.28.1 && PYTHONPATH=/app pytest /app/tests/ -v --asyncio-mode=auto -o asyncio_default_fixture_loop_scope=function"

audit:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

ci:
	$(MAKE) audit
