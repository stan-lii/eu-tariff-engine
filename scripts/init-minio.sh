#!/usr/bin/env bash
# Wait for MinIO to be ready, then create the raw artefact bucket.
set -euo pipefail

echo "Waiting for MinIO..."
until mc alias set local http://localhost:9000 "${MINIO_ROOT_USER:-minioadmin}" "${MINIO_ROOT_PASSWORD:-minioadmin_dev}" 2>/dev/null; do
  sleep 1
done

echo "Creating bucket: tariff-engine-raw"
mc mb local/tariff-engine-raw --ignore-existing
echo "MinIO bucket ready."
