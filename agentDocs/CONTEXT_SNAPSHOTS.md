# Agent context snapshots

The fork provides a manual `Agent context snapshot` GitHub Actions workflow for cases where an agent, reviewer, or debugging session benefits from a compact reproducible representation of one exact parent-repository tree.

This is a context/reproducibility aid, not a replacement for a normal recursive NVDA checkout.

## When to use it

Create a context snapshot when one of these is useful:

* a portable copy of the exact tracked parent-repository tree;
* a short-lived artifact for connector-only or review work;
* a reproducible tree reference without carrying the full NVDA Git history;
* a Git-native package that preserves tree modes, symlinks, and submodule Gitlink entries;
* a compact input for later investigation when keeping a full local checkout is unnecessary.

Do not generate snapshots automatically for every push or pull request. The workflow is intentionally manual because NVDA's tree is large enough that repeated snapshots would waste Actions time and storage.

## Running the workflow

Open GitHub Actions, select `Agent context snapshot`, choose the desired ref, and run the workflow with one format:

* `zip` - default; a `git archive` ZIP of the exact parent-repository tree.
* `bundle` - a Git bundle containing a synthetic parentless commit that references the exact source tree.
* `both` - generate both representations in one artifact.

The uploaded artifact is retained for 3 days. The fork-wide artifact cleanup workflow provides an additional backstop for short-lived Actions storage.

## Artifact contents

Every snapshot artifact contains:

* `metadata.json` with repository, source commit SHA, source tree SHA, selected ref, workflow run information, requested format, and snapshot semantics;
* `gitlinks.json` with every mode `160000` / type `commit` entry and its exact submodule commit SHA;
* `SHA256SUMS` covering every file in the snapshot package;
* `nvda-current-tree.zip` when `zip` or `both` is requested;
* `nvda-current-tree.bundle` when `bundle` or `both` is requested.

The workflow derives all snapshot payloads from committed Git objects. It does not include untracked files, local build output, developer environments, connector payload directories, or other working-tree-only data.

## ZIP semantics

`nvda-current-tree.zip` is created with `git archive` from the selected commit.

It contains the exact tracked files represented by the parent repository's tree, under an `nvda/` prefix. It does not contain `.git` history and does not recursively embed the contents of Git submodules.

Use the ZIP when the consumer needs source and documentation files but does not need Git object semantics.

The workflow validates the archive with `unzip -tq` before upload.

## Bundle semantics

`nvda-current-tree.bundle` is deliberately not a full-history bundle.

The workflow:

1. reads the exact tree SHA of the selected source commit;
2. creates a synthetic commit with that tree and no parent;
3. gives that synthetic commit a temporary local ref;
4. bundles the objects reachable from that synthetic commit;
5. verifies the resulting bundle with `git bundle verify`;
6. deletes the temporary ref from the runner checkout.

The resulting bundle preserves the parent repository's Git tree identity, file blobs, executable/symlink modes, and Gitlink entries without including NVDA's original commit history.

The synthetic commit itself is not the original source commit. Use `metadata.json` to identify the original `sourceSha` and exact `treeSha`.

## Submodules

Neither format recursively embeds external submodule repositories.

For each submodule pointer, `gitlinks.json` records:

```json
{
  "mode": "160000",
  "path": "include/example",
  "sha": "<exact-submodule-commit>",
  "type": "commit"
}
```

The ZIP keeps the parent repository's `.gitmodules` file but does not package submodule working trees. The bundle keeps the Gitlink entries in the parent tree but does not contain the corresponding commits from the external submodule repositories.

For a complete build-capable environment, prefer a normal recursive clone and `git submodule update --init --recursive`. Reconstruct submodules from a snapshot only when there is a specific need to do so.

## Verification

Before relying on a downloaded snapshot, verify `SHA256SUMS` against the artifact contents.

For the ZIP:

```bash
unzip -tq nvda-current-tree.zip
```

For the bundle:

```bash
git bundle verify nvda-current-tree.bundle
git bundle list-heads nvda-current-tree.bundle
```

Then compare the tree represented by the bundle with `metadata.json` if tree identity matters.

## Storage and security properties

* The workflow runs only on manual dispatch.
* It uses a 10-minute Ubuntu job and does not initialize submodules.
* Artifact retention is 3 days.
* Upload compression is disabled because ZIP and Git bundle payloads are already compressed or packed formats.
* No repository write permission is granted; the workflow has `contents: read` only.
* The temporary synthetic Git ref exists only inside the runner checkout.
* Snapshot generation never substitutes for validation. A source snapshot says what tree was captured, not whether that tree builds or runs correctly on Windows.
