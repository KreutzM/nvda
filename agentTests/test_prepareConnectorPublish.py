# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NVDA contributors
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).parents[1] / "agentTools" / "prepareConnectorPublish.py"
_SPEC = importlib.util.spec_from_file_location("prepareConnectorPublish", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)


def _git(repo: Path, *args: str, inputBytes: bytes | None = None) -> bytes:
	result = subprocess.run(
		["git", "-C", str(repo), *args],
		input=inputBytes,
		capture_output=True,
		check=True,
	)
	return result.stdout


def _initRepo(repo: Path) -> None:
	repo.mkdir()
	_git(repo, "init", "-q")
	_git(repo, "config", "user.name", "Test Agent")
	_git(repo, "config", "user.email", "test@example.invalid")


def _makeBlobRepo(tmpPath: Path) -> tuple[Path, str, str]:
	repo = tmpPath / "repo"
	_initRepo(repo)

	(repo / "keep.txt").write_text("base\n", encoding="utf-8")
	(repo / "delete.txt").write_text("remove me\n", encoding="utf-8")
	_git(repo, "add", ".")
	_git(repo, "commit", "-q", "-m", "base")
	base = _git(repo, "rev-parse", "HEAD").decode().strip()

	(repo / "keep.txt").write_text("line one\r\nline two\r\n", encoding="utf-8", newline="")
	(repo / "binary.dat").write_bytes(b"\x00\xa1\xff\r\n")
	(repo / "delete.txt").unlink()
	_git(repo, "add", "-A")
	_git(repo, "commit", "-q", "-m", "head")
	head = _git(repo, "rev-parse", "HEAD").decode().strip()
	return repo, base, head


def _buildPlan(repo: Path, base: str, head: str, output: Path) -> dict[str, object]:
	baseTree = _git(repo, "rev-parse", f"{base}^{{tree}}").decode().strip()
	return _MODULE.buildPublishPlan(
		repo=repo,
		baseRef=base,
		headRef=head,
		repositoryFullName="owner/repo",
		remoteBaseCommit="a" * 40,
		branchName="agent/test",
		outputDir=output,
		expectedBaseTree=baseTree,
	)


def testPlanUsesExactCommittedBlobBytes(tmp_path: Path) -> None:
	repo, base, head = _makeBlobRepo(tmp_path)
	output = tmp_path / "plan"

	manifest = _buildPlan(repo, base, head, output)

	assert manifest["expected_tree"] == _git(repo, "rev-parse", f"{head}^{{tree}}").decode().strip()
	changed = {entry["path"]: entry for entry in manifest["changed_files"]}
	assert set(changed) == {"binary.dat", "delete.txt", "keep.txt"}
	assert changed["delete.txt"]["blob_sha"] is None

	for path in ("binary.dat", "keep.txt"):
		entry = changed[path]
		payload = json.loads((output / entry["payload_file"]).read_text(encoding="utf-8"))
		decoded = base64.b64decode(payload["content"])
		committed = _git(repo, "cat-file", "blob", entry["blob_sha"])
		assert decoded == committed

	treePayload = json.loads((output / "create-tree.json").read_text(encoding="utf-8"))
	baseTree = _git(repo, "rev-parse", f"{base}^{{tree}}").decode().strip()
	assert treePayload["base_tree_sha"] == baseTree
	assert any(item == {"path": "delete.txt", "sha": None} for item in treePayload["tree_elements"])


def testPlanPreservesSubmoduleGitlink(tmp_path: Path) -> None:
	child = tmp_path / "child"
	_initRepo(child)
	(child / "dependency.txt").write_text("base\n", encoding="utf-8")
	_git(child, "add", ".")
	_git(child, "commit", "-q", "-m", "child base")

	repo = tmp_path / "parent"
	_initRepo(repo)
	_git(
		repo,
		"-c",
		"protocol.file.allow=always",
		"submodule",
		"add",
		"-q",
		str(child),
		"dependency",
	)
	_git(repo, "commit", "-q", "-am", "parent base")
	base = _git(repo, "rev-parse", "HEAD").decode().strip()

	submodule = repo / "dependency"
	_git(submodule, "config", "user.name", "Test Agent")
	_git(submodule, "config", "user.email", "test@example.invalid")
	(submodule / "dependency.txt").write_text("updated\n", encoding="utf-8")
	_git(submodule, "add", "dependency.txt")
	_git(submodule, "commit", "-q", "-m", "child update")
	gitlinkSha = _git(submodule, "rev-parse", "HEAD").decode().strip()

	_git(repo, "add", "dependency")
	_git(repo, "commit", "-q", "-m", "update dependency")
	head = _git(repo, "rev-parse", "HEAD").decode().strip()

	output = tmp_path / "plan"
	manifest = _buildPlan(repo, base, head, output)
	changed = {entry["path"]: entry for entry in manifest["changed_files"]}
	assert set(changed) == {"dependency"}
	assert changed["dependency"]["mode"] == "160000"
	assert changed["dependency"]["object_type"] == "commit"
	assert changed["dependency"]["gitlink_sha"] == gitlinkSha
	assert changed["dependency"]["blob_sha"] is None
	assert changed["dependency"]["payload_file"] is None
	assert manifest["blob_uploads"] == []

	treePayload = json.loads((output / "create-tree.json").read_text(encoding="utf-8"))
	assert treePayload["tree_elements"] == [
		{
			"path": "dependency",
			"mode": "160000",
			"type": "commit",
			"sha": gitlinkSha,
		},
	]


def testPlanRejectsDirtyWorktree(tmp_path: Path) -> None:
	repo, base, head = _makeBlobRepo(tmp_path)
	(repo / "uncommitted.txt").write_text("dirty", encoding="utf-8")

	with unittest.TestCase().assertRaisesRegex(_MODULE.PublishPlanError, "not clean"):
		_buildPlan(repo, base, head, tmp_path / "plan")


def testPlanRejectsRemoteTreeMismatch(tmp_path: Path) -> None:
	repo, base, head = _makeBlobRepo(tmp_path)

	with unittest.TestCase().assertRaisesRegex(_MODULE.PublishPlanError, "does not match"):
		_MODULE.buildPublishPlan(
			repo=repo,
			baseRef=base,
			headRef=head,
			repositoryFullName="owner/repo",
			remoteBaseCommit="a" * 40,
			branchName="agent/test",
			outputDir=tmp_path / "plan",
			expectedBaseTree="b" * 40,
		)
