# Agent validation levels

This document defines how agents must describe validation for changes in `KreutzM/nvda`. It exists to prevent inspection, static analysis, CI, and real Windows execution from being conflated.

The repository's authoritative test commands remain in `projectDocs/testing/automated.md` and related project documentation. This file defines reporting semantics and minimum evidence, not a replacement test framework.

## Core rule

Report only checks that actually ran, in the environment where they actually ran.

Do not turn a plausible code review into a test result. Do not turn GitHub Actions into local validation. Do not turn a passing unit test into evidence that NVDA was manually exercised in Windows.

## Validation levels

### V0: repository inspection

V0 means the change was inspected without executing repository validation.

Examples:

* files and call sites were read;
* repository structure was inspected;
* a branch diff was reviewed;
* referenced paths were verified;
* implementation behavior was reasoned about from code and tests;
* connector state and blob SHAs were checked.

Allowed claim:

```text
Validation: V0 inspection only. The changed files and branch diff were reviewed through the GitHub connector. No code was executed.
```

V0 does not establish that code imports, builds, passes lint, passes tests, or works at runtime.

### V1: static or platform-independent checks

V1 means relevant checks executed, but without establishing an NVDA Windows runtime result.

Examples can include, when actually available and appropriate:

* Markdown linting;
* YAML/TOML/XML syntax validation;
* actionlint;
* Ruff formatting/linting where the required environment is available;
* repository-specific scripts that do not require an NVDA runtime;
* connector-side structural verification such as exact branch comparisons.

A V1 report must list the exact checks that ran and their result.

Example:

```text
Validation: V1.
* markdownlint: passed
* branch compare against target: behind_by=0; expected paths only

Not run: Windows source build, NVDA unit tests, runtime validation.
```

A V1 check performed on Linux or through a remote service must not be described as Windows validation.

### V2: local Windows developer validation

V2 means validation was executed in a suitable Windows development environment using the repository's supported toolchain.

Depending on the change, this can include:

```cmd
scons source
runlint.bat
runcheckpot.bat
rununittests.bat
runlicensecheck.bat
```

and targeted or system tests documented elsewhere in the repository.

Do not run every command mechanically for every change. Select checks according to change impact and report exactly what ran.

Examples of truthful V2 claims:

```text
Validation: V2 Windows developer environment.
* scons source: passed
* rununittests.bat -k test_magnifier: passed
* runcheckpot.bat: passed
```

If NVDA itself was started and manually exercised, report that separately from automated checks.

### V3: GitHub Actions validation

V3 means one or more GitHub Actions checks ran for the exact commit being reviewed.

A V3 report must identify the relevant workflow or checks and their conclusions. It must not imply that the agent ran those checks locally.

Example:

```text
Validation: V3 CI.
* CI/CD: passed for commit <sha>
* Autofix or fail: passed for commit <sha>

No local Windows runtime validation was performed.
```

If some jobs are skipped, cancelled, neutral, or absent, do not summarize the whole pipeline as fully passed without qualification.

## Manual runtime and hardware evidence

Some behavior cannot be established from unit tests or generic CI.

Examples include:

* visual magnifier quality and interaction;
* real multi-monitor behavior;
* physical braille displays;
* synthesizer-specific behavior;
* application-specific accessibility integration;
* timing-sensitive or focus-sensitive user interaction;
* elevated or secure-screen behavior.

Report manual evidence independently from V0-V3.

Example:

```text
Manual Windows validation:
* NVDA started from the prepared source tree.
* Fullscreen magnifier was toggled and zoom changed on a two-monitor system.
* Focus tracking was exercised in Notepad.

Not tested: docked mode, secure desktop, touch input.
```

Do not claim physical hardware validation from mocks, simulators, or unit-test doubles.

## Change-to-check guidance

Use the narrowest useful checks during development, then broaden validation when the affected boundary warrants it.

### Documentation-only changes

Typically consider:

* Markdown linting;
* link/path verification;
* relevant documentation generation if the changed document participates in generated output;
* GitHub Actions checks triggered by the pull request.

A full NVDA runtime test is normally unnecessary unless the documentation change accompanies product behavior that also changed.

### Python source changes

Typically consider:

* applicable `prek` hooks;
* Ruff/linting;
* Pyright and ty where relevant;
* targeted unit tests;
* `runcheckpot.bat` when translatable strings changed;
* broader unit or system tests for cross-cutting behavior.

Follow `.github/instructions/python.instructions.md` and current project documentation.

### Native C/C++ changes

Typically consider:

* applicable lint/static checks;
* `scons source` or the appropriate native build target;
* unit/system tests that exercise the native boundary;
* security review for IPC, injected code, UIAccess, bounds, lifetime, and untrusted data.

Follow `.github/instructions/cpp.instructions.md`.

### User-interface changes

Typically consider:

* targeted unit tests where available;
* translation-string checks;
* user-guide or context-help impact;
* manual Windows interaction when layout, focus, keyboard operation, or visual behavior changed.

### Magnifier changes

At minimum, inspect and usually run the relevant tests under `tests/unit/test_magnifier/` when a Windows test environment is available.

Broaden to source build, GUI/config tests, manual Windows magnifier checks, multi-monitor checks, or system tests when the change crosses those boundaries.

### Dependency changes

Typically consider:

* lock/dependency consistency;
* `runlicensecheck.bat` for Python dependency changes;
* source build and targeted runtime tests;
* submodule status and intended Gitlink commit for submodule updates.

### CI or workflow changes

Typically consider:

* YAML validation;
* actionlint;
* a real GitHub Actions run on the exact changed commit;
* artifact creation and retention review.

Do not add large uploaded artifacts merely to make a CI test easier to inspect. Prefer logs and job summaries where possible.

## Connector-specific evidence

For connector-authored changes, record repository-state evidence before a pull request:

* feature branch and intended base;
* exact base commit when the branch was created;
* `behind_by` from the final compare;
* exact changed paths;
* current blob SHAs used for replaced or deleted files where relevant;
* whether any Gitlinks or non-text objects changed.

This evidence establishes publication integrity, not runtime correctness.

## Stacked pull requests

When a change is stacked on an unmerged agent branch, validate both of these views:

1. The stacked PR diff against its immediate base contains only the new roadmap layer.
2. The complete branch relative to `master` contains the dependency plus the new layer and no unrelated changes.

After the dependency is merged, retarget or rebase as needed and repeat the branch comparison before merge.

## CI result interpretation

Do not treat a workflow name alone as proof that every intended check ran.

When inspecting CI:

1. Confirm the workflow run is for the exact head commit.
2. Inspect overall status and conclusion.
3. Inspect jobs when a run fails, is partial, or contains skips that matter to the change.
4. Inspect logs only as needed to identify actionable failures.
5. Check uploaded artifacts only when the validation task genuinely requires them.

Avoid downloading large build artifacts merely to confirm that CI produced them.

## Reporting template

Use a compact report like this in pull requests and task summaries:

```text
Validation
* V0: complete branch diff inspected; expected paths only.
* V1: markdownlint passed.
* V2: not run; no local Windows environment used.
* V3: CI/CD passed for <sha>; Autofix or fail passed for <sha>.
* Manual runtime: not performed.

Remaining validation
* None for this documentation-only change.
```

Omit irrelevant levels if a shorter report is clearer, but never hide a missing validation level by implying it happened.

## Failure handling

When a check fails:

* record the failing check accurately;
* distinguish a repository defect from an environment or infrastructure failure;
* make the smallest justified fix;
* rerun the failed or affected check rather than automatically repeating an expensive full pipeline;
* do not rerun successful large jobs solely to obtain a cleaner-looking report when the repository allows a narrower retry.

For GitHub Actions, prefer retrying failed jobs or the smallest relevant workflow scope where repository permissions and tooling allow it.

## Artifact discipline

Validation should not create long-lived storage as a side effect unless that storage is part of the product or explicitly required evidence.

For agent-specific validation:

* prefer no uploaded artifact;
* never upload full repository snapshots or Git bundles by default;
* never duplicate NVDA installers or other existing CI products for agent convenience;
* if a small artifact is unavoidable, use minimal contents and the shortest practical retention;
* document why the artifact is needed and remove the upload in a later simplification if logs or summaries become sufficient.
