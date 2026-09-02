# FDSH Mock Service: Image Architecture

A single Docker image bundles nginx, an OAuth auth service, and a read-only FastAPI API. The container is self-contained and retrieve-only: it has no create, update, or delete operations.

```text
+----------------------------------------------------------------+
| fdsh-mock-service container                                    |
|                                                                |
|  +----------------+     +----------------+                     |
|  | nginx          |---->| auth           |                     |
|  | TLS 1.2/mTLS   |     | JWT /token     |                     |
|  | public :8443   |     | /introspect    |                     |
|  +-------+--------+     | internal :9000 |                     |
|          |              +----------------+                     |
|          | proxy_pass                                          |
|          v                                                     |
|  +----------------+                                            |
|  | API            |                                            |
|  | POST /mesh/    |                                            |
|  | imp1/...       |                                            |
|  | internal :8000 |                                            |
|  +-------+--------+                                            |
|          | read-only                                           |
|          v                                                     |
|  +----------------+                                            |
|  | /app/data/     |                                            |
|  | records.json   |                                            |
|  | bundled data   |                                            |
|  +----------------+                                            |
+----------------------------------------------------------------+
```

Requests flow from nginx (TLS 1.2 with mTLS, requiring a valid client certificate and OAuth bearer token) to the internal auth service for token validation, then to the internal API, which reads a bundled flat file.

## Host Runtime Inputs

Two paths are mounted into the container at runtime:

* `/etc/nginx/certs/` — host `certs/` directory, mounted read-only
* `/etc/nginx/nginx.conf` — mounted read-only and configurable

The mounted `certs/` directory holds only the server-side files: `ca.crt`, `server.crt`, and `server.key`. The client certificate and key stay on the calling host and are passed directly to curl or an integration client for mTLS — they're never copied into the image.

## Data Model

The API reads a single domain-specific, bundled flat file. The `nsc` domain currently reads synthetic records from `data/records.json`. Future domains can register their own request model, handler, and `data/<domain>.json` file — just generate that file before building a new image.

## Ports and Endpoints

Two ports are exposed publicly:

* `8443` → nginx HTTPS retrieve endpoint
* `9100` → auth OAuth token endpoint

The API's port `8000` stays internal to the container and isn't exposed on the host. The OAuth token endpoint is `http://localhost:9100/auth/oauth/v2/token`, and the NSC retrieve endpoint is `https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService`. Registered future domains use `POST /domains/{domain_name}` and return a matching response from that domain's bundled file; missing records and invalid NSC requests return the standard NSC error response shape.

## Build

Generate or replace `data/records.json` using `data/generate_records.py` before building, then run:

```sh
docker build -t fdsh-mock-service:latest .
```

The bundled sample data can be used as-is. Private keys and certificates are never copied into the image.

## Run

Generate local certificates:

```sh
./certs/generate.sh
```

The Compose file mounts the host `certs/` directory read-only at `/etc/nginx/certs/`, and mounts `nginx/nginx.conf` read-only at `/etc/nginx/nginx.conf`. The mounted `certs/` directory must contain only `ca.crt`, `server.crt`, and `server.key`. Keep `client.crt` and `client.key` on the calling host and use them with curl — never place them in the server cert directory.

 Start the service:

```sh
docker compose up --build -d
```

**Specify location of ca.crt:**

Export a variable called `CURL_CA_BUNDLE` and point to the ca.crt created earlier. This tells the curl command where to find the ca.crt.

**Get a token:**

```sh
curl -X POST http://localhost:9100/auth/oauth/v2/token \
  -d grant_type=client_credentials \
  -d client_id=local-dev-client-id \
  -d client_secret=local-dev-client-secret
```

The `client_id` and `client_secret` can be changed. The following files must be updated to reflect the change as well: [docker-compose.yml](docker-compose.yml) and [security.py](auth/app/security.py)

**Retrieve a record:**

Create a request.json based on the [nsc-request.schema.json](../specs/medh/nsc/schemas/nsc-request.schema.json) and use it in the request:

```sh
curl --cert certs/client.crt \
  --key certs/client.key \
  -X POST https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d @<request.json>
```

If you don't want to pass a file, pass the json by replacing `-d` option with the `--json option`.

Example:

```text
--json '{"nscRequest": {
        "personGivenName": "Casey",
        "personSurName": "Bennett",
        "personBirthDate": "1966-06-07",
        "asOfDate": "2023-10-13",
        "termsAcceptedIndicator": true
        }
        }'
```

## Publish

coming
