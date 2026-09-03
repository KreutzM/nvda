# Agent documentation

This directory contains compact operational documentation for coding agents working on `KreutzM/nvda`.

The goal is not to duplicate NVDA's existing developer documentation. Agent documents provide routing, repository orientation, fork-specific workflow rules, and repeated-discovery shortcuts so an agent can find authoritative technical material quickly and make reliable changes through either a normal local Git checkout or the GitHub connector.

## Start here

Read the repository-root `AGENTS.md` first. It defines fork identity, instruction precedence, validation claims, branch workflow, connector behavior, Actions storage discipline, and submodule handling.

Then use these guides as needed:

* `REPOSITORY_MAP.md` to identify the subsystem, nearby tests, and authoritative repository documentation.
* `GIT_WORKFLOW.md` for local Git, connector publication, feature branches, Gitlinks, pull requests, and storage-aware Actions usage.
* `VALIDATION.md` for V0-V3 validation levels and truthful reporting of inspection, static checks, Windows execution, and CI results.
* `CHANGE_IMPACT.md` to map a changed area to likely tests, documentation, compatibility, security, runtime, dependency, and CI concerns.
* `domains/MAGNIFIER.md` for the built-in magnifier architecture, native boundary, test map, performance/error invariants, and design questions for docked/lens/fixed modes.

## Authoritative technical documentation

Agent documentation complements, rather than replaces, these existing sources:

* `.github/instructions/` for scoped coding, documentation, and review rules.
* `projectDocs/dev/` for developer environment, architecture, build, and contribution mechanics.
* `projectDocs/testing/` for test strategy and commands.
* `user_docs/` for end-user documentation.
* `tests/` for executable expectations and regression coverage.

When an agent document and an authoritative technical document disagree about NVDA implementation details, prefer the authoritative technical document unless `AGENTS.md` explicitly defines a fork-specific override.

## Roadmap

The agent layer is expanded incrementally rather than created as a large parallel documentation set.

Current documentation and tooling foundation:

* `REPOSITORY_MAP.md` for repository navigation.
* `GIT_WORKFLOW.md` for publication and branch integrity.
* `VALIDATION.md` for validation evidence and reporting.
* `CHANGE_IMPACT.md` for change-to-check and cross-boundary impact routing.
* `agentTools/prepareConnectorPublish.py` and `agentTests/` for exact connector publication including submodule Gitlinks.
* `.github/workflows/agentInfrastructure.yml` for lightweight agent-tool validation.
* `domains/MAGNIFIER.md` as the first subsystem-specific context guide.

Planned next work should be driven by demonstrated need. Candidate areas include storage-aware snapshot/context workflows, artifact-retention tuning in existing fork CI, and additional domain guides for subsystems that repeatedly require expensive rediscovery.

Add further domain guides only when repeated agent work demonstrates that they reduce repository-discovery cost.

## Design principles

* Keep root instructions short enough to be read on every task.
* Link to existing NVDA documentation instead of copying it.
* Prefer deterministic repository state over inferred state.
* Prefer normal Git when it works and the GitHub connector when Git transport is unavailable.
* Separate inspection, static validation, Windows execution, and CI results.
* Keep agent infrastructure independent from NVDA product logic wherever practical.
* Treat submodules and native Windows boundaries explicitly rather than as ordinary Python files.
* Allow useful Actions artifacts, including snapshots and bundles, while keeping size, duplication, trigger frequency, and retention proportional to their purpose.
