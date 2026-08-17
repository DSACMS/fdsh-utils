# Specifications

The goal of this sub-project is to produce a Docker image that behaves as close
to the FDSH as possible to enable local testing. Additionally, this should
provide high quality, synthetic data.

## Requirements

### mTLS

The FDSH requires mutual TLS verification on all its connections. It
additionally requires TLS v1.2 that clients provide a valid X.509 certificate
signed by a trusted CA. Certificates must use 2048-bit keys and SHA-2 message
digest (SHA-256, SHA-384, or SHA-512).

#### mTLS Test Cases

1. No Client Certificate / Key

Unable to verify expected behavior

1. Invalid Client Certificate / Key

Unable to verify expected behavior

1. Invalid TLS version

When using TLS v1.1

```sh
curl \
    --cert ${PATH_TO_CERT} \
    --key ${PATH_TO_KEY} \
    --tlsv1.1 \
    --tls-max 1.1 \
     # Additional flags as needed
    -X POST ${HUB_HOST_AND_PORT} -v
```

```sh
* Added HUB_HOST_AND_IP to DNS cache
* Hostname HUB_HOST was found in DNS cache
*   Trying HUB_IP...
* Connected to HUB_HOST (HUB_IP) port HUB_PORT
* ALPN: curl offers h2,http/1.1
* (304) (OUT), TLS handshake, Client hello (1):
*  CAfile: CA_FILE_PATH
*  CApath: CA_DIR_PATH
* LibreSSL/3.3.6: error:1404B42E:SSL routines:ST_CONNECT:tlsv1 alert protocol version
* Closing connection
curl: (35) LibreSSL/3.3.6: error:1404B42E:SSL routines:ST_CONNECT:tlsv1 alert protocol version
```

When using TLS v1.3

```sh
curl \
    --cert ${PATH_TO_CERT} \
    --key ${PATH_TO_KEY} \
    --tlsv1.3 \
    --tls-max 1.3 \
     # Additional flags as needed
    -X POST ${HUB_HOST_AND_PORT} -v
```

```sh
* Added HUB_HOST_AND_IP to DNS cache
* Hostname HUB_HOST was found in DNS cache
*   Trying HUB_IP...
* Connected to HUB_HOST (HUB_IP) port HUB_PORT
* Closing connection
```

### OAuth token endpoint

JSON services are additionally authenticated using OAuth 2.0 client credentials.

#### OAuth Token Endpoint Test Cases

1. Invalid Grant Type

```sh
curl \
    --cert ${PATH_TO_CERT} \
    --key ${PATH_TO_KEY} \
    --tlsv1.2 \
    --tls-max 1.2 \
     # Additional flags as needed
    -X POST ${HUB_HOST_AND_PORT}/auth/oauth/v2/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=authorization_code&code=${OAUTH_CODE}&redirect_uri=${REDIRECT_URL}" \
    -v
```

```json
{
  "error":"invalid_request",
  "error_description":"Missing or duplicate parameters"
}
```

1. Invalid Credentials

```sh
curl \
    --cert ${PATH_TO_CERT} \
    --key ${PATH_TO_KEY} \
    --tlsv1.2 \
    --tls-max 1.2 \
     # Additional flags as needed
    -X POST ${HUB_HOST_AND_PORT}/auth/oauth/v2/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=bad_id&client_secret=bad_secret" \
    -v
```

```json
{
  "error":"invalid_client",
  "error_description":"The given client credentials were not valid"
}
```

1. Happy Path

```sh
curl \
    --cert ${PATH_TO_CERT} \
    --key ${PATH_TO_KEY} \
    --tlsv1.2 \
    --tls-max 1.2 \
     # Additional flags as needed
    -X POST ${HUB_HOST_AND_PORT}/auth/oauth/v2/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=${OAUTH_CLIENT_KEY}&client_secret=${OAUTH_CLIENT_SECRET}" \
    -v
```

```json
{
  "access_token":"<JWT_TOKEN>",
  "token_type":"Bearer",
  "expires_in":1800,
  "scope":"<SCOPES>"
}
```
