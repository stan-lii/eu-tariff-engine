#!/usr/bin/env bash
# Health check for EU Tariff Engine Docker services.
# Checks which profile services are running and reports their status.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Container names carry the project prefix from docker-compose.yml
PREFIX="tariff-engine"

pass() { echo -e "  ${GREEN}[OK]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; FAILED=1; }
skip() { echo -e "  ${YELLOW}[SKIP]${NC} $1 (not running)"; }

FAILED=0

echo ""
echo "=== EU Tariff Engine: Health Check ==="
echo ""

# --- Core Profile ---
echo "Core Profile:"

if docker inspect "${PREFIX}-te-postgres-1" --format='{{.State.Status}}' 2>/dev/null | grep -q running; then
  if docker exec "${PREFIX}-te-postgres-1" pg_isready -U tariff_engine -q 2>/dev/null; then
    pass "PostgreSQL + pgvector (te-postgres) on port 5432"
  else
    fail "PostgreSQL (te-postgres) is running but not ready"
  fi
else
  skip "PostgreSQL (te-postgres)"
fi

if docker inspect "${PREFIX}-te-redis-1" --format='{{.State.Status}}' 2>/dev/null | grep -q running; then
  if docker exec "${PREFIX}-te-redis-1" redis-cli ping 2>/dev/null | grep -q PONG; then
    pass "Redis (te-redis) on port 6379"
  else
    fail "Redis (te-redis) is running but not responding"
  fi
else
  skip "Redis (te-redis)"
fi

if docker inspect "${PREFIX}-te-minio-1" --format='{{.State.Status}}' 2>/dev/null | grep -q running; then
  if curl -sf http://localhost:9000/minio/health/live >/dev/null 2>&1; then
    pass "MinIO (te-minio) on port 9000"
  else
    fail "MinIO (te-minio) is running but not healthy"
  fi
else
  skip "MinIO (te-minio)"
fi

echo ""

# --- Obs Profile ---
echo "Obs Profile (Langfuse):"

if docker inspect "${PREFIX}-lf-web-1" --format='{{.State.Status}}' 2>/dev/null | grep -q running; then
  if curl -sf http://localhost:3000/api/public/health >/dev/null 2>&1; then
    pass "Langfuse Web (lf-web) on port 3000"
  else
    echo -e "  ${YELLOW}[WAIT]${NC} Langfuse Web starting (may take 2 to 3 minutes)"
  fi
else
  skip "Langfuse Web (lf-web)"
fi

if docker inspect "${PREFIX}-lf-clickhouse-1" --format='{{.State.Status}}' 2>/dev/null | grep -q running; then
  if curl -sf http://localhost:8123/ping >/dev/null 2>&1; then
    pass "ClickHouse (lf-clickhouse) on port 8123"
  else
    fail "ClickHouse (lf-clickhouse) is running but not responding"
  fi
else
  skip "ClickHouse (lf-clickhouse)"
fi

for svc in lf-postgres lf-redis lf-minio lf-worker; do
  if docker inspect "${PREFIX}-${svc}-1" --format='{{.State.Status}}' 2>/dev/null | grep -q running; then
    pass "$svc"
  else
    skip "$svc"
  fi
done

echo ""

# --- Memory Usage ---
echo "Container Memory Usage:"
RUNNING=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "^${PREFIX}" || true)
if [ -n "$RUNNING" ]; then
  docker stats --no-stream --format "  {{.Name}}: {{.MemUsage}}" $RUNNING
else
  echo "  No tariff engine containers running."
fi

echo ""

if [ "$FAILED" -eq 1 ]; then
  echo -e "${RED}Some checks failed. See above.${NC}"
  exit 1
else
  echo -e "${GREEN}All running services are healthy.${NC}"
fi
