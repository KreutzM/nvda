# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NVDA contributors
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

"""Prepare exact Git-data payloads for connector-only publication.

This is developer/agent tooling. It is not imported by the NVDA runtime.

The tool reads committed Git objects instead of working-tree text. This keeps
line endings, encodings, executable modes, symlink targets, blob SHAs and
submodule Gitlinks identical between a validated local commit and GitHub
Git-data publication.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


class PublishPlanError(RuntimeError):
	"""Raised when a safe connector publication plan cannot be produced."""


@dataclass(frozen=True, slots=True)
class ChangedPath:
	"""One changed path reported by Git."""

	status: str
	path: str
	oldPath: str | None = None


def _git(repo: Path, *args: str, text: bool = True) -> str | bytes:
	"""Run Git against ``repo`` and return stdout.

	The repository path is supplied as a separate argument to ``git -C`` and no
	shell is used. This tool is intended for explicit developer-controlled local
	repositories, not untrusted NVDA runtime input.
	"""
	command = ["git", "-C", str(repo), *args]
	result = subprocess.run(command, capture_output=True, check=False)
	if result.returncode != 0:
		stderr = result.stderr.decode("utf-8", errors="replace").strip()
		raise PublishPlanError(f"{' '.join(command)} failed: {stderr}")
	if text:
		return result.stdout.decode("utf-8", errors="strict").strip()
	return result.stdout


def _requireCleanWorktree(repo: Path) -> None:
	status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
	if status:
		raise PublishPlanError(
			"working tree is not clean; commit or remove all changes before preparing connector payloads",
		)


def _parseChangedPaths(raw: bytes) -> tuple[ChangedPath, ...]:
	tokens = raw.split(b"\0")
	if tokens and tokens[-1] == b"":
		tokens.pop()

	changes: list[ChangedPath] = []
	index = 0
	while index < len(tokens):
		status = tokens[index].decode("ascii")
		index += 1
		code = status[0]
		if code in {"R", "C"}:
			if index + 1 >= len(tokens):
				raise PublishPlanError("incomplete rename/copy record from git diff")
			oldPath = tokens[index].decode("utf-8", errors="surrogateescape")
			newPath = tokens[index + 1].decode("utf-8", errors="surrogateescape")
			index += 2
			changes.append(ChangedPath(status=status, path=newPath, oldPath=oldPath))
		else:
			if index >= len(tokens):
				raise PublishPlanError("incomplete path record from git diff")
			path = tokens[index].decode("utf-8", errors="surrogateescape")
			index += 1
			changes.append(ChangedPath(status=status, path=path))
	return tuple(changes)


def _changedPaths(repo: Path, baseRef: str, headRef: str) -> tuple[ChangedPath, ...]:
	raw = _git(
		repo,
		"diff",
		"--name-status",
		"-z",
		"--find-renames",
		baseRef,
		headRef,
		text=False,
	)
	assert isinstance(raw, bytes)
	return _parseChangedPaths(raw)


def _treeEntry(repo: Path, ref: str, path: str) -> tuple[str, str, str]:
	raw = _git(repo, "ls-tree", "-z", ref, "--", path, text=False)
	assert isinstance(raw, bytes)
	if not raw:
		raise PublishPlanError(f"path {path!r} does not exist in {ref}")
	header, storedPath = raw.rstrip(b"\0").split(b"\t", 1)
	if storedPath.decode("utf-8", errors="surrogateescape") != path:
		raise PublishPlanError(f"git returned an unexpected path for {path!r}")
	mode, objectType, sha = header.decode("ascii").split()
	return mode, objectType, sha


def _blobBytes(repo: Path, sha: str) -> bytes:
	raw = _git(repo, "cat-file", "blob", sha, text=False)
	assert isinstance(raw, bytes)
	return raw


def _jsonWrite(path: Path, value: object) -> None:
	path.write_text(
		json.dumps(value, indent=2, ensure_ascii=False) + "\n",
		encoding="utf-8",
		newline="\n",
	)


def _appendBlobChange(
	*,
	repo: Path,
	repositoryFullName: str,
	outputDir: Path,
	change: ChangedPath,
	mode: str,
	sha: str,
	blobUploads: list[dict[str, object]],
	treeElements: list[dict[str, object]],
	changedFiles: list[dict[str, object]],
	writtenBlobShas: set[str],
) -> None:
	content = _blobBytes(repo, sha)
	payloadFile = f"blobs/{sha}.json"
	if sha not in writtenBlobShas:
		payload = {
			"repository_full_name": repositoryFullName,
			"content": base64.b64encode(content).decode("ascii"),
			"encoding": "base64",
		}
		_jsonWrite(outputDir / payloadFile, payload)
		blobUploads.append(
			{
				"sha": sha,
				"size_bytes": len(content),
				"payload_file": payloadFile,
			},
		)
		writtenBlobShas.add(sha)

	treeElements.append({"path": change.path, "mode": mode, "type": "blob", "sha": sha})
	changedFiles.append(
		{
			"status": change.status,
			"path": change.path,
			"old_path": change.oldPath,
			"mode": mode,
			"object_type": "blob",
			"blob_sha": sha,
			"gitlink_sha": None,
			"size_bytes": len(content),
			"payload_file": payloadFile,
		},
	)


def _appendGitlinkChange(
	*,
	change: ChangedPath,
	mode: str,
	sha: str,
	treeElements: list[dict[str, object]],
	changedFiles: list[dict[str, object]],
) -> None:
	if mode != "160000":
		raise PublishPlanError(
			f"Git object type 'commit' for {change.path!r} has unexpected mode {mode!r}",
		)

	treeElements.append({"path": change.path, "mode": mode, "type": "commit", "sha": sha})
	changedFiles.append(
		{
			"status": change.status,
			"path": change.path,
			"old_path": change.oldPath,
			"mode": mode,
			"object_type": "commit",
			"blob_sha": None,
			"gitlink_sha": sha,
			"size_bytes": 0,
			"payload_file": None,
		},
	)


def buildPublishPlan(
	*,
	repo: Path,
	baseRef: str,
	headRef: str,
	repositoryFullName: str,
	remoteBaseCommit: str,
	branchName: str,
	outputDir: Path,
	expectedBaseTree: str | None = None,
) -> dict[str, object]:
	"""Build an exact connector publication plan from committed Git objects."""
	repo = repo.resolve()
	outputDir = outputDir.resolve()
	_requireCleanWorktree(repo)

	_git(repo, "rev-parse", "--verify", f"{baseRef}^{{commit}}")
	_git(repo, "rev-parse", "--verify", f"{headRef}^{{commit}}")
	try:
		_git(repo, "merge-base", "--is-ancestor", baseRef, headRef)
	except PublishPlanError as exc:
		raise PublishPlanError(f"{baseRef} is not an ancestor of {headRef}") from exc

	localBaseCommit = str(_git(repo, "rev-parse", f"{baseRef}^{{commit}}"))
	localBaseTree = str(_git(repo, "rev-parse", f"{baseRef}^{{tree}}"))
	headCommit = str(_git(repo, "rev-parse", f"{headRef}^{{commit}}"))
	expectedTree = str(_git(repo, "rev-parse", f"{headRef}^{{tree}}"))

	if expectedBaseTree is not None and expectedBaseTree != localBaseTree:
		raise PublishPlanError(
			"remote target tree does not match the verified local base tree: "
			f"remote={expectedBaseTree}, local={localBaseTree}",
		)

	changes = _changedPaths(repo, baseRef, headRef)
	if not changes:
		raise PublishPlanError("no committed changes exist between base and head")

	outputDir.mkdir(parents=True, exist_ok=True)
	blobDir = outputDir / "blobs"
	blobDir.mkdir(exist_ok=True)

	blobUploads: list[dict[str, object]] = []
	treeElements: list[dict[str, object]] = []
	changedFiles: list[dict[str, object]] = []
	writtenBlobShas: set[str] = set()

	for change in changes:
		code = change.status[0]
		if change.oldPath is not None and change.oldPath != change.path:
			treeElements.append({"path": change.oldPath, "sha": None})

		if code == "D":
			treeElements.append({"path": change.path, "sha": None})
			changedFiles.append(
				{
					"status": change.status,
					"path": change.path,
					"old_path": change.oldPath,
					"mode": None,
					"object_type": None,
					"blob_sha": None,
					"gitlink_sha": None,
					"size_bytes": 0,
					"payload_file": None,
				},
			)
			continue

		mode, objectType, sha = _treeEntry(repo, headRef, change.path)
		if objectType == "blob":
			_appendBlobChange(
				repo=repo,
				repositoryFullName=repositoryFullName,
				outputDir=outputDir,
				change=change,
				mode=mode,
				sha=sha,
				blobUploads=blobUploads,
				treeElements=treeElements,
				changedFiles=changedFiles,
				writtenBlobShas=writtenBlobShas,
			)
		elif objectType == "commit":
			_appendGitlinkChange(
				change=change,
				mode=mode,
				sha=sha,
				treeElements=treeElements,
				changedFiles=changedFiles,
			)
		else:
			raise PublishPlanError(
				f"unsupported Git object type {objectType!r} for {change.path!r}",
			)

	baseTreeForPublish = expectedBaseTree or localBaseTree
	createTreePayload = {
		"repository_full_name": repositoryFullName,
		"base_tree_sha": baseTreeForPublish,
		"tree_elements": treeElements,
	}
	createCommitTemplate = {
		"repository_full_name": repositoryFullName,
		"message": str(_git(repo, "log", "-1", "--format=%s", headRef)),
		"tree_sha": "<returned-tree-sha>",
		"parent_sha": remoteBaseCommit,
	}
	createBranchTemplate = {
		"repository_full_name": repositoryFullName,
		"branch_name": branchName,
		"sha": "<returned-commit-sha>",
	}
	comparePayload = {
		"repo_full_name": repositoryFullName,
		"base": remoteBaseCommit,
		"head": branchName,
	}

	_jsonWrite(outputDir / "create-tree.json", createTreePayload)
	_jsonWrite(outputDir / "create-commit-template.json", createCommitTemplate)
	_jsonWrite(outputDir / "create-branch-template.json", createBranchTemplate)
	_jsonWrite(outputDir / "compare.json", comparePayload)

	manifest: dict[str, object] = {
		"format_version": 2,
		"repository_full_name": repositoryFullName,
		"branch_name": branchName,
		"remote_base_commit": remoteBaseCommit,
		"local_base_ref": baseRef,
		"local_base_commit": localBaseCommit,
		"local_base_tree": localBaseTree,
		"head_ref": headRef,
		"head_commit": headCommit,
		"expected_tree": expectedTree,
		"changed_files": changedFiles,
		"blob_uploads": blobUploads,
		"create_tree_payload": "create-tree.json",
		"create_commit_template": "create-commit-template.json",
		"create_branch_template": "create-branch-template.json",
		"compare_payload": "compare.json",
	}
	_jsonWrite(outputDir / "manifest.json", manifest)

	gitlinkCount = sum(1 for entry in changedFiles if entry["object_type"] == "commit")
	instructions = f"""Connector publish plan
======================

Repository: {repositoryFullName}
Remote parent: {remoteBaseCommit}
Local base tree: {localBaseTree}
Expected final tree: {expectedTree}
Feature branch: {branchName}
Changed paths: {len(changedFiles)}
Unique blobs: {len(blobUploads)}
Gitlinks: {gitlinkCount}

Required sequence
-----------------
1. Create each blob using blobs/*.json. Every returned SHA must equal the SHA in manifest.json.
2. Create the tree using create-tree.json. Gitlink entries use mode 160000, type commit and the exact submodule commit SHA. The returned tree SHA must equal {expectedTree}.
3. Create the commit using create-commit-template.json after replacing <returned-tree-sha>.
4. Create the branch using create-branch-template.json after replacing <returned-commit-sha>.
5. Compare using compare.json and require behind_by == 0 plus only the expected paths.
6. Open a draft pull request.

Stop immediately on the first SHA mismatch. Do not retry by copying or re-encoding file text or by converting Gitlinks into blobs.
"""
	(outputDir / "README.txt").write_text(instructions, encoding="utf-8", newline="\n")
	return manifest


def _parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Prepare exact GitHub Git-data connector payloads from a committed diff.",
	)
	parser.add_argument("--repo", type=Path, default=Path.cwd())
	parser.add_argument("--base-ref", required=True)
	parser.add_argument("--head-ref", default="HEAD")
	parser.add_argument("--repository", required=True, dest="repositoryFullName")
	parser.add_argument("--remote-base-commit", required=True, dest="remoteBaseCommit")
	parser.add_argument("--branch", required=True, dest="branchName")
	parser.add_argument("--expected-base-tree", dest="expectedBaseTree")
	parser.add_argument("--output-dir", type=Path, default=Path(".agent-publish"), dest="outputDir")
	return parser


def main(argv: Iterable[str] | None = None) -> int:
	"""Run the command-line publisher-plan generator."""
	args = _parser().parse_args(argv)
	try:
		manifest = buildPublishPlan(
			repo=args.repo,
			baseRef=args.base_ref,
			headRef=args.head_ref,
			repositoryFullName=args.repositoryFullName,
			remoteBaseCommit=args.remoteBaseCommit,
			branchName=args.branchName,
			outputDir=args.outputDir,
			expectedBaseTree=args.expectedBaseTree,
		)
	except PublishPlanError as exc:
		print(f"error: {exc}", file=sys.stderr)
		return 2

	print(f"Prepared {len(manifest['changed_files'])} changed paths in {args.outputDir}")
	print(f"Expected final tree: {manifest['expected_tree']}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
