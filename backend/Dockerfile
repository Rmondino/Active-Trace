# =============================================================================
# Stage 1: builder — install dependencies
# =============================================================================
FROM python:3.13-slim AS builder

WORKDIR /build

# Install system build dependencies (for psycopg2, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[test]"

# =============================================================================
# Stage 2: runtime — minimal image
# =============================================================================
FROM python:3.13-slim AS runtime

WORKDIR /app

# Install runtime system deps (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ /app/app/
COPY run.py /app/run.py
COPY alembic.ini /app/alembic.ini
COPY alembic/ /app/alembic/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
