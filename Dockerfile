FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

USER appuser
EXPOSE 8000

ENV DPMCP_TRANSPORT=streamable-http \
    DPMCP_HOST=0.0.0.0 \
    DPMCP_PORT=8000

CMD ["data-platform-mcp"]
