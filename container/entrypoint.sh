#!/bin/sh
# OpenClaw Condo Agent — Entrypoint
set -e

CONFIG_FILE="/data/config/openclaw.json"
WORKSPACE="/data/workspace"
CREDENTIALS="/data/credentials"

# Generate config on first run
if [ ! -f "$CONFIG_FILE" ]; then
    echo "🔮 Generating OpenClaw config..."

    AGENT_NAME="${AGENT_NAME:-Condominio Agent}"
    AGENT_ID="${AGENT_ID:-condo-agent}"
    DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"

    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo "⚠️  WARNING: DEEPSEEK_API_KEY not set. Set it as env var or via config."
    fi

    cat > "$CONFIG_FILE" << CONFIGEOF
{
    "meta": {
        "lastTouchedVersion": "2026.5.7",
        "lastTouchedAt": "$(date -Iseconds)"
    },
    "auth": {
        "profiles": {
            "deepseek:default": {
                "provider": "deepseek",
                "mode": "api_key"
            }
        }
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
        "bind": "0.0.0.0",
        "auth": {
            "mode": "token",
            "token": "${GATEWAY_TOKEN:-$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo 'openclaw-condo-token')}"
        }
    },
    "skills": {
        "paths": ["$WORKSPACE/skills"]
    },
    "channels": {},
    "messages": {
        "fallbackOnNoReply": false
    },
    "hooks": {},
    "plugins": {},
    "tools": {},
    "commands": {},
    "session": {},
    "skills": {},
    "features": {
        "onboardingTips": false,
        "modelDownloader": false
    }
}
CONFIGEOF
    echo "✅ Config generated at $CONFIG_FILE"
fi

# Display mode
echo "🔮 OpenClaw Condo Agent iniciando..."
echo "   AGENT: ${AGENT_NAME:-default}"
echo "   MODEL: ${DEFAULT_MODEL:-deepseek/deepseek-chat}"
echo "   PORT:  18789"
echo ""

# For DeepSeek API key — OpenClaw reads from env var
if [ -n "$DEEPSEEK_API_KEY" ]; then
    export DEEPSEEK_API_KEY
fi

# Run OpenClaw with config
exec "$@"
