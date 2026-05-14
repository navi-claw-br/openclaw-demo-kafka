"""
Configuração centralizada dos agentes Kafka para demo OpenShift.
"""

# Kafka
KAFKA_BOOTSTRAP_SERVERS = "kafka-proxy-kafka.apps.bbdw.sandbox3066.opentlc.com:9092"
KAFKA_CLIENT_ID = "openclaw-agent"

# Tópicos de eventos do cluster (produzidos pelo event-watcher)
TOPIC_EVENTS = "cluster.events"
TOPIC_ALERTS = "cluster.alerts"

# Tópicos de agentes
TOPIC_COMMANDS = "agent.commands"
TOPIC_REASONING = "agent.reasoning"
TOPIC_FEEDBACK = "agent.feedback"
TOPIC_AGENT_EVENTS = "agent.events"

# Timeouts
POLL_TIMEOUT = 1.0   # segundos por poll loop
HEARTBEAT_INTERVAL = 3
SESSION_TIMEOUT = 30
