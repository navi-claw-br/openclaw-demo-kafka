#!/usr/bin/env python3
"""
Security Agent 🛡️ — Monitora o cluster OpenShift via Kafka e detecta
ameaças de segurança, acessos suspeitos e violações de política.
"""

import json
import logging
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/root/.openclaw/workspace/skills/kafka-base")

from config import (
    TOPIC_ALERTS,
    TOPIC_COMMANDS,
    TOPIC_EVENTS,
    TOPIC_REASONING,
)
from kafka_client import create_consumer, create_producer, analyze_message, publish_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] 🛡️  %(message)s",
)
log = logging.getLogger("security-agent")

# Palavras-chave que disparam análise de segurança
SECURITY_KEYWORDS = [
    "failed", "error", "unauthorized", "forbidden",
    "invalid", "security", "policy", "violation",
    "denied", "rejected", "attack", "breach",
    "privilege", "rbac", "podsecurity",
]

AGENT_NAME = "security-agent"


def is_security_event(value: dict) -> bool:
    """Verifica se o evento é relacionado a segurança."""
    reason = (value.get("reason") or value.get("message") or "").lower()
    return any(kw in reason for kw in SECURITY_KEYWORDS)


def get_cluster_context(value: dict) -> dict:
    """Consulta o cluster OpenShift para contexto adicional."""
    involved = value.get("involvedObject", {}) or {}
    kind = involved.get("kind", "")
    name = involved.get("name", "")
    namespace = involved.get("namespace", "")

    context = {}
    if not name:
        return context

    try:
        if kind == "Pod":
            cmd = ["oc", "get", "pod", name, "-n", namespace, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                pod_data = json.loads(result.stdout)
                container_statuses = pod_data.get("status", {}).get("containerStatuses", [])
                context["pod_status"] = pod_data.get("status", {}).get("phase")
                context["container_states"] = [
                    {"name": c["name"], "state": list(c.get("state", {}).keys())}
                    for c in container_statuses
                ]

        # Últimos eventos do namespace
        ev_cmd = ["oc", "get", "events", "-n", namespace, "--sort-by=.lastTimestamp", "-o", "json"]
        ev_result = subprocess.run(ev_cmd, capture_output=True, text=True, timeout=10)
        if ev_result.returncode == 0:
            events_data = json.loads(ev_result.stdout)
            context["recent_events"] = [
                {"reason": e.get("reason"), "message": e.get("message")}
                for e in events_data.get("items", [])[:5]
            ]
    except Exception as e:
        log.warning("Erro ao consultar cluster: %s", e)

    return context


def analyze_security(value: dict) -> dict:
    """Analisa um evento de segurança e produz recomendação."""
    analysis = analyze_message(value)
    context = get_cluster_context(value)
    reason = value.get("reason", "Unknown")
    message = value.get("message", "")

    severity = "critical" if any(w in reason.lower() for w in ["failed", "error", "breach"]) else \
               "warning" if any(w in reason.lower() for w in ["unauthorized", "forbidden", "denied", "violation"]) else \
               "info"

    recommendation = _build_recommendation(reason, message, analysis, context)

    return {
        "source": AGENT_NAME,
        "type": "security_analysis",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "reason": reason,
        "message": message,
        "analysis": analysis,
        "cluster_context": context,
        "recommendation": recommendation,
    }


def _build_recommendation(reason: str, message: str, analysis: dict, context: dict) -> str:
    """Gera uma recomendação legível baseada na análise."""
    r = reason.lower()

    if "unauthorized" in r or "forbidden" in r:
        return (
            f"Acesso não autorizado detectado para {analysis.get('name', 'recurso')} "
            f"no namespace {analysis.get('namespace', 'N/A')}. "
            "Verifique RBAC e roles do service account envolvido."
        )
    if "failed" in r:
        return (
            f"Falha em operação: {message}. "
            "Revise logs e eventos do recurso para identificar causa raiz."
        )
    if "violation" in r or "policy" in r:
        return (
            f"Violacão de política: {message}. "
            "Verifique PodSecurity, NetworkPolicy e OPA/Gatekeeper."
        )
    return f"Evento de segurança registrado: {message}. Monitore o ambiente."


def handle_message(key: str, value: dict):
    """Callback principal para mensagens recebidas."""
    if not is_security_event(value):
        return

    log.info("🔴 Evento de segurança detectado: %s", value.get("reason"))
    analysis = analyze_security(value)

    producer = create_producer()
    try:
        publish_event(producer, TOPIC_REASONING, key=AGENT_NAME, event=analysis)
        log.info("✅ Análise publicada em %s", TOPIC_REASONING)
    finally:
        producer.close()


def main():
    log.info("=" * 50)
    log.info("Security Agent 🛡️  iniciado")
    log.info("Escutando: %s", TOPIC_ALERTS)
    log.info("=" * 50)

    consumer = create_consumer(TOPIC_ALERTS, group_id=AGENT_NAME)
    try:
        for msg in consumer:
            handle_message(msg.key, msg.value)
    except KeyboardInterrupt:
        log.info("Security Agent encerrado.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
