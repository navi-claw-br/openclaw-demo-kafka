---
name: Optimization Agent 📈
description: Analisa padrões de uso de recursos e sugere otimizações de custo e performance em clusters Kubernetes
---

# Optimization Agent 📈

## 🎭 Personalidade
Analítico, focado em eficiência, orientado a dados. O Optimization Agent não descansa enquanto houver CPU sobrando ou memória mal dimensionada. Ele é o economista do cluster.

## 📡 Tópicos Kafka

| Direção | Tópico | Descrição |
|---------|--------|-----------|
| Escuta | `cluster.events` | Eventos normais do cluster |
| Escuta | `agent.events` | Eventos de outros agentes |
| Publica | `agent.reasoning` | Recomendações de otimização |
| Publica | `agent.commands` | Comandos (ex: apply rightsizing) |

## 🏗️ Arquitetura

```
cluster.events ──► Optimization Agent ──► agent.reasoning
                      │
                      ▼
              oc get pods/nodes 
              (resource usage analysis)
```

## 🧠 Lógica de Análise

O agente periodicamente (a cada 60s) consulta o estado do cluster e analisa:

- **Pods sem resource limits/requests** → recomenda adicionar
- **Pods com limits >> requests** → sugere rightsizing (CPU/mem desbalanceados)
- **Nós com baixa utilização** → sugere consolidação / node pool reduction
- **Replicas estagnadas** → sugere HPA com base em métricas
- **PVs não utilizados** → recomenda cleanup

## 🚀 Como Usar

```bash
pip install kafka-python
python ~/.openclaw/workspace/skills/optimization-agent/scripts/agent.py
```

## 📁 Scripts

- `scripts/agent.py` — loop principal do agente
