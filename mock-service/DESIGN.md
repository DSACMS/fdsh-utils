
# FDSH Mock Service — Design Document

See [README.md](README.md) for details on the mock service's purpose, contributing to the project, disclaimer, security and privacy policy, and versioning guidance.

---

## Architecture

The mock service is designed to closely as practical replicate the security and transport patterns of a real FDSH production API — specifically, one that requires both **mutual TLS (mTLS)** and **OAuth 2.0 bearer tokens** to access. mTLS means both the server and the client present certificates during the TLS handshake, proving identity in both directions. OAuth 2.0 client credentials is a machine-to-machine token grant: your client exchanges a `client_id` and `client_secret` for a short-lived bearer token, which it then presents on every API call. This dual-credential approach lets you develop and test client integrations locally without needing access to a live or shared FDSH environment.

The expected behavior contract for all endpoints, authentication flows, and response shapes is defined in [`specs.md`](specs.md), which is the source of truth for this project. The design document you are reading now describes the runtime architecture and implementation structure that fulfills that contract.

The project is split into two independent concerns:

- **Request Flow** — how a client authenticates and calls the API

- **Certificate Lifecycle** — how TLS certificates are generated, mounted, and monitor

These two concerns are deliberately decoupled so that certificate rotation does not interrupt the request flow, and so each can be reasoned about and debugged independently.

```text
Request flow (separate from cert lifecycle)

                        ┌──────────────────────────┐
                        │     Developer / Client   │
                        └────────────┬─────────────┘
                                     │
              ┌──────────────────────┼───────────────────────┐
              │                                              │
   (1) POST /token                                (2) HTTPS request
     grant_type=client_credentials                + client cert (mTLS)
     client_id / client_secret                    + Bearer token (OAuth)
              │                                              │
              ▼                                              ▼
   ┌────────────────────┐                       ┌─────────────────────────┐
   │  auth  (FastAPI)   │                       │  nginx (custom image)   │
   │ :9000 → host:9100  │                       │  :8443 (TLS 1.3, mTLS)  │
   │                    │                       │                         │
   │ POST /token        │◄───────────────┐      │ 1. verify client cert   │
   │   issues JWT       │                │      │    (ssl_verify_client)  │
   │                    │  (3) auth_req  │      │ 2. auth_request         │
   │ GET /introspect    │  GET /introspect      │    subrequest→auth      │
   │   validates JWT    │────────────────┘      │ 3. 200→proxy_pass       │
   └────────────────────┘                       │    401→reject           │
                                                └───────────┬─────────────┘
                                                            │
                                             (4) proxy to   │
                                                 api:8000   │
                                                            ▼
                                                 ┌─────────────────────┐
                                                 │   api  (FastAPI)    │
                                                 │  :8000 (internal)   │
                                                 │                     │
                                                 │ /mesh/imp1/         │
                                                 │ NationalStudent-    │
                                                 │ ClearinghouseSvc/   │
                                                 │ records             │
                                                 │                     │
                                                 │ on startup:         │
                                                 │  alembic upgrade    │
                                                 │  head               │
                                                 └──────────┬──────────┘
                                                            │
                                                            ▼
                                                 ┌─────────────────────┐
                                                 │  db (Postgres 16)   │
                                                 │  :5432              │
                                                 │  nsc_records table  │
                                                 └─────────────────────┘


Cert lifecycle (separate from request flow):

  certs/generate.sh ──► ca.crt/key, server.crt/key, client.crt/key
                              │
                              ▼
                    mounted read-only into nginx container
                              │
                              ▼
        watch-reload.sh (inotify) ──► nginx -s reload on change

  certs/check_expiry.sh ──► warns/fails if any cert nears expiry
```

### Request Flow

The request flow enforces **two independent security checks** before any request reaches the API. Both must pass — failing either one results in a rejected request.

**Step 1 — Get a token.** Before making any API call, the client posts its `client_id` and `client_secret` to the `auth` service (FastAPI, exposed on host port `9100`). This is a standard OAuth 2.0 client credentials grant. The auth service issues a short-lived JWT (valid for 1 hour by default). This step happens directly over HTTP — it does not go through nginx — because the client does not yet have a token to present.

**Step 2 — Call the API with both credentials.** All API traffic enters through nginx on port `8443`, which terminates TLS 1.3 and enforces mTLS. mTLS means the *client* must present a certificate (not just the server), and nginx verifies it against the local CA. Once the certificate check passes, nginx fires an internal `auth_request` subrequest to the auth service's `/introspect` endpoint to validate the bearer token. Only if *both* checks return success does nginx proxy the request upstream to the API on port `8000`.

This pattern mirrors how many production government APIs work — a useful property when you are building a client integration and want your local dev environment to behave as close to production as possible.

NOTE: The values sent for `client_id` and `client_secret` must match the values in [docker-compose.yml](docker-compose.yml) in the auth service and [security.py](auth/app/security.py). If the values are changed while the docker service is running, the service must be restarted to pick up the changes.

### Certificate Lifecycle

Certificates are self-signed and managed entirely by shell scripts in the `certs/` directory. This keeps the setup self-contained and reproducible without requiring an external CA or certificate management tool.

`generate.sh` creates three certificate/key pairs from a local CA:

- `ca.crt` / `ca.key` — the root certificate authority used to sign everything else
- `server.crt` / `server.key` — presented by nginx to the client during the TLS handshake
- `client.crt` / `client.key` — presented by your curl commands (or client code) to nginx during mTLS

All three are mounted **read-only** into the nginx container at startup. When certificates are regenerated (e.g., because they are nearing expiry), `watch-reload.sh` detects the file change via `inotify` and triggers a graceful `nginx -s reload` — so nginx picks up the new certs without a full container restart and without dropping in-flight connections.

`check_expiry.sh` is a lightweight guard you can run before starting the stack or in CI. It warns or fails if any certificate is within a configurable number of days of expiring, preventing hard-to-diagnose TLS errors from catching you off guard.

---

### Folder Breakdown

The project follows a clean separation between infrastructure concerns (nginx, certs), service code (auth, api), and developer tooling (seed, test). Here is a map of the repository and what each piece does:

```text
mock-service/
├── architecture-diagram.mermaid   # Visual architecture diagram source
├── docker-compose.yml             # Orchestrates all services
├── README.md                      # Project overview and onboarding
├── specs.md                       # API contract / field-level specs
├── certs/
│   ├── generate.sh                # Generates CA, server, and client certs
│   └── check_expiry.sh            # Warns if any cert is nearing expiry
├── nginx/
│   ├── Dockerfile                 # Custom nginx image
│   ├── nginx.conf                 # mTLS + auth_request configuration
│   └── watch-reload.sh            # Reloads nginx on cert file changes
├── auth/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── generate_client_creds.py   # Helper to generate client_id/secret pairs
│   └── app/
│       ├── main.py                # FastAPI app: /token and /introspect routes
│       └── security.py            # JWT issuance and validation logic
├── api/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock                    # Generated by `uv lock` — do not edit by hand
│   ├── alembic.ini                # Alembic configuration
│   ├── migrations/
│   │   ├── env.py                 # Alembic env — import new models here
│   │   ├── script.py.mako         # Migration file template
│   │   └── versions/
│   │       └── 0001_create_nsc_records.py
│   │       └── ...                # Additional migrations go here
│   └── app/
│       ├── main.py                # FastAPI app entry point, router registration
│       ├── db.py                  # Database session and engine setup
│       ├── logging_config.py      # Structured logging configuration
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── error.py           # Shared error response schema
│       │   └── nsc.py             # NSC request/response Pydantic schemas
│       ├── models/
│       │   ├── __init__.py
│       │   └── nsc.py             # SQLAlchemy ORM model for nsc_records
│       └── domains/
│           ├── __init__.py
│           └── nsc/
│               ├── __init__.py
│               └── router.py      # NSC CRUD route handlers
├── test/
│   └── test_nsc_property.py       # Property-based tests for NSC schemas
└── seed/
    ├── README.md                  # Seeder usage details
    └── seed_records.py            # Synthetic data generator and seeder CLI
```

The `domains/` structure inside `api/app/` is intentional — each domain (e.g., `nsc`) owns its own router, making it straightforward to add new domains without touching existing code. See [Adding a new domain](#adding-a-new-domain) below.

---

## Execution

Follow these steps to get the full stack running locally. Steps 1 and 2 only need to be done once (or when certs expire). Steps 3 onward are your normal dev loop.

### 1. Generate Certs (once)

This creates the CA, server certificate, and client certificate used by nginx and your curl commands. You only need to re-run this if the certs expire or you want to rotate them.

```bash
chmod +x certs/generate.sh certs/check_expiry.sh
./certs/generate.sh
```

### 2. Sanity-Check Cert Expiry

Run this before starting the stack to catch any certificates that are close to expiring. It is also a good habit to add this to your CI pipeline.

```bash
./certs/check_expiry.sh
```

### 3. Bring Everything Up

Docker Compose builds and starts all four services: `nginx`, `auth`, `api`, and `db`. Database migrations run automatically when the `api` container starts — you do not need to run Alembic manually.

```bash
docker compose up --build --no-cache
```

### 4. Get an OAuth 2.0 Access Token

Fetch a bearer token from the auth service using the client credentials grant. This call goes directly to the auth service on port `9100` — it intentionally bypasses nginx because you do not have a token yet to satisfy the OAuth check.

```bash
curl -X POST http://localhost:9100/token \
     -d grant_type=client_credentials \
     -d client_id=local-dev-client_id \
     -d client_secret=local-dev-secret
```

Expected response:

```json
{"access_token": "...", "token_type": "Bearer", "expires_in": 3600}
```

Copy the `access_token` value — you will use it in every subsequent request.

### 5. Call an API Endpoint

All API calls go through nginx on port `8443` and require **both** the client certificate (mTLS) and the bearer token (OAuth). Omitting either one will result in a `401`.

```bash
curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/retrieve \
     -H "Content-Type: application/json" \
     -d @json/NSC-request-MIN.json
```

### 6. View Interactive Docs

The FastAPI `/docs` (Swagger UI) endpoint is also behind nginx, so it requires the same credentials. This is useful for exploring the API schema interactively during development.

```bash
curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     https://localhost:8443/docs
```

> **Tip:** You can open the docs in a browser by importing the client cert into your browser's certificate store and navigating to `https://localhost:8443/docs`.

### 7. NSC Record CRUD Operations

The API exposes four operations for NSC records. All follow the same pattern: POST to the appropriate endpoint with the client cert, bearer token, and a JSON body. Use the `MIN` request file for the minimum required fields, and the `MAX` file to exercise all optional fields.

**Create a record:**

```bash
curl --cacert certs/ca.crt \
     --cert certs/client.crt \
     --key certs/client.key \
     -X POST \
     https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/create \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     -H "Content-Type: application/json" \
     -d @json/NSC-request-MIN.json
```

**Retrieve a record (MIN):**

```bash
curl --cacert certs/ca.crt \
     --cert certs/client.crt \
     --key certs/client.key \
     -X POST \
     https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/retrieve \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     -H "Content-Type: application/json" \
     -d @json/NSC-request-MIN.json
```

**Retrieve a record (MAX):**

```bash
curl --cacert certs/ca.crt \
     --cert certs/client.crt \
     --key certs/client.key \
     -X POST \
     https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/retrieve \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     -H "Content-Type: application/json" \
     -d @json/NSC-request-MAX.json
```

**Update a record:**

```bash
curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key \
     -X POST \
     https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/update \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     -H "Content-Type: application/json" \
     -d @json/NSC-request-MAX.json
```

**Delete a record:**

```bash
curl --cacert certs/ca.crt --cert certs/client.crt --key certs/client.key \
     -X POST \
     https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/delete \
     -H "Authorization: Bearer <access_token_from_step_4>" \
     -H "Content-Type: application/json" \
     -d @json/NSC-request-MAX.json
```

Invalid requests and missing records return the error shape defined in `json/NSC-response-Error.json`.

---

## Seeder

The seeder is a developer convenience tool that populates the local database with realistic synthetic NSC records. This is useful for testing pagination, filtering, edge cases, and UI rendering without having to craft request JSON by hand.

It handles the full flow automatically — generating valid synthetic data, obtaining an OAuth token, and posting records through the mTLS-protected API — so you can go from an empty database to a populated one with a single command.

The seeder:

- Generates synthetic NSC request JSON matching `NSC-Request-schema.jschema`
- Generates valid SSNs, names, dates, optional middle names, and previous names
- Obtains an OAuth token from the local auth service
- Uses the local CA and client certificate for mTLS
- Creates records through `https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService/create`

NOTE: The name generation is from a static list currently. The list must be updated in [seed_records.py](seed/seed_records.py), FIRST_NAMES and LAST_NAMES variables.

### CLI Commands

**Run 10 random records:**

```bash
cd mock-service
python3 seed/seed_records.py --count 10
```

**Generate MIN-style requests** (minimum required fields only):

```bash
cd mock-service
python3 seed/seed_records.py --count 10 --mode min
```

**Generate MAX-style requests** (all optional fields populated):

```bash
cd mock-service
python3 seed/seed_records.py --count 10 --mode max
```

**Preview without modifying the database** — useful for inspecting generated data before committing it:

```bash
cd mock-service
python3 seed/seed_records.py --count 3 --seed 42 --dry-run
```

The `--seed` flag makes the output deterministic, which is handy for reproducible test scenarios. See [seed/README.md](seed/README.md) for full CLI reference.

---

## Extending Services

The API is structured to make adding new domains low-friction. Each domain is self-contained in its own directory under `app/domains/`, with its own router, schemas, and model. You do not need to modify any existing domain code to add a new one.

### Adding a New Domain

1. Add a SQLAlchemy model in `app/models/<domain>.py`
2. Import it in `migrations/env.py` so Alembic's autogenerate picks it up
3. Add Pydantic request/response schemas in `app/schemas/<domain>.py`
4. Add a router in `app/domains/<domain>/router.py` with an appropriate URL prefix
5. Register the router in `app/main.py` with `app.include_router(...)`
6. Generate and review the migration:

```bash
uv run alembic revision --autogenerate -m "add <domain> table"
```

Always review the generated migration file before committing — autogenerate is accurate for most cases but does not detect every schema change (e.g., check constraints, custom types).

---

## Test Execution

Tests live in `test/` and use property-based testing to validate the NSC schema contract. Property-based tests are particularly well-suited here because they generate a large variety of inputs automatically, surfacing edge cases that hand-written examples would miss.

```bash
cd mock-service/api
uv sync
uv run pytest ../test/test_nsc_property.py -q
```

The test suite covers:

- MIN request schema validation
- MAX request schema validation
- Generated valid requests
- Rejection of unexpected properties
- `termsAcceptedIndicator` enforcement
- Invalid SSN rejection
- MIN response validation
- MAX response validation
- Previous-name ordering
- Serialized response schema validation

When adding a new domain, add a corresponding test file in `test/` following the same property-based pattern.

---

## Future Tasks

- Update endpoints: The current endpoints are not the same as the FDSH service. The current endpoints implement CRUD operations.
- Custom error messages: Not all error messages provided by the FDSH is implement. Investigate which ones make sense to implement in the mock service.