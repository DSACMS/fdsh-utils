---
name: fdsh-openapi-3-2
description: Author, review, update, or validate OpenAPI 3.2 specifications in the FDSH Utils repository. Use when Codex works on specs/, openapi.yml files, split OpenAPI path/schema fragments, JSON Schema draft 2020-12 usage inside OpenAPI, OpenAPI 3.1-to-3.2 decisions, Redocly linting, bundling, or compatibility guidance for FDSH service contracts.
---

# FDSH OpenAPI 3.2

## Core Rule

Use OpenAPI 3.2 deliberately for FDSH service specifications when the project
needs the 3.2 feature set or when the user asks for current OpenAPI 3.2
behavior. Do not treat `3.1.0`, `3.1.2`, and `3.2.0` as interchangeable:
`major.minor` identifies the OpenAPI feature set, while `patch` versions are
clarifications.

## Reference

The full OpenAPI 3.2.0 specification is bundled at:

```text
references/openapi-spec-v3.2.0.md
```

Do not load the whole reference by default. It is large. Use targeted `rg` or
section reads for the object or rule being edited.

Useful search patterns:

* `Versions and Deprecation`
* `OpenAPI Object`
* `OpenAPI Description Structure`
* `Schema Object`
* `JSON Schema Keywords`
* `Specifying Schema Dialects`
* `Reference Object`
* `Relative References in API Description URIs`
* `Parsing and Resolution Guidance`
* `Working with Examples`
* `Media Type Object`
* `Parameter Object`
* `Responses Object`
* `Appendix F`
* `Appendix G`

## Project Workflow

1. Inspect the relevant service directory under `specs/`.
2. Check its local `README.md`, `package.json`, and `openapi.yml` before
   changing version or structure.
3. Prefer the existing split-file layout unless a task requires restructuring.
4. Keep standalone JSON Schema files independently useful where the project has
   a `schemas/` directory.
5. Validate with the service-level scripts after edits when practical:

```sh
pnpm --filter <service-package-name> lint
pnpm --filter <service-package-name> bundle
```

For the MEDH NSC service, use:

```sh
pnpm --filter @fdsh-utils/spec-medh-nsc lint
pnpm --filter @fdsh-utils/spec-medh-nsc bundle
```

## OpenAPI 3.2 Authoring Guidance

* Set `openapi: 3.2.0` only when downstream tooling and consumers can handle
  the 3.2 feature set.
* If the goal is only to avoid stale patch text, prefer `openapi: 3.1.2` over
  `3.1.0`; that keeps the OpenAPI 3.1 feature set.
* Use JSON Schema draft 2020-12 semantics for Schema Objects unless a specific
  `$schema` or `jsonSchemaDialect` requirement says otherwise.
* Be careful with `$self`, `$id`, and relative `$ref` resolution in split-file
  specs. Search the reference for `Appendix F` and `Appendix G` before changing
  base URI or reference behavior.
* Avoid relying on undefined or implementation-defined behavior. If a tool
  accepts something but the spec calls it undefined, document or remove the
  ambiguity.
* Use OpenAPI examples according to their location. Prefer Schema Object
  `examples` for validation-ready data; use Example Object fields when the
  example belongs to parameter, request, response, or media-type documentation.
* Keep examples and fixtures synthetic. Do not include credentials, private
  keys, real beneficiary data, real student data, PHI, FTI, production URLs, or
  internal-only operational details.

## Version Decision Heuristic

When asked whether to use OpenAPI 3.1 or 3.2:

* Recommend `3.1.2` when broad tool compatibility matters and no 3.2 feature is
  needed.
* Recommend `3.2.0` when the repo needs current 3.2 semantics, new 3.2 fields,
  clearer reference behavior, or explicit alignment with the latest OAS feature
  set.
* Check Redocly, code generation, mock server, validator, partner, and
  publishing-tool support before changing an established spec.
