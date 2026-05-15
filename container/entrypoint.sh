#!/bin/sh
# OpenClaw Condo Agent — Entrypoint
set -e

export OPENCLAW_STATE_DIR="/data"
export OPENCLAW_CONFIG_PATH="/data/config/openclaw.json"

CONFIG_FILE="$OPENCLAW_CONFIG_PATH"
WORKSPACE="/data/workspace"
CREDENTIALS="/data/credentials"

# Ensure data directories exist
mkdir -p /data/config /data/workspace /data/credentials

# Generate config on first run
if [ ! -f "$CONFIG_FILE" ]; then
    echo "🔮 Generating OpenClaw config..."

    AGENT_NAME="${AGENT_NAME:-Condominio Agent}"
    AGENT_ID="${AGENT_ID:-condo-agent}"
    GATEWAY_TOKEN="${GATEWAY_TOKEN:-$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo 'openclaw-condo-token')}"

    cat > "$CONFIG_FILE" << CONFIGEOF
{
    "meta": {
        "lastTouchedVersion": "2026.5.7",
        "lastTouchedAt": "$(date -Iseconds)"
    },
    "auth": {
        "profiles": {}
    },
    "models": {
        "mode": "merge",
        "providers": {
            "deepseek": {
                "baseUrl": "https://api.deepseek.com",
                "api": "openai-completions",
                "models": [
                    {
                        "id": "deepseek-chat",
                        "name": "DeepSeek Chat",
                        "api": "openai-completions",
                        "input": ["text"],
                        "contextWindow": 131072,
                        "maxTokens": 8192
                    },
                    {
                        "id": "deepseek-reasoner",
                        "name": "DeepSeek Reasoner",
                        "api": "openai-completions",
                        "reasoning": true,
                        "input": ["text"],
                        "contextWindow": 131072,
                        "maxTokens": 65536
                    }
                ]
            }
        }
    },
    "agents": {
        "defaults": {
            "model": {
                "primary": "${DEFAULT_MODEL:-deepseek/deepseek-chat}"
            },
            "workspace": "$WORKSPACE",
            "maxConcurrent": 2
        },
        "list": [
            {
                "id": "main",
                "default": true,
                "name": "$AGENT_NAME",
                "workspace": "$WORKSPACE"
            }
        ]
    },
    "gateway": {
        "port": 18789,
        "mode": "local",
        "bind": "lan",
        "auth": {
            "mode": "token",
            "token": "$GATEWAY_TOKEN"
        }
    }
}
CONFIGEOF
    echo "✅ Config generated at $CONFIG_FILE"

    # Run setup wizard to install platform deps (models, profiles, etc)
    echo "🔧 Running openclaw setup..."
    openclaw setup --non-interactive --accept-defaults 2>/dev/null || true
fi

# Display mode
echo "🔮 OpenClaw Condo Agent iniciando..."
echo "   AGENT: ${AGENT_NAME:-default}"
echo "   MODEL: ${DEFAULT_MODEL:-deepseek/deepseek-chat}"
echo "   PORT:  18789"
echo ""

# For DeepSeek API key — OpenClaw reads from env var
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"

# Run OpenClaw with config
exec "$@"
