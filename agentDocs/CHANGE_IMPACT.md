# Agent change impact guide

This guide maps common NVDA change areas to likely tests, documentation, compatibility, security, runtime, and publication concerns. It is a routing aid, not a substitute for reading the implementation, nearby tests, scoped `.github/instructions/`, and authoritative project documentation.

## General workflow

For every nontrivial change:

1. Identify the narrowest subsystem in `REPOSITORY_MAP.md`.
2. Read the applicable `.github/instructions/` file.
3. Search nearby unit and system tests before creating new test locations.
4. Use this guide to identify likely secondary impact.
5. Select validation evidence using `VALIDATION.md`.
6. Verify the final branch diff using `GIT_WORKFLOW.md`.

## Python runtime source

Typical paths:

```text
source/**/*.py
source/**/*.pyw
```

Inspect nearby tests and direct callers, public or add-on-visible symbols, translation strings, configuration behavior, and secure-mode implications where applicable.

Likely validation includes applicable `prek` hooks, Ruff/linting, type checks where relevant, targeted unit tests, `runcheckpot.bat` for translatable strings, and broader tests for cross-cutting changes.

## Native C/C++ and injected code

Typical paths:

```text
nvdaHelper/
source/NVDAHelper/
**/*.cpp
**/*.h
```

Inspect `.github/instructions/cpp.instructions.md`, SCons build definitions, IPC and serialization boundaries, buffer lengths, ownership, lifetime, COM usage, UIAccess, secure-desktop behavior, injected-process implications, and untrusted input.

Likely validation includes relevant static checks, `scons source` or a narrower native build, targeted unit/system tests, and real Windows execution when behavior depends on process injection or OS APIs.

Do not infer native runtime safety from Python unit tests alone.

## Accessibility API handlers

Typical paths:

```text
source/UIAHandler/
source/IAccessibleHandler/
source/JABHandler.py
source/NVDAObjects/
```

Inspect event volume, COM/UIA call cost, threading, object lifetime, caching, text ranges, application/browser compatibility, and fallback behavior between accessibility APIs.

Changes to shared object construction, event dispatch, or text navigation have broad regression potential and usually warrant broader tests.

## Text navigation and browse mode

Typical paths:

```text
source/textInfos/
source/browseMode.py
virtual-buffer related code
```

Inspect caret and selection semantics, range boundaries, movement units, formatting retrieval, browse/focus mode switching, and browser/document compatibility.

Likely validation includes targeted text-info, cursor, browse-mode, and system tests.

## Speech

Typical paths:

```text
source/speech/
source/synthDrivers/
source/synthDriverHandler.py
```

Inspect sequence ordering, cancellation, spelling, say-all, priorities, synthesizer capabilities, and audio-device interactions.

Use speech and speech-manager tests plus driver-specific validation where appropriate. Do not generalize one synthesizer's result to all synthesizers.

## Braille

Typical paths:

```text
source/braille/
source/brailleDisplayDrivers/
source/brailleTables.py
```

Inspect display routing, input gestures, tethering, cursor behavior, translation tables, protocol handling, timing, and device capabilities.

Hardware-dependent behavior requires physical-device evidence for strong compatibility claims.

## GUI and settings

Typical paths:

```text
source/gui/
source/config/
```

Inspect keyboard navigation, focus order, labels and accessible names, DPI/layout behavior, configuration defaults, profile migration, context help, user-guide anchors, and translatable strings.

Likely validation includes targeted GUI/config tests, translation checks, user documentation, and manual Windows interaction when layout or focus behavior changes.

## Magnifier

Typical paths:

```text
source/_magnifier/
tests/unit/test_magnifier/
Windows Magnification API bindings used by the implementation
relevant GUI/configuration code
```

Inspect zoom transforms, coordinate conversion, focus/review/navigator/mouse tracking, tracking modes, color effects, overview behavior, mouse transforms, multi-monitor coordinates, virtual-screen bounds, API initialization and teardown, settings, commands, and boundaries between fullscreen, docked, lens, or other modes.

Likely validation includes targeted `tests/unit/test_magnifier/` tests, command/config tests, source build when Windows/native boundaries change, manual Windows visual validation, and multi-monitor testing for coordinate changes.

Visual quality, latency, clipping, and real multi-monitor behavior require runtime evidence; unit tests alone cannot establish them.

## Vision enhancement providers

Typical paths:

```text
source/visionEnhancementProviders/
tests/unit/test_visionEnhancementProviders/
```

Inspect the lifecycle and integration boundary before sharing code with the built-in magnifier. Similar low-vision goals do not imply identical rendering or configuration architecture.

## Input and gestures

Typical paths:

```text
source/inputCore.py
source/keyboardHandler.py
source/mouseHandler.py
source/touchHandler.py
source/globalCommands.py
```

Inspect gesture conflicts, precedence, keyboard layouts, NVDA modifier variants, latency, event ordering, secure-screen restrictions, and command documentation.

## App modules and application-specific support

Typical paths:

```text
source/appModules/
```

Inspect executable mapping, supported application versions, API fallback behavior, nearby app-module tests, and whether the behavior belongs in a generic object instead.

Manual testing in the target application is often needed for strong compatibility claims.

## Add-ons and public compatibility

Typical paths:

```text
source/addonHandler/
source/addonAPIVersion.py
public modules imported by add-ons
```

Inspect backward compatibility of imports, classes, methods, configuration, metadata, migration behavior, and API version implications. Avoid accidental public API breaks during internal refactors.

## Configuration schema and migration

Typical paths:

```text
source/config/
source/config/configSpec.py
source/config/profileUpgradeSteps.py
```

Inspect defaults, existing profile behavior, upgrade steps, invalid-value handling, GUI synchronization, and serialization compatibility.

## Localization and user-facing strings

When adding or changing translatable strings, follow repository translation conventions, add translator comments where required, run `runcheckpot.bat` in a suitable environment, and update user documentation when semantics or commands change.

Do not mechanically edit translated language files unless the task explicitly concerns localization workflow.

## User guide

Typical path:

```text
user_docs/en/userGuide.md
```

Read `.github/instructions/userGuide.instructions.md` before editing. Check command formatting, setting structure, anchors, context-help references, and generated key-command content where relevant.

## Python dependencies

For `pyproject.toml` or lock/dependency changes, inspect version compatibility, Windows availability, runtime/build distinction, license compatibility, security implications, and lock-file consistency.

Likely validation includes `runlicensecheck.bat`, source build, and targeted tests using the dependency.

## Submodule updates

Inspect the intended submodule repository and exact commit, recursive-checkout expectations, build/runtime compatibility, and parent-repository Gitlink diff.

Likely validation includes `git submodule status --recursive`, recursive update from a clean checkout, relevant build/tests, and verification that only intended Gitlinks changed.

Connector publication must use a Gitlink-capable path; ordinary text-file operations are not valid for changing a submodule pointer.

## Build-system changes

Typical paths:

```text
sconstruct
*sconscript
runtime-builders/
```

Inspect architecture-specific output, generated files, native dependencies, clean versus incremental builds, packaging, and install layout.

Likely validation includes an appropriate SCons build, exact-commit CI, and launcher/installer validation when packaging changes.

## GitHub Actions and CI

Typical paths:

```text
.github/workflows/
ci/
```

Inspect trigger scope, duplicate runs, permissions, concurrency/cancellation, runner assumptions, cache usage, artifact size, artifact duplication, artifact retention, and fork-safe behavior when secrets are unavailable.

Useful artifacts are allowed when they materially improve reproducibility, debugging, validation, publication, or agent access. For snapshots, Git bundles, installers, symbols, diagnostics, or context packs, explicitly consider expected size and generation frequency and set the shortest practical retention. Temporary agent-oriented artifacts should normally expire after days, not remain for weeks or months without a stated reason.

Likely validation includes YAML validation, actionlint, a real workflow run on the exact commit, and job/log inspection. Artifact download is only necessary when its contents are part of the validation question.

## Agent infrastructure

Typical paths:

```text
AGENTS.md
agentDocs/
agentTools/
tests/unit/test_agentTools/
agent-specific workflows
```

Keep this layer separate from NVDA product logic where practical. Agent-infrastructure changes should favor deterministic repository state, truthful validation reporting, and low operational overhead.

If agent tooling creates snapshots or publication bundles, ensure they are reproducible, checksummed where appropriate, scoped to a real consumer need, and retained only as long as needed.

## Documentation impact

For user-visible behavior, consider `user_docs/en/changes.md` and the relevant user-guide section. For developer-facing architecture or workflow changes, prefer updating the existing authoritative `projectDocs/` page rather than duplicating it into `agentDocs/`.

Agent documentation should primarily explain navigation, workflow, evidence, and repeated discovery shortcuts.

## Security-sensitive changes

Increase review depth when a change affects any of these areas:

* UIAccess or elevated accessibility privileges;
* secure desktop or lock screen;
* injected code;
* IPC or cross-process data;
* untrusted application/browser content;
* downloaded add-ons or update mechanisms;
* credentials, tokens, paths, or user data exposed through logs;
* binary parsing, bounds, memory lifetime, or native pointer handling.

Read the applicable Python or C++ security instructions and distinguish code review from actual runtime/security validation.

## Performance-sensitive changes

Increase scrutiny when a path runs per input event, accessibility event, object creation, text query, speech chunk, braille update, or magnifier frame/tracking update.

Look for added COM calls, repeated tree walks, allocations, logging, synchronization, polling, or per-frame work. Prefer targeted measurements when performance is part of the task rather than claiming improvement from code inspection alone.

## Final pre-PR questions

Before publication, answer these questions from evidence:

1. What subsystem owns this behavior?
2. Which adjacent tests or runtime boundaries can regress?
3. Did user-facing behavior, commands, settings, or documentation change?
4. Did public/add-on compatibility change?
5. Did configuration or migration behavior change?
6. Did a submodule, dependency, native boundary, or security-sensitive path change?
7. Which V0-V3 validation levels actually ran?
8. Is any manual Windows, application, hardware, or multi-monitor validation still missing?
9. Are any Actions artifacts useful, and if so are size and retention proportional to their purpose?
10. Does the complete branch diff contain only the intended change?
