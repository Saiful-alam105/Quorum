FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-cov==7.1.0

RUN useradd --create-home --uid 1000 sandbox \
    && mkdir -p /workspace \
    && chown sandbox:sandbox /workspace

WORKDIR /workspace

USER sandbox