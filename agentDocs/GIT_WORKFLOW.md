# Agent Git workflow

This document defines the least complex safe repository workflow for agents working on `KreutzM/nvda`. The mandatory fork-wide rules are in the repository-root `AGENTS.md`.

## Goals

* Start from a verified current target branch.
* Prefer normal Git transport whenever it works.
* Use the GitHub connector as a reliable fallback for ordinary repository work.
* Keep feature branches reviewable and avoid direct development on `master`.
* Treat submodule Gitlinks and byte-sensitive files explicitly.
* Verify the final branch diff before opening or updating a pull request.
* Allow useful Actions artifacts while keeping size, frequency, duplication, and retention proportional to their purpose.

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

When roadmap work is intentionally split into dependent pull requests, a temporary stacked branch may be based on the preceding feature branch. The pull request should then target that preceding branch so the diff contains only the new layer. Rebase, recreate, or retarget the stacked pull request after its dependency is merged.

Do not use NVDA's `try-*` branch naming for ordinary agent work because those names have repository-specific CI/release semantics.

### Normalize stacked branches after a squash merge

A squash merge changes commit ancestry even when the resulting `master` tree contains exactly the files expected from the parent pull request. A child branch that still descends from the pre-squash parent commits does not automatically descend from the new squash commit.

Do not assume that simply retargeting such a child pull request to `master` will preserve its layer-only diff. GitHub can show the already-merged parent changes again because the merge base is still the old stack ancestry.

After a stacked dependency is squash-merged:

1. Read the new target branch commit SHA.
2. Determine the exact desired child-layer tree and verify that it contains the merged parent state plus only the child's intended changes.
3. Rebase, recreate, or deliberately reparent the child branch onto the new target commit.
4. Compare the rewritten child branch with its new intended base.
5. Require `behind_by == 0` and only the child's expected paths before merging it.
6. Repeat from the bottom of a longer stack so every child directly follows its newly normalized parent.

For connector-only work, when the child tree has already been independently verified, an exact Git-data normalization may create a new commit whose tree is that verified child tree and whose parent is the current intended target commit, then force-update the feature branch deliberately. Use this only for planned stack normalization; do not rewrite branches casually.

Matching file trees are not a substitute for correct ancestry. Verify both the tree/diff and the commit relationship after every stack rewrite.

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
    prepare an exact Git-data plan with agentTools/prepareConnectorPublish.py.
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

For intentional stacked work, replace `master` in the branch-creation step with the verified current parent branch that will be the pull request's intended base.

### Connector-only path

When normal Git transport is unavailable:

1. Read repository metadata or the intended target branch ref.
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

Ordinary connector text-file operations are not valid for changing a submodule pointer. Use normal Git when possible or the exact Git-data publisher described below.

## 4. Choose direct connector operations for normal text changes

Direct connector operations are the preferred fallback for Markdown, Python, YAML, TOML, JSON, and other ordinary UTF-8 text when byte identity and mode metadata are not special requirements.

Typical sequence:

1. Create the feature branch from the current intended target.
2. Fetch files being modified and retain their current blob SHAs.
3. Apply focused creates, updates, or deletions.
4. For repeated updates to one file, use the SHA returned by the preceding write.
5. Compare the finished feature branch with its intended target.
6. Open or update a draft pull request only after the diff is verified.

Each contents operation may create a separate commit. That is acceptable for a feature branch intended for squash merge.

## 5. Use exact Git-data publication for special cases

Use `agentTools/prepareConnectorPublish.py` when at least one of these properties materially matters:

* exact binary bytes;
* non-UTF-8 content;
* line-ending preservation that ordinary text operations cannot safely guarantee;
* executable or symlink modes;
* submodule Gitlinks;
* a generated payload that should be transferred from verified Git objects;
* a many-file update that must appear atomically as one tree;
* explicit verification that a prepared local tree exactly matches the published tree.

The tool reads committed Git objects rather than working-tree text. It supports normal blobs, executable/symlink blob modes, deletions, renames, and submodule Gitlinks with mode `160000` and object type `commit`.

The working tree must be clean and the local base must be an ancestor of the head being published.

Example:

```powershell
python agentTools\prepareConnectorPublish.py `
  --base-ref <verified-local-base-ref> `
  --head-ref HEAD `
  --repository KreutzM/nvda `
  --remote-base-commit <current-remote-target-sha> `
  --expected-base-tree <current-remote-target-tree-sha> `
  --branch agent/<description> `
  --output-dir .agent-publish
```

`.agent-publish/` is ignored by Git and should remain local or be transferred only as a temporary publication payload when needed.

Required publication sequence:

1. Create each blob described by `blobs/*.json` and require the returned SHA to equal the manifest SHA.
2. Create the tree from `create-tree.json`; Gitlink entries use mode `160000`, type `commit`, and the exact submodule commit SHA.
3. Require the returned tree SHA to equal the plan's `expected_tree`.
4. Create the commit from `create-commit-template.json` with the verified remote target commit as parent.
5. Create the feature branch from that commit.
6. Compare the branch with the intended target and require `behind_by == 0` plus only expected paths.
7. Open a draft pull request.

Stop immediately on the first base-tree, blob, tree, or Gitlink SHA mismatch. Do not recover by copying/re-encoding text or converting a Gitlink into a blob.

## 6. Validate before publication

Run only checks appropriate to the changed area and report them using the levels in `VALIDATION.md`.

For a local branch, useful repository-state checks include:

```powershell
git status --short
git diff --check
git diff --stat
git diff --submodule=log <intended-base>...HEAD
```

For ordinary work `<intended-base>` is `master`. For an intentional stacked pull request it is the preceding feature branch until that dependency is merged and the child is normalized onto its new base.

Use the existing NVDA validation commands rather than inventing replacements. `projectDocs/testing/automated.md` is authoritative for current lint, translation, unit-test, system-test, and license-check mechanics.

Connector-only inspection cannot substitute for a Windows source build or runtime test.

## 7. Verify the complete branch diff

Before opening or updating a pull request, compare the feature branch against its intended base and require:

* the merge base is the intended target state;
* the branch is not unexpectedly behind the intended base;
* changed paths are exactly the task's intended paths;
* additions and deletions are plausible;
* no caches, environments, build output, generated diagnostics, or accidental downloads are committed;
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

After a stacked dependency is squash-merged, normalize the child branch before retargeting/merging it and re-run the complete intended-base comparison. Do not infer that the child remains layer-clean from its previous diff.

Do not merge unless the user explicitly authorizes the merge.

## 9. GitHub Actions artifacts and storage

The existing NVDA workflows are the primary product CI. Useful artifacts are allowed when they materially improve validation, reproducibility, debugging, publication, or agent access.

For any new or modified artifact upload, consider:

* expected compressed and uncompressed size;
* how often the workflow triggers;
* whether another workflow already produces equivalent data;
* which consumer needs the artifact;
* the shortest practical retention period.

Temporary agent snapshots, Git bundles, context packs, diagnostics, and similar artifacts should normally expire after days rather than weeks or months unless a longer retention has a stated purpose.

Large artifacts should use narrow triggers or opt-in workflows where practical. Small diagnostics can be more frequent when their storage cost remains negligible.

Do not download large artifacts merely to prove that they exist; inspect metadata first and fetch contents only when the contents are needed.

## Prohibited shortcuts

* Direct development on `master`.
* Repeatedly retrying transport already known to be unavailable.
* Starting from a stale or unknown base.
* Replacing an existing connector file without first obtaining its current blob SHA.
* Treating a set of downloaded files as a verified local checkout.
* Publishing a Gitlink as ordinary text or blob content.
* Accepting a blob, tree, base-tree, or Gitlink mismatch in an exact-publication path.
* Retargeting a post-squash stacked child without re-verifying its ancestry and layer-only diff.
* Keeping large or frequently generated Actions artifacts for long retention without a concrete need.
* Reporting CI as local execution or inspection as runtime validation.
