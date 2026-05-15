# 🏢 OpenClaw Condo Agent — Minimal Image
# Base: Node.js 22 Alpine (170MB)
FROM node:22-alpine AS builder

ARG OPENCLAW_VERSION=latest

WORKDIR /build

# Install OpenClaw (production only, no dev deps)
RUN npm install openclaw@${OPENCLAW_VERSION} --omit=dev --ignore-scripts && \
    # Strip docs (15MB) and non-essential files
    rm -rf node_modules/openclaw/docs && \
    rm -rf node_modules/openclaw/patches

# ── Runtime stage ──
FROM node:22-alpine

RUN apk add --no-cache curl ca-certificates tzdata

WORKDIR /opt/openclaw

# Copy from builder
COPY --from=builder /build/node_modules /opt/openclaw/node_modules

# Create symlink so 'openclaw' command works
RUN ln -s /opt/openclaw/node_modules/.bin/openclaw /usr/local/bin/openclaw

# Create workspace structure
RUN mkdir -p /data/workspace /data/config /data/credentials

# Create entrypoint config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Volumes for persistence
VOLUME /data/workspace /data/config /data/credentials

EXPOSE 18789

ENTRYPOINT ["/entrypoint.sh"]
CMD ["openclaw", "gateway"]
