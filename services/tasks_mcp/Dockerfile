# Stage 1: Build environment with uv
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv — pinned for reproducibility
COPY --link pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv export --no-dev --format requirements-txt --no-emit-project > requirements.txt \
    && uv pip install --system --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/uv /root/.cache/pip

# Install the project package itself (no deps — already done)
COPY --link tasks_mcp/ tasks_mcp/
RUN uv pip install --system --no-cache-dir --no-deps . \
    && rm -rf /root/.cache/uv

# Stage 2: Minimal runtime image
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 app \
    && adduser --system --uid 1001 --gid 1001 app

# Copy only runtime artifacts from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/tasks-mcp /usr/local/bin/tasks-mcp
COPY --from=builder /app/tasks_mcp /app/tasks_mcp

# Python runtime hardening
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1

EXPOSE 8000

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -m tasks_mcp.healthcheck 8000

CMD ["python", "-m", "tasks_mcp.server"]
