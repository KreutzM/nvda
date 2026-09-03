# Agent Git workflow

This document defines the least complex safe repository workflow for agents working on `KreutzM/nvda`. The mandatory fork-wide rules are in the repository-root `AGENTS.md`.

## Goals

* Start from a verified current target branch.
* Prefer normal Git transport whenever it works.
* Use the GitHub connector as a reliable fallback for ordinary repository work.
* Keep feature branches reviewable and avoid direct development on `master`.
* Treat submodule Gitlinks and byte-sensitive files explicitly.
* Verify the final branch diff before opening or updating a pull request.
* Avoid large or persistent GitHub Actions artifacts unless they are genuinely required.

## Branch model

The normal agent branch model is:

```text
master
  |
  +-- agent/<description>
        |
        +-- focused commits
        +-- validation
        +-- draft pull request
```

When roadmap work is intentionally split into dependent pull requests, a temporary stacked branch may be based on the preceding feature branch. The pull request should then target that preceding branch so the diff contains only the new layer. Rebase or retarget the stacked pull request after its dependency is merged.

Do not use NVDA's `try-*` branch naming for ordinary agent work because those names have repository-specific CI/release semantics.

## 1. Select the publication path

Use this decision order:

```text
Normal authenticated Git transport works?
|-- Yes: use a normal recursive local checkout and git push.
`-- No: use the GitHub connector.

Connector publication needed?
|-- Ordinary UTF-8 text:
|   create branch, read current file, use contents operations.
`-- Binary, byte-sensitive, mode-sensitive, Gitlink, or atomic change:
    use the Git-data path after connector tooling supports the case safely.
```

Do not choose low-level Git-data operations merely to reduce the number of commits created by connector contents operations.

## 2. Establish an exact base

### Local Git path

For a new checkout:

```powershell
git clone --recursive https://github.com/KreutzM/nvda.git
cd nvda
git switch master
git pull --ff-only
git submodule update --init --recursive
git switch -c agent/<description>
```

For an existing checkout:

```powershell
git fetch origin --prune
git switch master
git pull --ff-only
git submodule update --init --recursive
git switch -c agent/<description>
```

Before changing files, confirm the working tree state with `git status --short`.

### Connector-only path

When normal Git transport is unavailable:

1. Read repository metadata or the target branch ref.
2. Record the exact current target commit SHA.
3. Create `agent/<description>` from that exact ref or SHA.
4. Fetch every existing file that will be replaced or deleted before writing it.
5. Use the returned current blob SHA for updates and deletions.
6. Create new UTF-8 text files directly on the feature branch.
7. Never write the task directly to `master`.

Downloaded individual files are sufficient for inspection and connector edits, but they are not a verified local checkout and must not be described as one.

## 3. Work with submodules deliberately

NVDA uses multiple Git submodules.

For local work:

```powershell
git submodule status --recursive
git submodule update --init --recursive
```

After a pull, merge, rebase, branch switch, or dependency update that can change Gitlinks, refresh submodules before build or runtime validation.

A submodule pointer in the parent repository is a Git tree entry with mode `160000` and object type `commit`. It is not a normal file blob.

Until the repository's connector publisher explicitly supports Gitlinks, do not attempt to publish a submodule-pointer change through ordinary connector text-file operations. Record the limitation and use normal Git or a verified Git-data path instead.

## 4. Choose direct connector operations for normal text changes

Direct connector operations are the preferred fallback for Markdown, Python, YAML, TOML, JSON, and other ordinary UTF-8 text when byte identity and mode metadata are not special requirements.

Typical sequence:

1. Create the feature branch from the current target.
2. Fetch files being modified and retain their current blob SHAs.
3. Apply focused creates, updates, or deletions.
4. For repeated updates to one file, use the SHA returned by the preceding write.
5. Compare the finished feature branch with its target.
6. Open or update a draft pull request only after the diff is verified.

Each contents operation may create a separate commit. That is acceptable for a feature branch intended for squash merge.

## 5. Reserve Git-data publication for special cases

Use blob/tree/commit operations only when at least one of these properties materially matters:

* exact binary bytes;
* non-UTF-8 content;
* line-ending preservation that ordinary text operations cannot safely guarantee;
* executable or symlink modes;
* submodule Gitlinks;
* a generated payload that should be transferred from verified Git objects;
* a many-file update that must appear atomically as one tree;
* explicit verification that a prepared local tree exactly matches the published tree.

The NVDA connector publisher planned under the agent roadmap must support and test Gitlinks before it is treated as a general substitute for normal Git.

Stop publication if the expected base tree, blob SHA, tree SHA, or Gitlink SHA does not match the verified source state.

## 6. Validate before publication

Run only checks appropriate to the changed area and report them using the levels in `VALIDATION.md`.

For a local branch, useful repository-state checks include:

```powershell
git status --short
git diff --check
git diff --stat
git diff --submodule=log master...HEAD
```

Use the existing NVDA validation commands rather than inventing replacements. `projectDocs/testing/automated.md` is authoritative for current lint, translation, unit-test, system-test, and license-check mechanics.

Connector-only inspection cannot substitute for a Windows source build or runtime test.

## 7. Verify the complete branch diff

Before opening or updating a pull request, compare the feature branch against its intended base and require:

* the merge base is the intended target state;
* the branch is not unexpectedly behind the intended base;
* changed paths are exactly the task's intended paths;
* additions and deletions are plausible;
* no caches, environments, build output, generated diagnostics, or accidental downloads are present;
* submodule changes are intentional and show the expected Gitlink commits;
* validation claims match checks actually executed.

If the target branch moved during a connector-only change, reassess the branch before publication. Rebase, merge, recreate, or retarget as appropriate; do not silently overwrite concurrent target changes.

## 8. Pull requests

Use draft pull requests for agent-created work until the change is ready for final review.

The pull-request description should state:

* what changed and why;
* the base branch and publication path;
* checks actually executed;
* checks delegated to GitHub Actions or a Windows environment;
* any unvalidated hardware, application, or runtime behavior;
* whether the PR is stacked on another agent PR.

Do not merge unless the user explicitly authorizes the merge.

## 9. GitHub Actions and storage

The existing NVDA workflows are the primary product CI. Do not duplicate their build artifacts in agent-specific workflows.

For agent infrastructure:

* prefer jobs that emit logs, annotations, or job summaries and upload nothing;
* avoid repository snapshots, full Git bundles, source-tree ZIPs, installers, symbols, or duplicate build artifacts;
* if an artifact is strictly required, keep its contents narrow and use the shortest practical retention period;
* do not add an artifact merely so an agent can inspect information already available through the repository or workflow logs.

Storage-sensitive context packaging, if ever added, should be opt-in and domain-scoped rather than a persistent full-repository snapshot.

## Prohibited shortcuts

* Direct development on `master`.
* Repeatedly retrying transport already known to be unavailable.
* Starting from a stale or unknown base.
* Replacing an existing connector file without first obtaining its current blob SHA.
* Treating a set of downloaded files as a verified local checkout.
* Publishing a Gitlink as ordinary text or blob content.
* Accepting a blob, tree, base-tree, or Gitlink mismatch in an exact-publication path.
* Creating large persistent Actions artifacts for convenience.
* Reporting CI as local execution or inspection as runtime validation.
