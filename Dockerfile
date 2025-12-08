# Multi-stage build for buildOS Dashboard
# Optimized for Dokploy/Hetzner deployment

# Stage 1: Build frontend
FROM oven/bun:1 AS frontend-builder

WORKDIR /app/client
COPY apps/client/package.json apps/client/bun.lock ./
RUN bun install --frozen-lockfile

COPY apps/client/ ./
RUN bun run build

# Stage 2: Build server dependencies
FROM oven/bun:1 AS server-builder

WORKDIR /app/server
COPY apps/server/package.json apps/server/bun.lock ./
RUN bun install --frozen-lockfile --production

# Stage 3: Final production image
FROM python:3.12-slim

# Install system dependencies and bun
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && curl -fsSL https://bun.sh/install | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.bun/bin:${PATH}"

WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy server dependencies from builder
COPY --from=server-builder /app/server/node_modules ./apps/server/node_modules

# Copy application code
COPY orchestrator.py conversation_logger.py load_env.py sdk_tools.py skills_client.py ./
COPY apps/server/src ./apps/server/src/
COPY apps/server/package.json ./apps/server/

# Copy Claude config (agents, tools, etc.)
COPY .claude ./.claude/

# Copy built frontend from builder
COPY --from=frontend-builder /app/client/dist ./apps/client/dist

# Create necessary directories with correct permissions
RUN mkdir -p uploads workspace .logs/conversations \
    && chmod -R 755 uploads workspace .logs

# Environment variables
ENV SERVER_PORT=4000
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/events/recent?limit=1 || exit 1

# Expose port
EXPOSE 4000

# Start server (serves both API and static frontend)
WORKDIR /app/apps/server
CMD ["bun", "run", "src/index.ts"]
