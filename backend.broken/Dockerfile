# syntax=docker/dockerfile:1.7
# -----------------------------------------------------------------------------
# Backend Dockerfile - multi-stage build.
#
# Stage 1 (builder): installs dependencies into a venv. Heavy build tools live
#   here and are discarded.
# Stage 2 (runtime): copies just the venv + app code onto a slim base. Result
#   is a much smaller, faster-pulling image, with no compilers shipped to prod.
#
# We also run as a non-root user. Most k8s admission policies (PodSecurity
# baseline/restricted) reject containers running as root, and it's a sensible
# default regardless.
# -----------------------------------------------------------------------------

# --- Stage 1: build dependencies --------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install system packages needed only at build time (e.g. for compiling pandas
# wheels if a prebuilt one isn't available for the target arch). Cleaned up by
# virtue of being in the builder stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a venv that we'll copy whole into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first to maximize Docker layer caching - if requirements
# don't change, this layer is reused even when app code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# --- Stage 2: runtime --------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create a non-root user to run the app. UID 1000 is conventional for
# first non-system user and works well with most k8s securityContexts.
RUN groupadd -g 1000 app && useradd -u 1000 -g app -m -s /bin/bash app

WORKDIR /app

# Copy the prebuilt venv from the builder stage. No pip, no compilers.
COPY --from=builder /opt/venv /opt/venv

# Copy application code. Owned by the app user so it can read but not modify
# files at runtime - principle of least privilege.
COPY --chown=app:app app/ ./app/

USER app

EXPOSE 8000

# Use uvicorn directly (no gunicorn wrapper for now - one process per pod is
# fine, k8s handles scaling by spawning more pods rather than more workers).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]