# Repository map for agents

This document is a compact navigation layer for `KreutzM/nvda`. It is not a replacement for NVDA's design documentation. Use it to identify the likely subsystem, nearby tests, and the authoritative documentation to read before making changes.

## Repository-level entry points

### `AGENTS.md`

Fork-wide workflow, repository identity, validation claims, connector behavior, branch rules, and submodule handling.

### `.github/instructions/`

Scoped technical instructions that should be read when applicable:

- `python.instructions.md` for Python and Python-window files.
- `cpp.instructions.md` for native C/C++ code.
- `userGuide.instructions.md` for the English user guide.
- `review.instructions.md` for code-review expectations.

### `projectDocs/`

Authoritative developer and testing documentation. Important starting points include:

- `projectDocs/dev/createDevEnvironment.md` for the Windows development environment and submodules.
- `projectDocs/dev/buildingNVDA.md` for source preparation, running from source, and builds.
- `projectDocs/dev/designOverview.md` for the architectural model.
- `projectDocs/testing/automated.md` for lint, unit, system, translation, and license checks.

### `.github/workflows/` and `ci/`

Existing CI/CD implementation. Prefer extending or reusing this infrastructure over creating a parallel product build pipeline.

The main product workflow is `.github/workflows/testAndPublish.yml`. It performs a recursive checkout, prepares and builds NVDA on Windows, and drives the repository's established validation pipeline.

## Main application source

### `source/`

The primary NVDA runtime source tree. NVDA is mostly Python, with native components and Windows API boundaries where required.

Before broad changes here, read `projectDocs/dev/designOverview.md` and the applicable `.github/instructions/` file.

### `source/core.py`

Central application lifecycle and main-loop behavior. Changes here can have wide timing, shutdown, initialization, and event-processing impact.

### `source/NVDAObjects/`

NVDA's abstraction of accessible UI objects. Changes can affect object behavior across applications and accessibility APIs.

Likely related areas include `source/IAccessibleHandler/`, `source/UIAHandler/`, application modules, and unit/system tests for the affected object behavior.

### `source/IAccessibleHandler/`

MSAA/IAccessible and IAccessible2 handling. Treat browser, application, event, and text changes here as compatibility-sensitive.

### `source/UIAHandler/`

Microsoft UI Automation handling. Changes may affect many Windows applications and should be checked for event volume, COM/UIA call cost, threading, and compatibility.

Nearby tests include files and directories under `tests/unit/` whose names contain `UIA` and relevant system tests.

### `source/JABHandler.py`

Java Access Bridge integration.

### `source/textInfos/`

Text-range abstraction used for caret movement, selection, formatting, and document navigation across different accessibility backends.

### `source/browseMode.py` and related virtual-buffer code

Browse-mode navigation and document interaction. Changes can affect web and document navigation broadly.

### `source/globalCommands.py`

Global NVDA commands and scripts that can be invoked throughout the application. Command changes often require tests, gesture consideration, and user documentation.

### `source/inputCore.py`, `source/keyboardHandler.py`, `source/mouseHandler.py`, and `source/touchHandler.py`

Input gesture and device handling. Treat changes as latency- and regression-sensitive.

### `source/speech/`

Speech generation and sequencing. Nearby tests include `tests/unit/test_speech.py`, `tests/unit/test_speechManager/`, speech dictionary tests, and synthesizer tests.

### `source/braille/` and `source/brailleDisplayDrivers/`

Braille output, input, and display-driver support. Nearby tests include `tests/unit/test_braille/`, `tests/unit/brailleDisplayDrivers/`, and related table/driver tests.

### `source/gui/`

NVDA's wxPython-based user interface, dialogs, settings, configuration UI, and related helpers.

GUI changes may also require user-guide updates, context-sensitive help, translation checks, and manual Windows validation.

### `source/appModules/`

Application-specific behavior. Start by identifying the target executable/application and nearby app-module tests.

### `source/globalPlugins/`

Built-in global plugin functionality.

### `source/synthDrivers/`

Speech synthesizer drivers. Check driver-specific and synth-driver-handler tests.

### `source/brailleDisplayDrivers/`

Hardware-specific braille display drivers. Hardware behavior may require validation that cannot be established in generic CI.

## Magnifier and low-vision areas

### `source/_magnifier/`

Built-in magnifier implementation. This is the first planned domain for deeper agent documentation.

Relevant implementation concerns include tracking, focus management, mouse handling, zoom transforms, color effects, Windows Magnification API state, cleanup, and future magnifier modes.

Start with the files in this package and then inspect the Windows API bindings used by the implementation.

### `tests/unit/test_magnifier/`

Dedicated magnifier unit tests. The current test area includes coverage for:

- focus management;
- fullscreen magnification;
- base magnifier behavior;
- magnifier commands;
- mouse hooks;
- spotlight management.

For magnifier changes, prefer targeted tests here during development and broader NVDA validation before merge when the change crosses subsystem boundaries.

### `source/visionEnhancementProviders/`

Other vision-enhancement infrastructure. Do not assume it is interchangeable with the built-in magnifier; inspect the integration boundary before refactoring across them.

### `tests/unit/test_visionEnhancementProviders/`

Unit coverage for vision-enhancement providers.

## Native and Windows boundaries

### `source/NVDAHelper/`

Native helper and integration code associated with injected/in-process behavior. Native changes are security- and stability-sensitive.

### `source/winBindings/`

Python ctypes definitions and wrappers for Windows APIs. Keep raw Windows API definitions here when the repository conventions require it.

### `nvdaHelper/` or native build inputs referenced by SCons

When a task reaches native/injected code, read the C++ instructions and build documentation before editing. NVDA operates with elevated accessibility privileges in some contexts and processes untrusted external data, so IPC, bounds, privilege, and data-leak checks matter.

## Configuration, add-ons, and compatibility

### `source/config/` and configuration-related modules

Runtime and user configuration. Changes may require profile migration, default-value compatibility, GUI settings updates, and tests.

### `source/addonHandler/` and add-on-related modules

Add-on loading, compatibility, metadata, and lifecycle behavior. Preserve API compatibility deliberately rather than accidentally changing public/imported symbols.

### `source/addonAPIVersion.py`

NVDA add-on API compatibility version information. Changes here can have ecosystem-wide implications.

## Documentation and localization

### `user_docs/en/userGuide.md`

Primary English user guide. Read `.github/instructions/userGuide.instructions.md` before editing it.

### `user_docs/en/changes.md`

User-facing change history used by the existing NVDA documentation pipeline.

### Localization files and `source/l10nUtil.py`

Translation-related changes have specialized checks. Use `runcheckpot.bat` and the documented localization tooling where applicable.

## Tests

### `tests/unit/`

Primary Python unit-test suite. Search this tree for the subsystem name before creating a new test location.

### `tests/system/`

Robot Framework system tests. Use these for behavior requiring a running NVDA/application environment when unit tests are insufficient.

### `tests/manual/`

Manual test material where automated coverage cannot fully express the behavior.

### `tests/checkPot.py`

Translation-string validation support.

The authoritative commands and current test mechanics are documented in `projectDocs/testing/automated.md`.

## Build and dependency infrastructure

### `pyproject.toml`

Python package metadata, pinned runtime/build dependencies, Ruff configuration, Pyright configuration, and other Python tooling settings.

Do not introduce dependency changes without checking license compatibility and the repository's lock/dependency workflow.

### `.pre-commit-config.yaml`

Configuration used by `prek`/pre-commit-compatible hooks. It includes formatting, linting, repository hygiene, translation checks, unit tests, license checks, and type checks depending on file type and execution environment.

### `sconstruct` and `*sconscript`

SCons build definitions. Build changes can affect native binaries, generated source, packaging, and runtime layout.

### `.gitmodules`

Submodule definitions. This repository relies on multiple versioned external repositories. Parent-repository changes to submodules appear as Gitlinks with mode `160000`.

### `include/` and `miscDeps`

Third-party and build/runtime dependency material, much of it supplied by submodules. Do not treat these trees as ordinary first-party source without checking ownership and submodule boundaries.

## CI/CD

### `.github/workflows/testAndPublish.yml`

Main Windows CI/CD pipeline. It recursively checks out submodules and runs the established build/test process.

Do not reproduce this workflow in a separate agent-specific product CI unless there is a demonstrated gap. Agent-infrastructure CI should validate only agent-specific files and tooling where possible.

### `ci/`

Scripts and documentation supporting the CI/CD pipeline. Read `ci/README.md` before changing CI behavior, signing, publishing, release deployment, or fork-specific workflow configuration.

## How to use this map

For a new task:

1. Identify the narrowest subsystem above.
2. Read its implementation entry points instead of scanning the entire repository.
3. Search `tests/unit/` and `tests/system/` for the subsystem or symbols being changed.
4. Read the applicable `.github/instructions/` file.
5. Read the specific `projectDocs/` page for build, architecture, or testing questions.
6. Expand outward only when imports, call sites, tests, or runtime behavior demonstrate that another subsystem is involved.

If repeated work in one subsystem still requires substantial rediscovery, add a focused guide under `agentDocs/domains/` rather than growing this repository map indefinitely.
