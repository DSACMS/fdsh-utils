# FDSH Hub Service Specifications

**Disclaimer: This project is not official FDSH documentation or part of the official FDSH product; see [DISCLAIMER.md](../DISCLAIMER.md).**

This directory is the project root for FDSH hub service OpenAPI documentation in
FDSH Utils. It gives readers a map of the service specification file tree.
Service-specific purpose, authoring, local development, validation, and security
guidance belongs in each service README.

The current documented service is the MEDH NSC endpoint.

## What to Expect

* Hub service specifications are grouped by service area, then by service.
* Each service directory should include its own README and OpenAPI source files.
* Shared material that applies across hub services lives under `shared/`.

## File Tree

```text
.
├── README.md
├── shared/
└── medh/
    └── nsc/
        ├── README.md
        ├── package.json
        ├── openapi.yml
        ├── paths/
        └── schemas/
```

* `README.md`: This file-tree overview.
* `shared/`: Cross-service OpenAPI fragments for hub-wide requirements.
* `shared/security-schemes.yml`: Shared security schemes for FDSH JSON
  endpoints.
* `medh/`: MEDH service specifications.
* `medh/nsc/`: Current MEDH NSC endpoint specification.
* `medh/nsc/README.md`: Service-level documentation, including local
  development and validation guidance.
* `medh/nsc/openapi.yml`: OpenAPI entrypoint for the MEDH NSC specification.
* `medh/nsc/paths/`: Operation path fragments referenced by the OpenAPI
  entrypoint.
* `medh/nsc/schemas/`: JSON Schema source files used by the specification.

## Current Service Documentation

* [MEDH NSC Service Specifications](medh/nsc/README.md)
