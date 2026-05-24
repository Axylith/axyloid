# Multi-stage build: keeps the final image small (~150MB)
# Stage 1: build the dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps for compiling cryptography (PyJWT needs it)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata + README (hatchling reads README during pip install)
COPY pyproject.toml README.md ./
COPY core/ ./core/
COPY cli/ ./cli/
COPY server/ ./server/

# Install into a clean prefix we can copy out
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: minimal runtime
FROM python:3.11-slim

# Non-root user for security
RUN useradd --create-home --shell /bin/bash axyloid

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy the app source (the package is also installed via pip,
# but keeping source available helps debugging)
COPY --chown=axyloid:axyloid core/ ./core/
COPY --chown=axyloid:axyloid cli/ ./cli/
COPY --chown=axyloid:axyloid server/ ./server/

USER axyloid

# Cloud Run injects PORT; default to 8080 if running locally
ENV PORT=8080
EXPOSE 8080

# Use uvicorn directly. Single worker — Cloud Run handles concurrency
# at the container level, not the worker level.
CMD exec uvicorn server.main:app --host 0.0.0.0 --port ${PORT} --workers 1