---
name: fdsh-project-readme
description: Create, initialize, or standardize README.md files for projects added inside the FDSH Utils repository. Use when Codex is asked to add a README for a new project directory, improve an existing project README, document a project listed under the top-level README.md, mirror CMS Tier 4 repository scaffold guidance at a project boundary, or decide which repository-level policy files should be inherited rather than duplicated.
---

# FDSH Project README

## Core Rule

Initialize project READMEs so each project is usable on its own while
inheriting repository-level Tier 4 policy files from the FDSH Utils root.

Do not copy the CMS Tier 4 scaffold wholesale into project folders. Keep
these files canonical at the repository root unless the user explicitly asks for
an exceptional local supplement:

* `LICENSE`
* `code.json`
* `CODE_OF_CONDUCT.md`
* `SECURITY.md`
* `CONTRIBUTING.md`
* `COMMUNITY.md`
* `GOVERNANCE.md`
* `repolinter.json`

Create or edit the local `README.md`; add or update local tooling only when the
project has independent validation, build, test, bundling, or packaging.

Every project README must include the repository-standard disclaimer immediately
after the `#` title, with the `DISCLAIMER.md` link calculated relative to that
project directory:

```markdown
**Disclaimer: This project is not official FDSH documentation or part of the official FDSH product; see [DISCLAIMER.md](<relative-path-to-DISCLAIMER.md>).**
```

## Workflow

1. Inspect the project path and classify it:
   * Project directory already listed or intended to be listed in the top-level
     `README.md`.
   * Technical project if it has source files, executable checks, packaging, or
     generated artifacts.
   * Documentation-only if there are no source files or executable checks.
2. Inspect the root files needed for relative links:
   * `README.md`
   * `CONTRIBUTING.md`
   * `SECURITY.md`
   * `GOVERNANCE.md`
   * `CODE_OF_CONDUCT.md`
   * `LICENSE`
   * `DISCLAIMER.md`
   * `package.json` and workspace config when tooling is relevant.
3. Determine whether README-only is enough:
   * Sufficient for documentation-only projects.
   * Not sufficient for SDKs, mock servers, packages, validators, generated
     artifact workflows, or any project with checks.
4. Write the README with the required sections below.
5. Use correct relative links from the project directory to root policy files;
   calculate them from the project path instead of hard-coding a fixed depth.
6. Update the top-level `README.md` so the new project appears in the repository
   structure and documentation index.
7. If creating a new technical project, also check whether root workspace
   scripts, spellcheck vocabulary, and repository-level checks need updates.

## Required README Sections

Use these sections unless the user asks for a shorter draft:

* **Title and Status**: human-readable name, maturity (`draft`,
  `experimental`, `active`, or `deprecated`), and whether contents are source,
  generated artifacts, examples, or supporting docs.
* **Disclaimer**: repository-standard disclaimer immediately below the title,
  linking to root `DISCLAIMER.md` using the correct relative path.
* **Purpose**: the FDSH-related capability, tool, SDK, fixture set,
  specification, mock, or document set covered; user problem; intended
  audience.
* **Relationship to FDSH Utils**: how this project fits the repository,
  dependencies on other projects, and whether it is independently usable.
* **Scope and Non-goals**: what belongs here, what is excluded, completeness
  level, and whether examples are synthetic.
* **Repository Structure**: local tree only, with descriptions of meaningful
  files and folders.
* **Source of Truth and Generated Artifacts**: what to edit by hand, what is
  generated, regeneration command, whether outputs are committed, and stale
  artifact detection.
* **Local Development**: runtime/package-manager prerequisites, install
  command, local run command if applicable, and credentials/environment needs.
* **Validation and Tests**: exact lint, test, bundle, schema, or build commands
  contributors should run before a pull request.
* **Versioning and Releases**: whether the project has an independent
  version/release process and what counts as a breaking change.
* **Contributing**: link to root `CONTRIBUTING.md` and add local conventions.
* **Security, Privacy, and Sensitive Data**: link to root `SECURITY.md`; forbid
  credentials, certificates, tokens, private keys, non-public PII, PHI, FTI,
  production data, internal-only URLs, network paths, system names, or
  operational details unless approved for public release.
* **Policies**: short inherited-policy section linking to root `LICENSE`,
  `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `GOVERNANCE.md`.

## Project Directory Defaults

Use a local structure that matches the project type and keeps the project
discoverable from the top-level `README.md`.

Prefer this minimum shape:

```text
<project-path>/
├── README.md
├── <tool manifest, if needed>
├── <source files or docs>
├── examples/ or fixtures/       # when useful
└── generated/ or dist/          # only if intentionally committed
```

Prefer these conventions for all project types:

* Choose the path from the taxonomy already used in the top-level `README.md`.
* Use lowercase, hyphenated package names when package tooling is present.
* Keep source-of-truth inputs separate from generated outputs.
* Use synthetic examples and fixtures.
* Provide one local `test`, `lint`, or equivalent validation target when the
  project has executable checks.
* Make root-level checks able to call the project-level checks when practical.

## README Template

Adapt this template. Keep wording concrete; remove placeholders before
delivering.

````markdown
# <Project Name>

**Disclaimer: This project is not official FDSH documentation or part of the official FDSH product; see [DISCLAIMER.md](<relative-path-to-DISCLAIMER.md>).**

Status: <draft | experimental | active | deprecated>

<One paragraph describing what this project provides and who it is for.>

## Purpose

<Describe the user problem, FDSH capability, and intended audience.>

## Relationship to FDSH Utils

<Explain how this project fits with the rest of the repository and whether
other projects depend on it.>

## Scope and Non-goals

<List what is covered, intentionally excluded, incomplete, synthetic, or
illustrative.>

## Repository Structure

```text
.
├── README.md
├── <source files>
└── <supporting folders>
```

<Describe each meaningful file or folder.>

## Source of Truth and Generated Artifacts

<State what to edit, what is generated, whether generated files are committed,
and how to regenerate or detect stale output.>

## Local Development

```sh
<install command>
<run command, if applicable>
```

<State whether credentials or environment variables are required.>

## Validation and Tests

```sh
<lint command>
<test command>
<bundle/build command, if applicable>
```

## Versioning and Releases

<State whether the project has independent versions or releases.>

## Contributing

For repository-wide contribution guidance, see the top-level
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md).

<Add project-specific contribution rules.>

## Security, Privacy, and Sensitive Data

For vulnerability reporting, see the top-level
[`SECURITY.md`](../../../SECURITY.md).

Use synthetic examples and fixtures. Do not commit credentials, certificates,
tokens, private keys, non-public PII, PHI, FTI, production data, internal-only
URLs, network paths, system names, or operational details unless approved for
public release.

## Policies

This project inherits repository-level open source policy, licensing,
governance, security, and community expectations from the FDSH Utils repository.
See the top-level `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `GOVERNANCE.md`, and `DISCLAIMER.md` using relative links from
this project directory.
````

## Root Integration Checklist

When initializing a new project, check whether to:

* Update top-level `README.md` repository structure and documentation index.
* Include the repository-standard disclaimer immediately below the project
  README title.
* Add the path to `pnpm-workspace.yaml` or the appropriate workspace manifest.
* Add root scripts so repository-level `lint` and `test` include the
  project.
* Add legitimate domain vocabulary to spellcheck configuration.
* Update root ownership or CODEOWNERS if review responsibility changes.
* Update the single root `code.json` only if repository-level metadata changes.
* Ignore generated or temporary outputs unless they are intentionally committed
  and documented.
