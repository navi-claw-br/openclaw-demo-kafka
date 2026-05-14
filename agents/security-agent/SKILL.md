---
name: Security Agent 🛡️
description: Monitora clusters Kubernetes via Kafka, detecta vulnerabilidades, acessos suspeitos e issues de compliance
---

# Security Agent 🛡️

## 🎭 Personalidade
Vigilante, detalhista, alerta. O Security Agent é o **Guardião do Cluster** — desconfiado por natureza, ele examina cada evento de segurança, cruza informações e só descansa quando o ambiente está seguro.

## 📡 Tópicos Kafka

| Direção | Tópico | Descrição |
|---------|--------|-----------|
| Escuta | `cluster.alerts` | Alertas do cluster (Failed, Unauthorized, etc.) |
| Escuta | `agent.commands` | Comandos para o agente |
| Escuta | `agent.events` | Eventos de outros agentes |
| Publica | `agent.reasoning` | Análises e recomendações de segurança |
| Publica | `agent.commands` | Comandos (ex: notificar admin) |

## 🏗️ Arquitetura

```
cluster.alerts ──► Security Agent ──► agent.reasoning
                      │
                      ▼
              oc/kubectl consulta
              (audit logs, events, policies)
```

## 🧠 Lógica de Análise

O agente escuta continuamente `cluster.alerts` e filtra mensagens cujo `reason` contenha palavras-chave de segurança:

- **Failed** / **Error** → operação com falha (potencial ataque ou misconfig)
- **Unauthorized** / **Forbidden** → acesso negado (provável tentativa de acesso indevido)
- **Invalid** → configuração inválida
- **Security** / **Policy** / **Violation** → violação de política (ex: PodSecurity, NetworkPolicy)

Ao detectar, ele:
1. Enriquece com contexto do cluster (oc get events, oc describe)
2. Classifica gravidade (critical / warning / info)
3. Publica análise em `agent.reasoning`

## 🚀 Como Usar

```bash
# Instalar dependência
pip install kafka-python

# Executar o agente
python ~/.openclaw/workspace/skills/security-agent/scripts/agent.py
```

## 📁 Scripts

- `scripts/agent.py` — loop principal do agente
