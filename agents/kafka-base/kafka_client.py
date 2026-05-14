"""
Cliente Kafka base compartilhado por todos os agentes.
Requires: pip install kafka-python
"""

import json
import logging
from typing import Callable, Any
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

from skills.kafka_base.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CLIENT_ID,
    POLL_TIMEOUT,
)

log = logging.getLogger(__name__)


def create_consumer(topic: str | list[str], group_id: str | None = None) -> KafkaConsumer:
    """Cria um consumer Kafka para um ou mais tópicos."""
    try:
        consumer = KafkaConsumer(
            *([topic] if isinstance(topic, str) else topic),
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id or f"{KAFKA_CLIENT_ID}-{topic}" if isinstance(topic, str) else KAFKA_CLIENT_ID,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
            key_deserializer=lambda v: v.decode("utf-8") if v else None,
            session_timeout_ms=30000,
            heartbeat_interval_ms=3000,
        )
        log.info("Consumer conectado a %s → tópico(s): %s", KAFKA_BOOTSTRAP_SERVERS, topic)
        return consumer
    except NoBrokersAvailable:
        log.error("Nenhum broker disponível em %s", KAFKA_BOOTSTRAP_SERVERS)
        raise


def create_producer() -> KafkaProducer:
    """Cria um producer Kafka."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
        )
        log.info("Producer conectado a %s", KAFKA_BOOTSTRAP_SERVERS)
        return producer
    except NoBrokersAvailable:
        log.error("Nenhum broker disponível em %s", KAFKA_BOOTSTRAP_SERVERS)
        raise


def publish_event(producer: KafkaProducer, topic: str, key: str, event: dict):
    """Publica um evento JSON em um tópico Kafka."""
    future = producer.send(topic, key=key, value=event)
    result = future.get(timeout=10)
    log.debug("Evento publicado em %s [key=%s]: offset=%s", topic, key, result.offset)
    return result


def subscribe_topic(
    consumer: KafkaConsumer,
    callback: Callable[[str, dict], Any],
    topics_override: list[str] | None = None,
):
    """Escuta mensagens de um consumer e chama callback(key, value) para cada uma."""
    topics = topics_override or list(consumer.topics())  # fallback
    log.info("Assinando: %s", topics)
    try:
        for msg in consumer:
            key = msg.key
            value = msg.value
            if value is None:
                continue
            try:
                callback(key, value)
            except Exception:
                log.exception("Erro no callback para msg key=%s", key)
    except KeyboardInterrupt:
        log.info("Consumer encerrado via Ctrl+C")
    finally:
        consumer.close()


def analyze_message(value: dict) -> dict:
    """
    Análise básica de uma mensagem.
    Retorna dict com metadados extraídos: severity, category, resource, reason.
    """
    reason = (value.get("reason") or value.get("message") or "").lower()
    kind = (value.get("involvedObject", {}) or {}).get("kind", "") if isinstance(value.get("involvedObject"), dict) else ""

    severity = "info"
    category = "unknown"
    if any(w in reason for w in ["error", "failed", "crash", "oom", "unhealthy"]):
        severity = "critical"
    elif any(w in reason for w in ["warning", "backoff", "unauthorized", "forbidden"]):
        severity = "warning"
    elif any(w in reason for w in ["created", "started", "normal"]):
        severity = "info"

    if kind in ("Pod", "Deployment", "StatefulSet", "DaemonSet"):
        category = "workload"
    elif kind in ("Node",):
        category = "infra"
    elif kind in ("ConfigMap", "Secret"):
        category = "config"

    return {
        "severity": severity,
        "category": category,
        "resource_kind": kind,
        "reason_raw": reason,
        "name": (value.get("involvedObject", {}) or {}).get("name", ""),
        "namespace": (value.get("involvedObject", {}) or {}).get("namespace", ""),
    }
