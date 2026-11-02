# Issue Tracker

## Current status

The codebase is feature-rich but depends on several optional heavyweight
runtimes. The issues below are current engineering risks, not confirmed user
data-loss or security defects.

| ID | Priority | Status | Description |
| --- | --- | --- | --- |
| ISS-RUNTIME-001 | High | Open | GLM-OCR needs Torch, Transformers, Accelerate, substantial RAM/VRAM, and small support files fetched on first use. |
| ISS-TEST-002 | High | Open | The full test suite needs a documented dependency matrix; some integrations depend on optional local services or packages. |
| ISS-GUI-003 | Medium | Open | GUI behavior needs repeatable end-to-end tests across Windows display scaling and Tk/DnD environments. |
| ISS-DOC-004 | Medium | Open | Bundled third-party source trees require explicit release packaging and update policies. |
| ISS-UX-005 | Medium | Open | There is no built-in configuration screen for feature flags, model paths, or OCR engine selection. |
| ISS-DATA-006 | Medium | Open | Notes, reminders, and to-dos are local plaintext/JSON; encryption and backup/export flows are not implemented. |
| ISS-FEAT-007 | Low | Open | Reminders are one-time only; recurrence is not implemented. |
| ISS-OBS-008 | Low | Open | No benchmark or structured local diagnostic report is available yet. |

## Resolved or implemented

- System tray, animated panel transitions, gradient chat bubbles, and drag/drop
  are implemented.
- Empty input, loose routing, malformed reminder resilience, safe file-content
  search boundaries, and confirmation handling have dedicated code paths and
  tests.

## Reporting guidance

Include OS, Python version, feature configuration, selected model engine,
command or UI action, exact error, and whether an optional runtime is installed.
Do not include personal note, reminder, or chat content in a public report.
