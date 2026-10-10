FROM debian:trixie-slim AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

RUN python3 -m venv /opt/venv \
    && useradd --create-home tester

WORKDIR /app


FROM base AS tests

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY --chown=tester . .
RUN chown tester /app
USER tester

CMD ["pytest"]
