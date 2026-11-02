# Change Log

## Current repository state

The project has evolved from a small offline assistant into a modular desktop
and CLI application. The current implementation includes:

- A Tkinter floating assistant with responsive worker-queue message handling,
  system tray support, quick actions, attachment picker, and drag-and-drop.
- A Typer CLI for core productivity tasks, OCR, document conversion, web
  research, and Colibri management.
- Rule-based intent routing, confirmation handling for consequential local
  actions, conversation history, and SQLite retrieval memory.
- GLM-OCR integration for image text, formula, and table recognition, with
  PaddleOCR/Tesseract fallback and PDF routing.
- Docling-based document conversion with fallback extraction paths.
- GPT Researcher and Colibri adapters behind optional configuration flags.
- Expanded tests covering the integrations and GLM-OCR adapter behavior.
- Colibri-first free-form chat with automatic GGUF fallback when its local
  server is unavailable.
- Strict complex-model routing, nested Llama configuration support, one-model
  GGUF residency, family-specific TinyLlama/Gemma prompts, and visible model
  status in the desktop header.
- Safer screen reading: temporary captures by default, configurable retention,
  a clear-captures command, and serialized desktop requests.
- Project pytest discovery is restricted to `tests/`; SQLite connections and
  animation failures are handled more reliably.

## Historical corrections retained in the codebase

Earlier stability work fixed command-history recording, strict time/date/open
routing, reminder resilience, feature gating, to-do validation, safe local
file-content search, and empty-input handling. The active source and test suite
are authoritative; this file is a high-level record rather than a release log.
