# FDSH Mock Service

**Disclaimer: This project is not official FDSH documentation or part of the official FDSH product; see [DISCLAIMER.md](../DISCLAIMER.md).**

This project defines the expected behavior for a future Dockerized mock service
that behaves as closely as practical to FDSH for local integration testing. It
is intended for developers who need a local target for mTLS, OAuth 2.0 client
credentials, and synthetic FDSH-like response behavior before connecting to
shared or live environments.

## Purpose

The mock service project exists to make FDSH integration development faster,
safer, and more repeatable. Its deliverable goal is a Docker image that exposes
FDSH-like endpoints, enforces the authentication behaviors described in
[`specs.md`](specs.md), and returns high-quality synthetic data for local tests.

The immediate audience is contributors designing or implementing the mock
service. A secondary audience is developers who will eventually run the image as
a local dependency in application integration tests.

## Relationship to FDSH Utils

This is a draft sub-project within FDSH Utils. It complements the service
specification work under [`../specs/`](../specs/) by defining runtime behavior
for local testing rather than service-contract source files.

The project is not independently runnable yet. At present, it contains behavior
requirements only; future implementation work should add local source files,
container build configuration, fixtures, and executable validation targets here.

## Scope and Non-goals

Current scope:

* Behavior requirements for an FDSH-like local mock service.
* mTLS expectations, including TLS 1.2-only behavior and client certificate
  validation.
* OAuth 2.0 client credentials token endpoint behavior.
* Synthetic data expectations for future endpoint responses and fixtures.

Non-goals:

* Official FDSH documentation or certification evidence.
* Production connectivity, production credentials, or production data.
* A full FDSH replacement for performance, availability, or security testing.
* Exact behavior for cases marked unknown in [`specs.md`](specs.md) until those
  cases are verified and documented.

## Repository Structure

```text
.
├── README.md
└── specs.md
```

* `README.md`: Project overview, contribution guidance, and local policy
  expectations for the mock service sub-project.
* `specs.md`: Source behavior notes for the expected Docker image, including
  mTLS and OAuth token endpoint test cases.

## Source of Truth and Generated Artifacts

[`specs.md`](specs.md) is the current source of truth for expected mock-service
behavior. Contributors should update it when expected runtime behavior changes
or when an unknown behavior is verified.

No generated artifacts are currently committed. Future generated artifacts,
such as Docker images, bundled fixtures, SDKs, clients, or test reports, should
be reproducible from committed source files and should not be hand-edited.

When implementation files are added, document the exact regeneration or build
command in this README and make stale generated output detectable through local
validation.

## Local Development

Install repository tooling from the repository root:

```sh
pnpm install
```

There is no mock-service package, Dockerfile, or run command yet. No
credentials, certificates, tokens, private keys, or environment variables are
required to read or edit the current documentation.

Future local runtime instructions should include the Docker image build command,
the container run command, required test-only certificate material, and any
synthetic OAuth client configuration.

## Validation and Tests

Run documentation checks from the repository root before opening a pull request:

```sh
pnpm run lint:disclaimer
pnpm run lint:markdown
pnpm run spellcheck
```

There are no mock-service-specific executable tests yet. When implementation is
added, this project should include validation for at least:

* Rejected requests without an acceptable client certificate.
* Rejected requests using unsupported TLS versions.
* OAuth token endpoint error responses for invalid grant types and invalid
  credentials.
* OAuth token endpoint success responses for valid synthetic client
  credentials.
* Synthetic endpoint data that avoids real person, organization, credential, or
  system information.

## Versioning and Releases

This project does not currently have an independent version or release process.
The first release boundary should be defined when the Docker image and its test
fixtures become runnable.

A breaking change is any change that requires a consuming local integration
test, fixture contract, certificate setup, OAuth client setup, endpoint path,
request shape, or response shape to change.

## Contributing

For repository-wide contribution guidance, see the top-level
[`CONTRIBUTING.md`](../CONTRIBUTING.md).

When changing this sub-project:

* Keep expected behavior concrete enough to test.
* Preserve unknown behavior as explicit unknowns rather than guessing.
* Use synthetic fixtures and test-only credentials only.
* Add or update local validation commands when executable behavior is added.
* Prefer small, reviewable behavior increments over a broad mock-service surface
  that is difficult to verify.

## Security, Privacy, and Sensitive Data

For vulnerability reporting, see the top-level
[`SECURITY.md`](../SECURITY.md).

Use synthetic examples and fixtures. Do not commit credentials, certificates,
tokens, private keys, non-public PII, PHI, FTI, production data, internal-only
URLs, network paths, system names, or operational details unless approved for
public release.

Future test certificates, OAuth clients, and secrets must be clearly synthetic,
local-only, and invalid for any real environment.

## Policies

This project inherits repository-level open source policy, licensing,
governance, security, and community expectations from the FDSH Utils repository.
See the top-level [`LICENSE`](../LICENSE),
[`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md),
[`CONTRIBUTING.md`](../CONTRIBUTING.md), [`SECURITY.md`](../SECURITY.md),
[`GOVERNANCE.md`](../GOVERNANCE.md), and
[`DISCLAIMER.md`](../DISCLAIMER.md).
