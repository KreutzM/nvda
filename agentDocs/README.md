# Agent documentation

This directory contains compact operational documentation for coding agents working on `KreutzM/nvda`.

The goal is not to duplicate NVDA's existing developer documentation. Agent documents provide routing, repository orientation, and fork-specific workflow rules so an agent can find the authoritative technical material quickly and can make reliable changes through either a normal local Git checkout or the GitHub connector.

## Start here

Read the repository-root `AGENTS.md` first. It defines fork identity, instruction precedence, validation claims, branch workflow, connector behavior, Actions storage discipline, and submodule handling.

Then use these guides as needed:

* `REPOSITORY_MAP.md` to identify the subsystem, nearby tests, and authoritative repository documentation.
* `GIT_WORKFLOW.md` for local Git, connector publication, feature branches, Gitlinks, pull requests, and storage-aware Actions usage.
* `VALIDATION.md` for V0-V3 validation levels and truthful reporting of inspection, static checks, Windows execution, and CI results.

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

Current foundation:

* `REPOSITORY_MAP.md` for repository navigation.
* `GIT_WORKFLOW.md` for publication and branch integrity.
* `VALIDATION.md` for validation evidence and reporting.

Planned next documents and tooling:

* `CHANGE_IMPACT.md`: mapping from changed areas to likely tests, documentation, and risk checks.
* connector publication tooling with explicit Gitlink/submodule support and tests.
* agent-infrastructure CI that avoids large or long-lived uploaded artifacts.
* `domains/MAGNIFIER.md`: the first subsystem-specific context guide and pilot for domain documentation.

Add further domain guides only when repeated agent work demonstrates that they reduce repository-discovery cost.

## Design principles

* Keep root instructions short enough to be read on every task.
* Link to existing NVDA documentation instead of copying it.
* Prefer deterministic repository state over inferred state.
* Prefer normal Git when it works and the GitHub connector when Git transport is unavailable.
* Separate inspection, static validation, Windows execution, and CI results.
* Keep agent infrastructure independent from NVDA product logic wherever practical.
* Treat submodules and native Windows boundaries explicitly rather than as ordinary Python files.
* Avoid large persistent GitHub Actions artifacts; prefer logs, checks, and job summaries.
