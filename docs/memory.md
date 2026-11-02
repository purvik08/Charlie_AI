# Project Status Log

## 2026-11-03 — Current baseline

- Repository version is `0.9.0` in `pyproject.toml`.
- `main.py` dispatches to the GUI with no arguments and to the Typer CLI with
  arguments.
- The current UI is a polished floating-orb Tkinter assistant with quick
  actions, file attachment, drag-and-drop, async response handling, and tray
  support.
- OCR supports bundled GLM-OCR weights for image text/table/formula extraction
  and falls back to PaddleOCR/Tesseract; PDFs follow the fallback path.
- Document parsing, web research, and a Colibri adapter are implemented as
  optional integrations.
- User-facing README and all `docs/` reference material were synchronized with
  this architecture.

## Working assumptions

- Local model files, GLM-OCR weights, and vendor trees are intentionally ignored
  by Git because of their size.
- Core task utilities remain useful without any external model or network.
- Optional integrations must remain graceful when their runtime is absent.
