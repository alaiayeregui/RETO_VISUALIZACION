#!/bin/bash
# setup-passwords.sh
# Configura la contraseña del usuario kibana_system en Elasticsearch.
# Ejecutar UNA SOLA VEZ tras el primer arranque: bash setup/setup-passwords.sh

set -euo pipefail

source .env

echo "⏳ Esperando a que Elasticsearch esté disponible..."
until curl -s --cacert /dev/stdin \
  "https://localhost:9200" \
  -u "elastic:${ELASTIC_PASSWORD}" \
  --cert-status > /dev/null 2>&1; do
  sleep 3
done

echo "🔐 Estableciendo contraseña para kibana_system..."
curl -s -X POST \
  --cacert <(docker exec elasticsearch cat /usr/share/elasticsearch/config/certs/ca/ca.crt) \
  "https://localhost:9200/_security/user/kibana_system/_password" \
  -u "elastic:${ELASTIC_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d "{\"password\": \"${KIBANA_PASSWORD}\"}" | python3 -m json.tool

echo ""
echo "✅ Contraseña configurada. Kibana puede conectarse ahora."
echo "   Abre http://localhost:5601 con usuario: elastic / contraseña: ${ELASTIC_PASSWORD}"
