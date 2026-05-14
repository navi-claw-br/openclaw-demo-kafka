#!/usr/bin/env python3
"""
Optimization Agent 📈 — Analisa o cluster OpenShift buscando oportunidades
de otimização de recursos, custo e performance.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/root/.openclaw/workspace/skills/kafka-base")

from config import (
    TOPIC_EVENTS,
    TOPIC_AGENT_EVENTS,
    TOPIC_REASONING,
    TOPIC_COMMANDS,
)
from kafka_client import create_consumer, create_producer, publish_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] 📈  %(message)s",
)
log = logging.getLogger("optimization-agent")

AGENT_NAME = "optimization-agent"
ANALYSIS_INTERVAL = 60  # segundos entre análises


def run_oc(cmd: list[str]) -> dict | None:
    """Executa um comando oc e retorna o JSON parseado."""
    full_cmd = ["oc"] + cmd + ["-o", "json"]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        log.warning("Erro ao executar oc %s: %s", cmd, e)
    return None


def analyze_pods() -> list[dict]:
    """Analisa todos os pods em busca de problemas de dimensionamento."""
    findings = []
    data = run_oc(["get", "pods", "--all-namespaces"])
    if not data:
        return findings

    for item in data.get("items", []):
        name = item["metadata"]["name"]
        namespace = item["metadata"]["namespace"]
        containers = item.get("spec", {}).get("containers", [])

        for c in containers:
            resources = c.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})

            # Pod sem requests
            if not requests:
                findings.append({
                    "type": "missing_requests",
                    "severity": "warning",
                    "pod": name,
                    "namespace": namespace,
                    "container": c["name"],
                    "detail": "Container sem resource requests definidos",
                })
                continue

            # Pod sem limits
            if not limits:
                findings.append({
                    "type": "missing_limits",
                    "severity": "warning",
                    "pod": name,
                    "namespace": namespace,
                    "container": c["name"],
                    "detail": "Container sem resource limits definidos",
                })
                continue

            # CPU limits >> requests (> 5x)
            cpu_req = _parse_resource(requests.get("cpu", "0"))
            cpu_lim = _parse_resource(limits.get("cpu", "0"))
            if cpu_req > 0 and cpu_lim / cpu_req > 5:
                findings.append({
                    "type": "unbalanced_cpu",
                    "severity": "info",
                    "pod": name,
                    "namespace": namespace,
                    "container": c["name"],
                    "detail": f"CPU limit={limits['cpu']} é {cpu_lim/cpu_req:.0f}x o request={requests['cpu']}",
                    "suggestion": f"Ajuste limit para ~2x o request ({requests['cpu']})",
                })

            # Memory limits >> requests (> 3x)
            mem_req = _parse_memory(requests.get("memory", "0"))
            mem_lim = _parse_memory(limits.get("memory", "0"))
            if mem_req > 0 and mem_lim / mem_req > 3:
                findings.append({
                    "type": "unbalanced_memory",
                    "severity": "info",
                    "pod": name,
                    "namespace": namespace,
                    "container": c["name"],
                    "detail": f"Memory limit={limits['memory']} é {mem_lim/mem_req:.0f}x o request={requests['memory']}",
                    "suggestion": f"Ajuste limit para ~1.5x o request ({requests['memory']})",
                })

    return findings


def analyze_nodes() -> list[dict]:
    """Analisa utilização dos nós."""
    findings = []
    data = run_oc(["get", "nodes"])
    if not data:
        return findings

    total = len(data.get("items", []))
    if total < 3:
        return findings  # cluster pequeno demais para análise de node pool

    # Verifica nós com taints que podem estar subutilizados
    for item in data.get("items", []):
        name = item["metadata"]["name"]
        taints = item.get("spec", {}).get("taints", [])
        if not taints:
            continue
        # Nó dedicado a workload específica
        for t in taints:
            if t.get("effect") == "NoSchedule":
                findings.append({
                    "type": "dedicated_node",
                    "severity": "info",
                    "node": name,
                    "detail": f"Nó com taint NoSchedule (key={t.get('key')}) — verificar utilização",
                })

    return findings


def analyze_scaling() -> list[dict]:
    """Analisa deployments sem HPA."""
    findings = []
    data = run_oc(["get", "deployments", "--all-namespaces"])
    if not data:
        return findings

    # Lista HPAs existentes
    hpa_data = run_oc(["get", "hpa", "--all-namespaces"])
    hpa_targets = set()
    if hpa_data:
        for item in hpa_data.get("items", []):
            ref = item.get("spec", {}).get("scaleTargetRef", {})
            hpa_targets.add(f"{ref.get('kind', '')}/{ref.get('name', '')}")

    for item in data.get("items", []):
        name = item["metadata"]["name"]
        namespace = item["metadata"]["namespace"]
        replicas = item.get("spec", {}).get("replicas", 1)
        target = f"Deployment/{name}"

        if target not in hpa_targets and replicas >= 3:
            findings.append({
                "type": "no_hpa",
                "severity": "info",
                "deployment": name,
                "namespace": namespace,
                "replicas": replicas,
                "detail": f"Deployment com {replicas} réplicas sem HPA",
                "suggestion": "Considere adicionar HPA baseado em CPU/memória",
            })

    return findings


def _parse_resource(val: str) -> float:
    """Converte valor de CPU para número (cores)."""
    if not val or val == "0":
        return 0.0
    if val.endswith("m"):
        return float(val[:-1]) / 1000
    return float(val)


def _parse_memory(val: str) -> float:
    """Converte valor de memória para bytes."""
    if not val or val == "0":
        return 0.0
    multipliers = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4, "k": 1000, "M": 10**6, "G": 10**9, "T": 10**12}
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            return float(val[:-len(suffix)]) * mult
    return float(val)


def run_optimization_cycle(producer) -> list[dict]:
    """Executa um ciclo completo de análise."""
    log.info("🔍 Iniciando ciclo de otimização...")
    all_findings = []

    all_findings.extend(analyze_pods())
    all_findings.extend(analyze_nodes())
    all_findings.extend(analyze_scaling())

    if not all_findings:
        log.info("✅ Nenhuma oportunidade de otimização encontrada.")
        return []

    for finding in all_findings:
        event = {
            "source": AGENT_NAME,
            "type": "optimization_finding",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **finding,
        }

        # Determina severidade para o tópico
        topic = TOPIC_REASONING
        publish_event(producer, topic, key=AGENT_NAME, event=event)

        emoji = "🔴" if finding.get("severity") == "critical" else "🟡" if finding.get("severity") == "warning" else "ℹ️"
        log.info("%s %s: %s", emoji, finding["type"], finding.get("detail", ""))

    return all_findings


def main():
    log.info("=" * 50)
    log.info("Optimization Agent 📈 iniciado")
    log.info("Intervalo de análise: %ss", ANALYSIS_INTERVAL)
    log.info("=" * 50)

    producer = create_producer()
    try:
        while True:
            run_optimization_cycle(producer)
            time.sleep(ANALYSIS_INTERVAL)
    except KeyboardInterrupt:
        log.info("Optimization Agent encerrado.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
