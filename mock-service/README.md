# FDSH Mock Service: Complete Guide

**Disclaimer:** This project is not an official FDSH documentation or part of the
official FDSH product. See the repository [DISCLAIMER.md](../DISCLAIMER.md).

This project provides a local, Dockerized FDSH-like mock service for integration
development. It supports mTLS, OAuth 2.0 client credentials, JWT bearer token
validation, synthetic NSC retrieve responses, and executable unit,
property-based, and BDD tests.

## Contents

1. [Purpose and Scope](#purpose-and-scope)
2. [Project Structure](#project-structure)
3. [Runtime Architecture](#runtime-architecture)
4. [Prerequisites](#prerequisites)
5. [Build and Run](#build-and-run)
6. [Calling the Service](#calling-the-service)
7. [Testing](#testing)
8. [BDD Development](#bdd-development)
9. [Response Codes and Test Data](#response-codes-and-test-data)
10. [Security and Contribution Rules](#security-and-contribution-rules)

## Purpose and Scope

The mock service is intended for local integration testing before connecting to
shared or live environments. It is retrieve-only: it has no create, update, or
delete operations.

The current public retrieve route is:

```text
POST /mesh/imp1/NationalStudentClearinghouseService
```

The implementation uses synthetic data only. It should never contain real
people, organizations, credentials, production tokens, private keys, or other
non-public operational information.

## Project Structure

```text
mock-service/
├── api/
│   ├── app/
│   │   ├── domains/
│   │   │   └── nsc.py                  # NSC lookup and response handling
│   │   ├── main.py                     # FastAPI retrieve API and validation
│   │   ├── response_codes.py           # MESH response metadata catalog
│   │   └── schemas.py                  # Pydantic request/response schemas
│   └── pyproject.toml
├── auth/
│   ├── app/
│   │   ├── main.py                     # Token and introspection endpoints
│   │   └── security.py                 # JWT issuance and validation
│   └── pyproject.toml
├── certs/
│   ├── check_expiry.sh                 # Certificate expiry check
│   └── generate.sh                     # Local CA, server, and client certs
├── data/
│   ├── generate_records.py             # Synthetic record generator
│   ├── records.json                    # Runtime records bundled into image
│   └── test_records.json               # Deterministic test records
├── json/                               # Example requests, responses, schemas
├── nginx/
│   └── nginx.conf                      # TLS, mTLS, and auth_request config
├── test/
│   ├── features/                       # Gherkin scenarios by MESH code
│   ├── step_defs/
│   │   └── test_nsc_response_codes.py  # Shared pytest-bdd steps
│   ├── mesh_response_codes.csv         # BDD response-code assertions
│   ├── test_property_based.py          # Unit and Hypothesis tests
│   ├── conftest.py                     # Test imports and test data setup
│   ├── pytest.ini                      # Pytest logging configuration
│   ├── run_tests.sh                    # Complete test runner
├── docker-compose.yml                  # Local container orchestration
├── Dockerfile                          # Combined image build
├── README.md                           # Project overview
├── ARCHITECTURE.md                     # Detailed runtime architecture
├── specs.md                            # Mock-service behavior notes
└── supervisord.conf                    # Runs auth, API, and nginx
```

## Runtime Architecture

```text
+--------------------------------------------------------------------------------+
| Host                                                                           |
|  curl / integration client                                                    |
|       | HTTPS 8443, client certificate, bearer token                          |
|       v                                                                        |
|  +------------------------------------------------------------------------+    |
|  | fdsh-mock-service container                                            |    |
|  |  +----------------+       +----------------+       +----------------+ |    |
|  |  | nginx          |------>| auth           |       | API            | |    |
|  |  | TLS 1.2/mTLS   | token | JWT issue      |       | FastAPI        | |    |
|  |  | public :8443   |       | /auth/...      |       | internal :8000 | |    |
|  |  | auth_request   |       | /introspect    |       | /mesh/imp1/... | |    |
|  |  +-------+--------+       | internal :9000 |       | JWT + schema   | |    |
|  |          | proxy + auth  +----------------+       +-------+--------+ |    |
|  |          +---------------------------------------------->| records  | |    |
|  |                                                         +----------------+ |    |
|  +------------------------------------------------------------------------+    |
|                                                                                |
|  test/run_tests.sh -> pytest -> TestClient -> API                             |
|  test/features + step_defs + test_property_based.py + data/test_records.json  |
+--------------------------------------------------------------------------------+
```

At runtime, nginx is the public TLS 1.2 endpoint. It requires a trusted client
certificate and uses the auth service's `/introspect` endpoint to validate the
bearer token before proxying retrieve requests to the API. The API also checks
the JWT scope and validates the NSC request schema before reading
`data/records.json`.

The token endpoint is:

```text
POST https://localhost:8443/auth/oauth/v2/token
```

The API and auth service use the configured JWT signing key. The API port 8000
and auth port 9000 are internal container ports and are not published by
Compose.

## Prerequisites

Use Python 3.12 or newer. Install repository tooling from the repository root:

For Docker execution, install Docker and Docker Compose.

For local tests, use a virtual environment. From `mock-service`:

```sh
python3 -m venv .venv-bdd
source .venv-bdd/bin/activate
python -m pip install \
  fastapi \
  PyJWT \
  pydantic-settings \
  python-multipart \
  pytest \
  hypothesis \
  pytest-bdd \
  httpx2
```

`httpx2` is required because the installed Starlette test client uses it for
its current compatibility path.

## Build and Run

Generate local certificates:

```sh
cd mock-service
./certs/generate.sh
```

The host `certs/` directory must contain only the server-side files mounted
into the container:

```text
ca.crt
server.crt
server.key
```

Keep `client.crt` and `client.key` on the calling host. Do not copy them into
the image or mounted server certificate directory.

Build and start the service:

```sh
docker compose up --build -d
```

The Compose configuration publishes HTTPS on port 8443 and mounts the local
certificates and nginx configuration read-only.

Stop the service:

```sh
docker compose down
```

## Calling the Service

The default local OAuth client is:

```text
client_id: local-dev-client-id
client_secret: local-dev-client-secret
```

Get a token:

```sh
curl --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d grant_type=client_credentials \
  -d client_id=local-dev-client-id \
  -d client_secret=local-dev-client-secret \
  https://localhost:8443/auth/oauth/v2/token
```

Store the returned access token in a shell variable, then retrieve the seeded
Casey Bennett record:

```sh
TOKEN="<access_token>"

curl --cacert certs/ca.crt \
  --cert certs/client.crt \
  --key certs/client.key \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data @json/request.json \
  https://localhost:8443/mesh/imp1/NationalStudentClearinghouseService
```

Create a request.json based on the [nsc-request.schema.json](../specs/medh/nsc/schemas/nsc-request.schema.json).

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

The record must exist in the [records.json](data/records.json) for a successful retrieval.

The minimum request must match a record in `data/records.json` for a successful
lookup. The lookup compares the supplied names, birth date, as-of date, and any
optional fields supplied by the request.

For local curl configuration, `CURL_CA_BUNDLE` may point to the generated CA:

```sh
export CURL_CA_BUNDLE="$PWD/certs/ca.crt"
```

## Testing

The test suite has three layers:

- Regular pytest tests for direct behavior and response model checks.
- Hypothesis property-based tests for generated valid and invalid inputs.
- pytest-bdd scenarios for externally visible response code behavior.

The test bootstrap sets `NSC_DATA_FILE` to `data/test_records.json`, so tests
use deterministic data rather than the runtime dataset.

### Run Everything

From `mock-service`:

```sh
test/run_tests.sh
```

The runner automatically prefers `venvtest/bin/python`, then `.venv/bin/python`,
then `python3`, and finally `python`. It sets:

```text
PYTHONPATH=mock-service/auth:mock-service/api
```

The runner returns pytest's exit code, so it can be used in CI.

### Test Runner Options

Do not write a failure log:

```sh
test/run_tests.sh --no-log
```

This is the default. Write failed-run output to `test/test_run.log`:

```sh
test/run_tests.sh --log
```

`--log` removes a previous log at the start and creates a new one only when
tests fail. Successful runs do not create a log.

Show help:

```sh
test/run_tests.sh --help
```

Only one option may be supplied. Run a focused suite directly when debugging:

```sh
export PYTHONPATH="$PWD/auth:$PWD/api"
venvtest/bin/python -m pytest test/step_defs/test_nsc_response_codes.py -q
venvtest/bin/python -m pytest test/test_property_based.py -q
```

### Look Up a Response Code

Use `test/lookup_response_code.py` to read a response code's MESH response
description and trusted-data-source description from
`test/mesh_response_codes.csv`:

```sh
test/lookup_response_code.py MX009999
```

Example output:

```text
Response code: MX009999
Response description: Unexpected Response Code
Description: Service returned an unknown or unsupported response code.
```

The command accepts exactly one response code. It exits with status `0` when
the code is found, `1` when the code is not in the CSV, and `2` when the
argument is missing or invalid.

## BDD Development

Feature files use Gherkin to describe service behavior in terms that product,
QA, and development can read together. They define the feature purpose and
scenarios, including conditions, actions, and expected outcomes. They should
describe what the service does, not Python implementation details.

Step definition files contain the Python glue that makes Gherkin executable.
They construct request data, submit requests to the FastAPI app, and assert
response fields. They should coordinate tests and assertions; service behavior
belongs in the application modules.

One cohesive feature per `.feature` file is recommended. A feature file should
normally contain several related scenarios, rather than one file per scenario.
This is a convention, not a technical restriction. Step definition modules do
not need a one-to-one relationship with feature files and may support several
related features.

The current feature files cover every response code in
`test/mesh_response_codes.csv`. To add a scenario:

1. Add or update the response code row in the CSV.
2. Add one cohesive `.feature` file under `test/features`.
3. Reuse existing Given/When/Then steps when possible.
4. Add a step definition only for distinct test behavior.
5. Run the focused BDD test.
6. Run `test/run_tests.sh` before handing the change to development.

The in-process BDD suite does not require Docker, nginx, TLS certificates, or a
live OAuth token. Full stack tests should be separate and cover TLS 1.2, mTLS,
nginx forwarding, OAuth token validation, and the public HTTPS route.

## Response Codes and Test Data

The response catalog in `api/app/response_codes.py` supplies the MESH response
code, `responseText`, and trusted-data-source description. The BDD CSV mirrors
that catalog and is used by the step definitions as the assertion source.

The primary configured response codes include:

- `MS000000`: successful request.
- `ME110010`: authentication or authorization failure.
- `ME100005`: insufficient search privileges.
- `ME110020` through `ME110075`: invalid request fields.
- `ME120030` through `ME120045`: invalid previous-name fields.
- `ME007000`: schema validation failure.
- `MX005001`: trusted data source exception.
- `MX009000`: unexpected system exception.
- `MX009999`: unexpected response code.

A missing fixture currently returns `ME123456` with HTTP 404. This is retained
as mock service behavior even though it is not in the response-code CSV.

## Source of Truth and Maintenance

[`specs.md`](specs.md) describes expected mock service behavior. Runtime code,
fixtures, and executable tests show the current implementation. When behavior
changes, update the relevant specification, fixture, feature, and test
instructions together.

Generated artifacts such as Docker images, test reports, and SDKs should be
reproducible and should not be hand edited. Generate or replace
`data/records.json` with `data/generate_records.py` before building an image.

## Security and Contribution Rules

Use only synthetic test data and local only credentials. Never commit:

- Private keys or non-public certificates.
- Access tokens or production credentials.
- Real personal, health, financial, or tax information.
- Production URLs, network paths, or internal operational details.

For repository contribution guidance, see the top level
[`CONTRIBUTING.md`](../CONTRIBUTING.md). For vulnerability reporting, see
[`SECURITY.md`](../SECURITY.md). The project inherits repository-level license,
community, governance, security, and disclaimer policies.
