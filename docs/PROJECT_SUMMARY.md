# Project Summary

Charlie is a Python-based, local-first AI assistant available as a Tkinter
desktop app and a Typer CLI. Its core orchestrator is `OfflineAssistant`, which
routes direct requests to local productivity features and routes general chat to
an available local model.

## Current capabilities

- Floating-orb desktop chat with quick actions, file attachment, drag/drop,
  status feedback, message history, and tray integration.
- CLI commands for productivity, system information, OCR, document conversion,
  research, and local model services.
- Local notes, to-dos, reminders, file search, and SQLite retrieval memory.
- Colibri-first local chat with TinyLlama/Gemma GGUF fallback, plus optional TTS.
- GLM-OCR image recognition with PaddleOCR/Tesseract fallback.
- On-demand screen reading: a desktop quick action captures the current display
  locally and extracts its visible text through the OCR stack; captures are
  temporary by default.
- Optional Docling parsing and GPT Researcher web/deep research.

## Repository conventions

Source, tests, configurations, model documentation, and user docs are tracked.
Large model binaries and downloaded vendor source trees are not tracked. See
`README.md` for setup and everyday workflows, `architecture.md` for internals,
and `issues.md` for active limitations.
