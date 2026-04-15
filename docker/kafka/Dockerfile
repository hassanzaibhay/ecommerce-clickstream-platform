FROM apache/kafka:3.9.0
COPY docker/kafka/start-kafka.sh /opt/kafka/start-kafka.sh
USER root
RUN chmod +x /opt/kafka/start-kafka.sh
USER appuser
CMD ["bash", "/opt/kafka/start-kafka.sh"]
