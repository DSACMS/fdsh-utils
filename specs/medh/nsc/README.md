# MEDH NSC Service Specifications

**Disclaimer: This project is not official FDSH documentation or part of the official FDSH product; see [DISCLAIMER.md](../../../DISCLAIMER.md).**

This project contains the OpenAPI and JSON Schema source files for the
MEDH National Student Clearinghouse (`NSC`) education service.

## Purpose

The MEDH NSC specification project documents the FDSH service contract for
Medicaid-related postsecondary enrollment verification through NSC. It is
intended for developers, reviewers, and partner teams that need to understand,
mock, validate, or generate tooling from the service interface.

## Scope and Non-goals

This project covers the MEDH NSC service specification source files and local
validation workflow.

Current scope:

* OpenAPI 3.1 source for the MEDH NSC service.
* JSON Schema source files used by the OpenAPI document.
* Path fragments referenced by the OpenAPI entrypoint.
* Local linting, schema validation, and bundling commands.
* Synthetic examples and fixtures when they are added.

## Repository Structure

```text
.
├── README.md
├── package.json
├── openapi.yml
├── paths/
└── schemas/
```

* `README.md`: Service-level guidance for the MEDH NSC specification workspace.
* `package.json`: Local package metadata, validation scripts, and tooling
  dependencies.
* `openapi.yml`: OpenAPI entrypoint for the MEDH NSC service. It is currently a
  placeholder for linter development, defines service server variables, and
  references shared FDSH security schemes from `../../shared/`.
* `paths/`: Operation path fragments referenced by `openapi.yml`.
* `schemas/`: JSON Schema source files used by the service specification.

## Source of Truth and Generated Artifacts

The source-of-truth files are `openapi.yml`, `paths/`, and `schemas/`.
Contributors should update those files before changing generated or downstream
artifacts.

Generated SDKs, validators, mock servers, tests, published bundles, bundled
OpenAPI files, or dereferenced OpenAPI files should be generated from or
validated against these source files. Do not hand-edit generated outputs.

The `bundle` script creates `openapi.bundled.yml` for local inspection. Do not
commit generated bundles unless a future change documents why they are committed
and how to regenerate them.

## Local Development

Install dependencies from the repository root:

```sh
pnpm install
```

Run NSC-specific checks from the repository root:

```sh
pnpm --filter @fdsh-utils/spec-medh-nsc lint
```

No credentials or environment variables are required for the current local
specification validation workflow.

## Validation and Tests

Run all current NSC specification checks:

```sh
pnpm --filter @fdsh-utils/spec-medh-nsc test
```

Run individual checks:

```sh
pnpm --filter @fdsh-utils/spec-medh-nsc lint:openapi
pnpm --filter @fdsh-utils/spec-medh-nsc validate:schemas
pnpm --filter @fdsh-utils/spec-medh-nsc bundle
```

Available package scripts:

* `lint`: Runs OpenAPI linting and JSON Schema validation.
* `lint:openapi`: Runs Redocly against `openapi.yml`.
* `validate:schemas`: Compiles JSON Schema files in `schemas/`.
* `bundle`: Creates `openapi.bundled.yml` for local inspection.
* `test`: Runs the current linting workflow.

## Authoring Conventions

* Prefer OpenAPI 3.1 so the OpenAPI document can use JSON Schema draft 2020-12
  semantics.
* Keep JSON Schemas independently useful; do not bury important schema
  constraints only inside OpenAPI operation definitions.
* Use stable, descriptive schema names instead of names tied to implementation
  classes.
* Prefer small, reviewable files over one large bundled OpenAPI document.
* Define service-specific gateway hosts with OpenAPI Server Variables in
  `openapi.yml`; keep shared OAuth endpoint URLs relative when they depend on
  the selected service server.
* Reference hub-wide security schemes from `../../shared/security-schemes.yml`
  instead of redefining mTLS or OAuth 2.0 client credentials locally.
* Keep generated SDK, server, validator, and mock artifacts outside this
  service directory unless the generated-output policy changes.

## Versioning and Releases

This service specification does not currently have an independent release
process. The local package version supports workspace tooling and should not be
treated as an official FDSH service version.

A breaking change is any change that would require an existing consumer, mock,
SDK, validator, or integration test to change its expected request or response
contract.

## Contributing

For repository-wide contribution guidance, see the top-level
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md).

When changing this service specification:

* Update source specification files before generated or downstream artifacts.
* Keep examples and fixtures synthetic.
* Document incomplete, placeholder, or illustrative coverage in this README or
  the relevant source file.
* Run the NSC validation commands before opening a pull request.
* Put guidance that applies across all hub service specifications in
  `../../README.md` or a future shared specification area.
* If MEDH-specific cross-service guidance becomes necessary, add that structure
  deliberately and update `../../README.md` so the file tree remains accurate.

## Security, Privacy, and Sensitive Data

For vulnerability reporting, see the top-level
[`SECURITY.md`](../../../SECURITY.md).

This specification workspace should describe the wire contract, but it must not
encourage use of real beneficiary data in examples, tests, fixtures, or
mock-server behavior.

Use synthetic data only. Do not commit real SSNs, real student data, real
requester identifiers, access tokens, certificates, private keys, live endpoint
credentials, non-public PII, PHI, FTI, internal-only URLs, network paths, system
names, or operational details unless approved for public release.

## Policies

This project inherits repository-level open source policy, licensing,
governance, security, and community expectations from the FDSH Utils repository.
See the top-level [`LICENSE`](../../../LICENSE),
[`CODE_OF_CONDUCT.md`](../../../CODE_OF_CONDUCT.md),
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md),
[`SECURITY.md`](../../../SECURITY.md), [`GOVERNANCE.md`](../../../GOVERNANCE.md),
and [`DISCLAIMER.md`](../../../DISCLAIMER.md).
