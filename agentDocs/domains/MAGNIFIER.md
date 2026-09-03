# Magnifier domain guide

This guide is the first subsystem-specific agent context document for `KreutzM/nvda`. Use it to reduce rediscovery when working on NVDA's built-in magnifier. It describes current architectural boundaries, likely change impact, and validation expectations; source code and tests remain authoritative.

Read the repository-root `AGENTS.md`, `agentDocs/VALIDATION.md`, and `.github/instructions/python.instructions.md` before implementing changes.

## Current implementation status

The built-in magnifier has a shared base architecture for multiple view types, but the rendering implementations are not equally complete.

Current state:

* `FullScreenMagnifier` is the implemented magnifier view and calls the Windows Magnification API.
* `DockedMagnifier` currently defines the class/lifecycle shape but `_doUpdate` is empty.
* `LensMagnifier` currently defines the class/lifecycle shape but `_doUpdate` is empty.
* `FixedMagnifier` currently defines the class/lifecycle shape but `_doUpdate` is empty.

Do not assume docked, lens, or fixed rendering already exists merely because the enum values, factory branches, configuration, commands, and class skeletons exist.

When implementing one of these modes, first decide which behavior belongs in the shared `Magnifier` base and which is genuinely view-specific. Avoid copying fullscreen-specific Windows API assumptions into another mode without checking the required Magnification API model.

## Primary implementation map

### `source/_magnifier/__init__.py`

Owns subsystem lifecycle and current magnifier instance.

Important responsibilities:

* create the class corresponding to `MagnifiedView`;
* initialize from persisted configuration;
* start and stop the current instance;
* switch magnified views at runtime;
* keep persisted enabled state synchronized with actual start/stop success.

Changing view construction or lifecycle usually requires inspecting this file plus commands, config, and startup/shutdown behavior.

### `source/_magnifier/magnifier.py`

Shared base behavior for all magnifier views.

Important responsibilities include:

* active/inactive lifecycle;
* shared zoom state and validation;
* current coordinates and boundary clamping;
* display-change tracking;
* screen-curtain interaction;
* timer-driven update loop;
* transient-error counting and recovery delegation;
* focus/tracking integration;
* low-level mouse-hook handoff to the main thread;
* manual panning and edge movement;
* movement between screen coordinates and magnified-view center;
* shared magnifier parameters.

The update loop is latency-sensitive. The timer interval is currently 12 ms, so work added to the repeated path can run very frequently.

The low-level mouse-hook callback is especially sensitive: it intentionally records the latest coordinates and schedules work with `wx.CallAfter` instead of calling the Magnification API synchronously inside the global mouse hook. Do not move expensive work or native Magnification calls into that hook path.

### `source/_magnifier/fullscreenMagnifier.py`

Implemented fullscreen renderer and Windows Magnification API integration.

Important responsibilities include:

* native API initialization and uninitialization;
* clearing stale API state;
* fullscreen zoom/offset transforms;
* color-effect application;
* UIAccess-dependent input transforms;
* access-denied fallback when input transform is unavailable;
* center/relative tracking-mode coordinate behavior;
* spotlight/overview integration;
* recovery after repeated native API errors;
* reset to neutral magnification on shutdown;
* display/orientation-dependent view sizing.

Native failures are not merely logging concerns: repeated failures can cause API reinitialization and eventually stop the magnifier. Preserve the distinction between transient update errors, recovery attempts, and unrecoverable failure.

### `source/_magnifier/dockedMagnifier.py`

Reserved view implementation for a panel anchored to a screen edge. Rendering is currently not implemented.

An implementation is likely to require explicit design for:

* host window/control ownership and lifetime;
* dock edge and dimensions;
* source rectangle versus destination rectangle;
* how the remaining desktop/work area should behave;
* focus/mouse tracking behavior near the dock;
* DPI and multiple-monitor coordinates;
* interaction with input transformation;
* filter support;
* teardown and recovery.

Do not implement `_doUpdate` in isolation without establishing the lifecycle and native/window resources required by start/stop.

### `source/_magnifier/lensMagnifier.py`

Reserved view implementation for a movable magnified region near the tracked target. Rendering is currently not implemented.

Likely design concerns include:

* lens window/control creation;
* size and border configuration;
* positioning without covering the tracked object unnecessarily;
* screen-edge clamping;
* click/input coordinate behavior;
* rapid mouse/focus movement;
* multi-monitor transitions;
* avoiding feedback/recursive magnification of the lens itself.

### `source/_magnifier/fixedMagnifier.py`

Reserved view implementation for a floating/pinned magnified panel. Rendering is currently not implemented.

Likely design concerns include persistent geometry, monitor/DPI changes, resize/move behavior, source selection, input mapping, focus tracking, and configuration migration.

### `source/_magnifier/config.py`

Magnifier-specific access to persisted NVDA configuration.

Current configuration concepts include:

* enabled state;
* zoom level;
* pan step;
* color filter;
* magnified view;
* follow mouse;
* follow system focus;
* follow review cursor;
* follow navigator object;
* fullscreen tracking mode;
* temporary all-follow override;
* magnifier debug logging.

Zoom currently accepts 100% through 5000% in 50-percentage-point steps.

`isTrueCentered()` currently derives its behavior from fullscreen relative mode and contains comments identifying unresolved limitations. Treat it as an implementation constraint rather than a general user-facing abstraction that can automatically be reused for every new view.

When adding settings, inspect the repository configuration specification, settings GUI, user guide, profile/default behavior, and migration needs rather than editing this adapter alone.

### `source/_magnifier/commands.py`

Command-level behavior and spoken feedback.

It handles operations such as:

* enabling/disabling the magnifier;
* zooming;
* panning and edge movement;
* moving the mouse to the magnified view;
* cycling color filters;
* changing magnified view;
* toggling tracking sources;
* toggling all tracking;
* changing fullscreen tracking mode;
* starting the fullscreen overview/spotlight.

Commands often update both the running magnifier object and persisted configuration. Preserve that synchronization deliberately.

Some commands are only valid for fullscreen. New view implementations may require reevaluating these guards and messages instead of simply making every command operate on every view.

## Utility layer

The main utility package is `source/_magnifier/utils/`.

### `focusManager.py`

Resolves coordinates from enabled tracking sources such as focus, review cursor, and navigator object. Changes here can alter every magnifier view because the shared base uses this tracking result.

Inspect `tests/unit/test_magnifier/test_focusManager.py` for current precedence, coordinate, and fallback expectations before changing it.

### `mouseHook.py`

Provides the low-level mouse hook used for mouse tracking. This code participates in a global Windows hook chain and must return quickly.

Do not add logging, COM calls, Magnification API calls, blocking work, or expensive coordinate processing to the synchronous hook path without strong evidence that latency remains safe.

### `spotlightManager.py`

Implements the temporary fullscreen overview/spotlight behavior. It currently belongs to `FullScreenMagnifier`; do not assume it is generic to docked/lens/fixed modes.

### `filterHandler.py`

Defines native color-effect matrices. Filter changes cross the boundary from the `Filter` enum/configuration to Windows `MAGCOLOREFFECT` data.

### `errorHandling.py`

Contains magnifier-specific error types/decorators. Preserve the difference between user-presentable start errors and lower-level native update failures.

### `types.py`

Defines shared enums/data structures such as magnified views, tracking types, actions, filters, directions, coordinates, sizes, and fullscreen modes.

Changes to enum ordering can affect commands that cycle through `list(EnumType)`, persisted configuration values, tests, and user-visible behavior. Treat enum-order changes as behavioral changes.

## Native Windows boundary

### `source/winBindings/magnification.py`

This file binds functions from `magnification.dll`.

The current fullscreen implementation uses APIs including:

* `MagInitialize`;
* `MagUninitialize`;
* `MagSetFullscreenTransform`;
* `MagSetFullscreenColorEffect`;
* `MagSetInputTransform`.

The binding layer converts failed BOOL-returning calls into `OSError` through its `errcheck` helper. Higher-level recovery logic depends on those errors propagating correctly.

Keep raw Windows API declarations in the binding layer and behavioral policy in `_magnifier` unless repository conventions demonstrate otherwise.

### UIAccess and input transform

`FullScreenMagnifier` checks `systemUtils.hasUiAccess()` before treating input transform as supported. `MagSetInputTransform` may still return access denied, in which case the implementation disables that capability and continues without input transformation.

Changes involving touch, pen, clicking, pointer mapping, or destination/source rectangles need explicit testing both with and without UIAccess. Do not assume visual magnification proves pointer mapping is correct.

## Screen curtain interaction

The magnifier and screen curtain are intentionally mutually constrained.

The shared base:

* blocks magnifier startup while screen curtain is active;
* can disable the magnifier when screen curtain becomes active;
* remembers that state and attempts to restart after screen curtain is disabled;
* updates persisted enabled state if restart fails.

Changes to start/stop lifecycle must preserve these interactions and their user-facing failure messages.

## Display and multi-monitor concerns

The base subscribes to display-change tracking and stores display orientation/size. Coordinate clamping and fullscreen sizing currently use that state.

Any work involving multiple monitors should explicitly determine whether coordinates are:

* primary-display local;
* virtual-screen global;
* target-monitor local;
* native API source/destination coordinates.

Do not infer multi-monitor correctness from single-monitor boundary tests.

For new docked/lens/fixed modes, monitor ownership and transitions should be designed before implementation because window geometry, DPI, source rectangles, and input mapping can use different coordinate spaces.

## Configuration and UI impact

A magnifier feature can touch more than `source/_magnifier/`.

Before adding or changing a user setting, search for the `magnifier` configuration section and related GUI settings in the current branch. Check:

* configuration specification/defaults;
* GUI settings controls;
* context help and labels;
* translatable strings;
* user guide;
* command/key documentation;
* changes/release notes when user-visible behavior changes.

Use `runcheckpot.bat` when translatable strings change in a suitable Windows developer environment.

## Test map

Dedicated unit tests live under `tests/unit/test_magnifier/`.

Current test files include:

* `test_magnifier.py` for shared base behavior;
* `test_fullscreenMagnifier.py` for fullscreen calculations/native integration behavior;
* `test_focusManager.py` for tracking-coordinate logic;
* `test_magnifierCommands.py` for command behavior;
* `test_mouseHook.py` for hook behavior;
* `test_spotlightManager.py` for overview/spotlight behavior.

Search these files for the method or concept being changed before adding new tests.

New docked/lens/fixed implementations should receive dedicated test files once they contain behavior substantial enough to test independently. Shared behavior should normally stay in shared/base tests rather than being copied into each view's test file.

## Validation by change type

### Shared base/tracking change

Usually inspect/run:

* `test_magnifier.py`;
* `test_focusManager.py` when tracking changes;
* `test_mouseHook.py` when mouse tracking changes;
* relevant command tests;
* broader magnifier tests if behavior crosses view boundaries.

Manual Windows validation is appropriate when movement, timing, focus, or real cursor behavior changes.

### Fullscreen rendering/native change

Usually inspect/run:

* `test_fullscreenMagnifier.py`;
* shared magnifier tests;
* source build when bindings/native interactions change;
* real fullscreen magnifier startup/shutdown;
* zoom and panning;
* filter behavior;
* overview/spotlight when touched;
* UIAccess input-transform behavior when relevant;
* multi-monitor behavior for coordinate changes.

### Command/configuration change

Usually inspect/run command tests plus config-related tests, translation checks for user-facing strings, and user-guide updates when commands/settings change.

### New view implementation

Before calling a new view complete, validate at least:

* clean repeated start/stop;
* switching from/to fullscreen and other implemented views;
* zoom changes;
* each supported tracking source;
* manual panning if supported;
* filters if supported;
* screen edges;
* display/DPI changes;
* multi-monitor movement when supported;
* screen-curtain interaction;
* failures during native/window initialization;
* cleanup after failure;
* persisted config state;
* commands that should be supported or rejected.

Document intentionally unsupported functions rather than silently inheriting commands that do nothing.

## Performance invariants

Treat these paths as performance-sensitive:

* timer-driven update work;
* focus coordinate resolution;
* synchronous low-level mouse-hook callback;
* native transform calls;
* per-frame coordinate conversion;
* logging inside repeated paths.

When changing them:

* avoid unnecessary COM/UIA calls;
* avoid repeated allocations or tree walks where practical;
* keep mouse-hook work minimal;
* avoid verbose normal-level logging per frame/event;
* measure latency/CPU when optimization or regression risk is material.

Do not claim a performance improvement from code structure alone.

## Error-handling invariants

Preserve these distinctions:

* start failure that should be presented to the user;
* transient update failure;
* repeated failure that triggers recovery;
* recovery failure that stops the magnifier;
* access-denied input transform that degrades functionality without necessarily stopping visual magnification.

Avoid broad exception suppression around the main update path because it can bypass recovery accounting. Conversely, an optional capability such as input transform may deliberately degrade when access is unavailable.

## Recommended agent workflow for a magnifier task

1. Read this guide and `CHANGE_IMPACT.md`.
2. Identify whether the task is shared architecture, fullscreen, tracking, commands/config, or a new view.
3. Read the corresponding implementation files and dedicated tests.
4. Search call sites/config/UI only as far as demonstrated dependencies require.
5. Write or update targeted tests before broad validation where practical.
6. Report V0-V3 evidence using `VALIDATION.md`.
7. For visual, multi-monitor, pointer, or timing behavior, explicitly list manual Windows validation still required.
8. Verify the complete branch diff before PR publication.

## Questions before implementing docked, lens, or fixed rendering

Answer these explicitly in the implementation plan:

1. Which Windows Magnification API model will render the view: fullscreen transform or magnifier control/window APIs?
2. Who owns the native/window resource and where is it initialized and destroyed?
3. What coordinate space defines source and destination rectangles?
4. What happens on DPI/display changes and cross-monitor movement?
5. How are mouse/touch/pen coordinates mapped?
6. Which filters are supported?
7. Which existing commands apply and which must be rejected or adapted?
8. How is the magnifier prevented from recursively magnifying its own window where relevant?
9. What is the failure/recovery strategy?
10. Which behavior can be unit-tested and which requires real Windows visual/manual validation?

Resolving these before writing `_doUpdate` reduces the risk of building a renderer that works only in the simplest single-monitor visual case.
