# Kafka Config Central

Shared Kafka configuration for agent skills.

```python
KAFKA_BOOTSTRAP_SERVERS = "kafka-proxy-kafka.apps.bbdw.sandbox3066.opentlc.com:9092"

TOPIC_EVENTS = "cluster.events"
TOPIC_ALERTS = "cluster.alerts"
TOPIC_COMMANDS = "agent.commands"
TOPIC_REASONING = "agent.reasoning"
TOPIC_FEEDBACK = "agent.feedback"
TOPIC_AGENT_EVENTS = "agent.events"
```

To connect from inside OpenShift cluster, use:
`my-cluster-kafka-bootstrap:9092`
