# 🏢 OpenClaw Condo Agent

Container mínimo do OpenClaw para rodar como agente de condomínio no OpenShift.

## Build local

```bash
docker build -t openclaw-condo .
```

## Deploy no OpenShift

```bash
# Ajustar a secret com sua API key
oc apply -f deploy/deploy.yaml

# Editar a secret com a chave real
oc edit secret openclaw-condo-secrets -n openclaw-condo

# Ou via linha de comando:
oc patch secret openclaw-condo-secrets -n openclaw-condo -p '{"stringData":{"deepseek-api-key":"sk-..."}}'
```

## Variáveis de Ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `DEEPSEEK_API_KEY` | ✅ | Chave da API DeepSeek |
| `AGENT_NAME` | ❌ | Nome do agente (default: "Condominio Agent") |
| `DEFAULT_MODEL` | ❌ | Modelo padrão (default: "deepseek/deepseek-chat") |
| `GATEWAY_TOKEN` | ❌ | Token de autenticação do gateway |

## Tamanho

- Imagem base: node:22-alpine (~170MB)
- OpenClaw: ~370MB (runtime + providers)
- **Total estimado: ~540MB**

> Para ambientes maiores, considerar imagem completa com node:22-slim ou ubi9/nodejs-22.
