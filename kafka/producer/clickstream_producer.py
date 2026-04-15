#!/usr/bin/env python3
"""Kafka producer that simulates live clickstream events from CSV data."""
import argparse
import csv
import json
import os
import signal
import sys
import time

from kafka import KafkaProducer


def main() -> None:
    parser = argparse.ArgumentParser(description="Clickstream Kafka Producer")
    parser.add_argument("--csv-path", default="/data/events.csv", help="Path to CSV file")
    parser.add_argument("--rate", type=int, default=100, help="Events per second")
    args = parser.parse_args()

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.environ.get("KAFKA_TOPIC_EVENTS", "clickstream-events")

    producer = KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
    )

    running = True

    def shutdown(signum, frame):
        nonlocal running
        running = False
        print("\nShutting down producer...")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    interval = 1.0 / args.rate if args.rate > 0 else 0.01
    total_sent = 0

    print(f"Starting producer: {args.csv_path} -> {topic} @ {args.rate} events/sec")

    while running:
        try:
            with open(args.csv_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not running:
                        break

                    event = {
                        "event_time": row.get("event_time", ""),
                        "event_type": row.get("event_type", ""),
                        "product_id": int(row["product_id"]) if row.get("product_id") else 0,
                        "category_id": int(row["category_id"]) if row.get("category_id") else 0,
                        "category_code": row.get("category_code", ""),
                        "brand": row.get("brand", ""),
                        "price": float(row["price"]) if row.get("price") else 0.0,
                        "user_id": int(row["user_id"]) if row.get("user_id") else 0,
                        "user_session": row.get("user_session", ""),
                    }

                    producer.send(topic, value=event)
                    total_sent += 1

                    if total_sent % 1000 == 0:
                        print(f"Sent {total_sent} events...")

                    time.sleep(interval)

            print(f"Reached EOF, looping back to start... (total sent: {total_sent})")
        except FileNotFoundError:
            print(f"ERROR: CSV file not found: {args.csv_path}")
            sys.exit(1)

    producer.flush()
    producer.close()
    print(f"Producer stopped. Total events sent: {total_sent}")


if __name__ == "__main__":
    main()
