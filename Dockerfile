# Multi-stage build: keeps the final image small (~150MB)
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY core/ ./core/
COPY cli/ ./cli/
COPY server/ ./server/

RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: minimal runtime
FROM python:3.11-slim

RUN useradd --create-home --shell /bin/bash axyloid

WORKDIR /app

COPY --from=builder /install /usr/local

COPY --chown=axyloid:axyloid core/ ./core/
COPY --chown=axyloid:axyloid cli/ ./cli/
COPY --chown=axyloid:axyloid server/ ./server/

USER axyloid

ENV PORT=8080
EXPOSE 8080

# Explicit shell-form CMD with proper variable expansion.
# The :-8080 fallback handles edge cases where PORT might be unset.
CMD ["sh", "-c", "exec uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]