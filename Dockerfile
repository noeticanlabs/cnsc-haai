# HAAI Docker Image
# =================================================

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini .
COPY setup.cfg .

# Final stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/src /app/src
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/pytest.ini /app/pytest.ini
COPY --from=builder /app/setup.cfg /app/setup.cfg
COPY --from=builder /app/requirements.txt /app/requirements.txt

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HAAI_ENV=production

# Create non-root user for security
RUN groupadd -r haai && useradd -r -g haai haai
RUN chown -R haai:haai /app
USER haai

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app'); from haai import __version__; print(f'HAAI v{__version__}')" || exit 1

# Default command
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
