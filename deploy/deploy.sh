#!/usr/bin/env bash
set -euo pipefail
cd /opt/rico4
docker compose pull || true
docker compose build --pull
docker compose up -d
docker compose ps
