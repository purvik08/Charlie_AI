# Implementation Status and Next Plan

## Completed

- Modular `OfflineAssistant` orchestration and rule-based intent detection.
- Tkinter floating assistant and Typer CLI.
- Local productivity features: time/date, system data, file search, notes,
  to-dos, reminders, and allowlisted app/folder opening.
- Colibri-first local chat, GGUF fallback/discovery, retrieval memory, and TTS.
- OCR, GLM-OCR, document parsing, web research, drag-and-drop, and system tray
  integrations.
- Offline-ready GLM-OCR support files, safer temporary screen captures, and
  focused integration/regression tests.

## Next priorities

1. Run repeatable performance and memory benchmarks for GGUF and GLM-OCR.
2. Add a CI workflow that runs the test suite without requiring heavyweight
   optional runtimes.
3. Improve end-to-end GUI coverage and accessibility checks.
4. Add structured configuration validation and clearer runtime diagnostics.
5. Add a visual region-selection overlay for screen OCR and document the
   release strategy for GLM-OCR support files.

## Before a release

- Run `python -m pytest tests -q`.
- Exercise GUI input, attachment picker, drag-and-drop, tray menu, and reminder
  behavior on the release platform.
- Test a real image with GLM-OCR and a PDF with the fallback OCR path.
- Verify the optional research path fails safely and that Colibri falls back to
  GGUF chat when its local server is unavailable.
- Package vendor/runtime instructions without committing model weights or large
  third-party source trees.
