# Generates a local CA, server cert (for nginx), and one client cert (for developers/clients to authenticate with).

#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CERT_DIR"

DAYS_CA=3650
DAYS_LEAF=825   # keep under common 825-day max even though this is internal/local

echo "==> Generating local CA"
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days "$DAYS_CA" \
  -subj "/C=US/O=LocalDev/OU=LocalCA/CN=local-dev-root-ca" \
  -out ca.crt

echo "==> Generating server key + CSR (nginx)"
openssl genrsa -out server.key 2048
openssl req -new -key server.key \
  -subj "/C=US/O=LocalDev/OU=Server/CN=localhost" \
  -out server.csr

cat > server.ext <<EOF
subjectAltName = DNS:localhost,DNS:nginx,IP:127.0.0.1
extendedKeyUsage = serverAuth
EOF

echo "==> Signing server cert with local CA"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days "$DAYS_LEAF" -sha256 -extfile server.ext

echo "==> Generating client key + CSR (developer/client)"
openssl genrsa -out client.key 2048
openssl req -new -key client.key \
  -subj "/C=US/O=LocalDev/OU=Client/CN=local-dev-client" \
  -out client.csr

cat > client.ext <<EOF
extendedKeyUsage = clientAuth
EOF

echo "==> Signing client cert with local CA"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days "$DAYS_LEAF" -sha256 -extfile client.ext

rm -f server.csr client.csr server.ext client.ext ca.srl

echo ""
echo "==> Done. Files generated in $CERT_DIR:"
echo "    ca.crt / ca.key         (local root CA — trusted by nginx)"
echo "    server.crt / server.key (used by nginx for TLS)"
echo "    client.crt / client.key (present this when calling the API)"
echo ""
echo "The API also requires an OAuth bearer token from http://localhost:9100/token."
echo "Example API call once services are up and you have a token:"
echo "  curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key \\"
echo "       -H 'Authorization: Bearer <access_token>' \\"
echo "       https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/retrieve \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d @json/NSC-request-MIN.json"