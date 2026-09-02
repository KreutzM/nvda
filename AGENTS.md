# AGENTS.md

## Scope

These instructions apply to the entire repository.

## Repository identity

* The primary repository is `KreutzM/nvda`.
* The primary development branch is `master`.
* This repository is an independently developed fork of NVDA.
* `nvaccess/nvda` may be consulted as a technical and historical reference, but it is not the publication target for normal work in this repository.
* NV Access contribution-governance requirements do not apply unless a task explicitly asks to prepare work for upstream contribution.

## Instruction precedence

Use the following order when deciding how to work:

1. This `AGENTS.md` defines fork-wide agent workflow and publication rules.
2. Applicable files under `.github/instructions/` define technical rules for specific file types and review contexts.
3. `projectDocs/` defines NVDA architecture, build, testing, documentation, and development procedures.
4. Existing source code and tests define implementation behavior when documentation is incomplete or stale.

Do not duplicate large upstream technical standards into agent documentation. Link to the authoritative repository document instead.

## Environment

* NVDA is a Windows application. Treat Windows as the authoritative runtime and build environment.
* Use the Python version declared by the repository and follow `projectDocs/dev/createDevEnvironment.md` for development setup.
* Clone recursively so required submodules are available.
* After pulls, merges, rebases, or checkouts that may change submodule pointers, update submodules before building or testing.
* A non-Windows environment may be used for repository inspection and platform-independent tooling, but it does not establish that NVDA builds or runs correctly.

## Validation claims

Report only validation that actually ran.

* Repository inspection or reasoning is not a build.
* Static analysis is not a runtime test.
* Connector-based edits are not local execution.
* GitHub Actions results are CI validation, not local validation.
* Do not claim successful NVDA runtime behavior without execution on a suitable Windows environment.
* When a check cannot be run, state that explicitly and identify the check delegated to CI or a Windows developer environment.

## Repository acquisition and GitHub publishing

* Prefer a normal, current local clone and normal `git push` when available.
* Use `git clone --recursive https://github.com/KreutzM/nvda.git` for a new local checkout.
* Probe an unavailable transport only once per task; after a capability is known to be unavailable, use the working path instead of retrying it repeatedly.
* When normal Git push is unavailable, use the GitHub connector for repository reads, branches, ordinary UTF-8 text edits, comparisons, pull requests, and CI inspection.
* Create a feature branch from the current `master` before making changes through the connector.
* Read an existing file before replacing or deleting it and use its current blob SHA for connector writes.
* Direct connector file operations are preferred for ordinary UTF-8 text changes. Several focused commits are acceptable because feature pull requests may be squash-merged.
* Do not use low-level Git-data blob/tree/commit publication merely to reduce commit count. Reserve it for cases that materially require exact bytes, file modes, Gitlinks/submodule pointers, binary data, or atomic publication.
* After connector writes, compare the feature branch with `master` and verify that it is not behind and that only intended paths changed.

## Development workflow

* Do not develop directly on `master`.
* Create focused branches using the `agent/<description>` naming convention for agent-driven work unless a task requires another branch name.
* Keep changes focused and reviewable. Avoid unrelated refactors and mechanical repository-wide rewrites.
* Preserve existing NVDA coding conventions, including the scoped rules in `.github/instructions/`.
* Add or update tests for behavioral changes where practical.
* Prefer targeted tests during development and broader validation before merge when the affected subsystem warrants it.
* Use the existing NVDA build, lint, translation, license, unit-test, and system-test infrastructure instead of creating parallel replacements.
* Avoid committing build output, caches, local virtual environments, generated diagnostics, or other workstation artifacts.

## GitHub Actions storage discipline

GitHub Actions storage is a limited repository resource and must be managed deliberately.

* Useful artifacts are allowed, including snapshots, Git bundles, installers, logs, diagnostics, and context packages when they materially improve validation, reproducibility, debugging, or agent access.
* Prefer logs, job summaries, checks, repository commits, and caches over uploaded artifacts when they provide the same value without persistent storage.
* Keep uploaded artifacts narrowly scoped and avoid duplicating artifacts already produced by another workflow unless the duplicate has a clear operational purpose.
* Use the shortest practical retention period for temporary artifacts. Agent-oriented snapshots, bundles, context packs, and diagnostics should normally be retained for days rather than weeks or months unless a longer period has an explicit purpose.
* Before adding or expanding artifact upload steps, consider expected size, upload frequency, retention, duplication, and whether consumers actually need persistent download access.
* Large or frequently generated artifacts require stronger justification and shorter retention than small diagnostic artifacts.
* Snapshot or context-pack workflows should be opt-in or narrowly triggered when possible rather than creating large persistent artifacts for every repository event.

## Submodules

This repository contains multiple Git submodules that are part of the build and runtime dependency graph.

* Treat submodule pointers as first-class versioned dependencies.
* Do not replace a submodule with copied files unless a task explicitly changes repository architecture.
* When changing a submodule pointer, record the intended submodule commit and verify the parent repository diff.
* Connector tooling must treat Git mode `160000` as a Gitlink, not as a normal file blob.

## Technical guidance

Before modifying a subsystem, read the relevant local documentation and nearby tests instead of inferring architecture from filenames alone.

Useful starting points include:

* `agentDocs/README.md` for agent-oriented navigation.
* `agentDocs/REPOSITORY_MAP.md` for a compact subsystem map.
* `projectDocs/dev/createDevEnvironment.md` for environment setup.
* `projectDocs/dev/buildingNVDA.md` for builds and running from source.
* `projectDocs/testing/automated.md` for automated validation.
* `projectDocs/dev/designOverview.md` for architecture.
* `.github/instructions/python.instructions.md` for Python changes.
* `.github/instructions/cpp.instructions.md` for native C/C++ changes.
* `.github/instructions/userGuide.instructions.md` for English user-guide changes.
* `.github/instructions/review.instructions.md` for review expectations.

## Pull requests in this fork

* Pull requests normally target `KreutzM/nvda:master`.
* Agent-created branches may be published as draft pull requests once they form a coherent reviewable change.
* Before opening a pull request, inspect the complete branch diff against `master` and verify that no accidental files are included.
* Pull-request descriptions must distinguish checks actually executed from checks expected to run in CI.
* Prefer squash merge for connector-generated multi-commit branches unless preserving individual commits has a specific value.
* Do not merge unless the user explicitly requests or authorizes the merge.
