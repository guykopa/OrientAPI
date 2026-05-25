FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .

RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir --upgrade pip && \
    /venv/bin/pip install --no-cache-dir .


FROM python:3.12-slim AS final

RUN useradd --uid 1001 --no-create-home --shell /bin/false appuser

WORKDIR /app

COPY --from=builder /venv /venv
COPY src/ ./src/

USER appuser

EXPOSE 8000

ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
