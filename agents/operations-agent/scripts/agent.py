#!/usr/bin/env python3
"""
Operations Agent 🔧 — Self-healing de clusters OpenShift.
Escuta alertas do Kafka, diagnostica incidentes e executa ações corretivas.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/root/.openclaw/workspace/skills/kafka-base")

from config import TOPIC_ALERTS, TOPIC_COMMANDS, TOPIC_REASONING
from kafka_client import create_consumer, create_producer, publish_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] 🔧  %(message)s",
)
log = logging.getLogger("operations-agent")

AGENT_NAME = "operations-agent"

# Padrões de falha operacional e suas ações corretivas
FAILURE_PATTERNS = {
    "crashloopbackoff": {
        "severity": "critical",
        "action": "rollout_restart",
        "message": "Pod em CrashLoopBackOff — executando rollout restart",
    },
    "imagepullbackoff": {
        "severity": "critical",
        "action": "check_image",
        "message": "Falha ao puxar imagem — verificar se a imagem existe e o registry",
    },
    "oomkill": {
        "severity": "critical",
        "action": "increase_limits",
        "message": "Pod morto por OOM — aumentar resource limits de memória",
    },
    "nodenotready": {
        "severity": "critical",
        "action": "investigate_node",
        "message": "Nó não está Ready — investigar e possivelmente drenar",
    },
    "backoff": {
        "severity": "warning",
        "action": "monitor",
        "message": "BackOff detectado — monitorar situação",
    },
    "unhealthy": {
        "severity": "warning",
        "action": "check_probes",
        "message": "Probe de saúde falhando — verificar liveness/readiness",
    },
    "failed": {
        "severity": "warning",
        "action": "investigate",
        "message": "Falha em operação — investigar causa",
    },
}


def diagnose(value: dict) -> dict | None:
    """Analisa um alerta e retorna diagnóstico e ação corretiva."""
    reason = (value.get("reason") or value.get("message") or "").lower()
    involved = value.get("involvedObject", {}) or {}
    kind = involved.get("kind", "")
    name = involved.get("name", "")
    namespace = involved.get("namespace", "")

    for pattern, info in FAILURE_PATTERNS.items():
        if pattern in reason:
            return {
                "source": AGENT_NAME,
                "type": "diagnosis",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": info["severity"],
                "pattern": pattern,
                "action": info["action"],
                "message": info["message"],
                "resource": {"kind": kind, "name": name, "namespace": namespace},
                "original_reason": value.get("reason"),
                "original_message": value.get("message"),
            }

    return None


def execute_action(diagnosis: dict) -> dict:
    """Executa a ação corretiva recomendada."""
    action = diagnosis["action"]
    resource = diagnosis["resource"]
    ns = resource["namespace"]
    name = resource["name"]

    result = {"action": action, "status": "executed", "details": ""}

    try:
        if action == "rollout_restart" and ns and name:
            # Extrai o deployment do nome do pod: pod-name → deployment-name
            cmd = ["oc", "rollout", "restart", f"deployment/{name}", "-n", ns]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            result["details"] = r.stdout.strip() or r.stderr.strip()

        elif action == "investigate":
            cmd = ["oc", "describe", resource["kind"].lower(), name, "-n", ns] if ns else ["oc", "describe", resource["kind"].lower(), name]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            result["details"] = r.stdout[:300] if r.stdout else r.stderr[:300]

        else:
            result["status"] = "requires_manual"
            result["details"] = f"Ação '{action}' requer intervenção manual"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["details"] = "Comando excedeu 15s de timeout"
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)

    return result


def handle_alert(key: str, value: dict):
    """Processa um alerta do Kafka."""
    diagnosis = diagnose(value)
    if not diagnosis:
        return

    log.info("🔴 Alerta detectado: %s — %s", diagnosis["pattern"], diagnosis["message"])

    # Publica diagnóstico
    producer = create_producer()
    try:
        publish_event(producer, TOPIC_REASONING, key=AGENT_NAME, event=diagnosis)

        # Executa ação se for critical
        if diagnosis["severity"] == "critical":
            result = execute_action(diagnosis)
            diagnosis["action_result"] = result
            publish_event(producer, TOPIC_COMMANDS, key=AGENT_NAME, event=diagnosis)
            log.info("✅ Ação executada: %s → %s", result["action"], result["status"])
    finally:
        producer.close()


def main():
    log.info("=" * 50)
    log.info("Operations Agent 🔧 iniciado")
    log.info("Escutando: %s", TOPIC_ALERTS)
    log.info("=" * 50)

    consumer = create_consumer(TOPIC_ALERTS, group_id=AGENT_NAME)
    try:
        for msg in consumer:
            handle_alert(msg.key, msg.value)
    except KeyboardInterrupt:
        log.info("Operations Agent encerrado.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
