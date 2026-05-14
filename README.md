# OpenClaw Demo Kafka 🔮

> Agentes autônomos conectados ao Kafka no OpenShift para auto-geração, diagnóstico e resolução de problemas em clusters Kubernetes.

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     OpenShift Cluster                    │
│                                                         │
│  ┌──────────┐    ┌─────────────────────────────────┐   │
│  │  Event    │───▶│          Kafka (KRaft)          │   │
│  │  Watcher  │    │  cluster.events                 │   │
│  └──────────┘    │  cluster.alerts                  │   │
│                  │  agent.commands                   │   │
│                  │  agent.reasoning                  │   │
│                  │  agent.feedback                   │   │
│                  │  agent.events                     │   │
│                  └──────────┬──────────────────────┘   │
│                             │                          │
│           ┌─────────────────┼──────────────────┐       │
│           ▼                 ▼                  ▼       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Security    │  │ Optimization │  │  Operations  │ │
│  │  Agent 🛡️    │  │ Agent 📈     │  │ Agent 🔧     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │          │
│         └─────────────────┼──────────────────┘          │
│                           ▼                            │
│                   ┌──────────────┐                     │
│                   │  Troublemaker│                     │
│                   │  Agent 😈    │                     │
│                   └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## 📋 Componentes

### Agentes

| Agente | Nome | Função |
|--------|------|--------|
| 🛡️ | **Security Agent** | Monitora segurança, detecta vulnerabilidades, acessos suspeitos e violações de compliance |
| 📈 | **Optimization Agent** | Analisa uso de recursos, sugere rightsizing, HPA e otimizações de custo |
| 🔧 | **Operations Agent** | Self-healing: detecta CrashLoopBackOff, OOMKill, ImagePullBackOff e executa ações corretivas |
| 😈 | **Troublemaker** | Cria problemas controlados para testar os agentes (ativado via chat/roleta) |

### Infraestrutura

| Componente | Descrição |
|------------|-----------|
| **Apache Kafka** | Cluster KRaft no namespace `kafka`, barramento de eventos central |
| **Event Watcher** | Observa o cluster OpenShift e publica eventos no Kafka |
| **Proxy TCP** | Expõe Kafka via Route (plaintext, porta 9092) |
| **Agent System** | Backend MCP que conecta agentes ao cluster |
| **Mission Control** | Interface para criar problemas controlados |

## 🚀 Deploy no OpenShift

```bash
# Namespaces
oc new-project kafka
oc new-project openclaw-agents

# Kafka
oc apply -f deploy/kafka/ -n kafka

# Agentes
oc apply -f deploy/agents/ -n openclaw-agents

# Apresentação
oc apply -f deploy/presentation/ -n openclaw-agents
```

## 🎮 Uso

### Agentes (automático)
Os agentes rodam continuamente e reagem a eventos do Kafka.

### Troublemaker (manual)
```bash
# Listar ações disponíveis
python3 agents/troublemaker/scripts/troublemaker.py

# Criar um pod em CrashLoopBackOff
python3 agents/troublemaker/scripts/troublemaker.py crash

# Limpar todos os problemas
python3 agents/troublemaker/scripts/troublemaker.py cleanup
```

### Apresentação
Acesse a rota da apresentação no OpenShift:
```
https://openclaw-presentation-openclaw-presentation.apps.bbdw.sandbox3066.opentlc.com
```

## 📡 Tópicos Kafka

| Tópico | Descrição | Produzido por | Consumido por |
|--------|-----------|---------------|---------------|
| `cluster.events` | Eventos do cluster | Event Watcher | Optimization Agent |
| `cluster.alerts` | Alertas do cluster | Event Watcher | Security, Operations |
| `agent.commands` | Comandos entre agentes | Qualquer agente | Qualquer agente |
| `agent.reasoning` | Análises e recomendações | Security, Optimization, Operations | Outros agentes |
| `agent.feedback` | Feedback de ações | Operations Agent | Qualquer agente |
| `agent.events` | Eventos internos dos agentes | Qualquer agente | Optimization Agent |

## 🔧 Stack

- **OpenShift** (Red Hat)
- **Apache Kafka** (KRaft mode)
- **Python** (agentes)
- **MCP** (Model Context Protocol)
- **HTML/CSS/JS** (apresentação interativa)

---

> 🔮 Feito com 💙 por **Navi** e **Link**
