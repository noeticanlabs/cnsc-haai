#!/bin/bash
# HAAI Docker Entrypoint Script
# ===============================

set -e

echo "==================================="
echo "HAAI Docker Entrypoint"
echo "==================================="
echo "Environment: ${HAAI_ENV:-unknown}"
echo "Python version: $(python --version)"
echo ""

# Wait for dependencies if needed
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "import psycopg2; psycopg2.connect('${HAAI_DATABASE_URL}')" 2>/dev/null; then
            echo "✅ PostgreSQL is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: PostgreSQL not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ PostgreSQL failed to start after $max_attempts attempts"
    return 1
}

wait_for_redis() {
    echo "Waiting for Redis..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "import redis; r = redis.from_url('${HAAI_REDIS_URL}'); r.ping()" 2>/dev/null; then
            echo "✅ Redis is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Redis not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Redis failed to start after $max_attempts attempts"
    return 1
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    python -c "
import sys
sys.path.insert(0, '/app')
try:
    from haai.core.database import DatabaseManager
    db = DatabaseManager()
    db.initialize()
    print('✅ Database initialized successfully')
    db.shutdown()
except Exception as e:
    print(f'⚠️  Database initialization: {e}')
    print('Continuing without database...')
"
}

# Run tests or custom command
run_command() {
    echo ""
    echo "==================================="
    echo "Running: $@"
    echo "==================================="
    
    exec "$@"
}

# Main logic
main() {
    # Wait for dependencies if URL is provided
    if [ -n "${HAAI_DATABASE_URL}" ]; then
        wait_for_postgres || echo "⚠️  Continuing without PostgreSQL..."
    fi
    
    if [ -n "${HAAI_REDIS_URL}" ]; then
        wait_for_redis || echo "⚠️  Continuing without Redis..."
    fi
    
    # Run migrations
    if [ "${HAAI_ENV}" = "production" ]; then
        run_migrations
    fi
    
    # Print version info
    echo ""
    echo "HAAI Version Info:"
    python -c "
import sys
sys.path.insert(0, '/app')
try:
    from haai import __version__
    print(f'  Version: {__version__}')
except ImportError:
    print('  Version: unknown')
    
try:
    from haai.core import CoherenceEngine
    print('  CoherenceEngine: ✅')
except ImportError as e:
    print(f'  CoherenceEngine: ❌ ({e})')

try:
    from haai.nsc import NSCProcessor
    print('  NSCProcessor: ✅')
except ImportError as e:
    print(f'  NSCProcessor: ❌ ({e})')

try:
    from haai.governance import CGLGovernance
    print('  CGLGovernance: ✅')
except ImportError as e:
    print(f'  CGLGovernance: ❌ ({e})')
"
    
    echo ""
    echo "==================================="
    echo "Starting HAAI..."
    echo "==================================="
    
    # Run the provided command
    run_command "$@"
}

# Run main with all arguments
main "$@"
