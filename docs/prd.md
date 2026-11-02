# Product Requirements Document

## Product

Charlie is a local-first desktop and CLI assistant for personal productivity,
local inference, image/document understanding, and optional research.

## Users and value

It serves people who want convenient AI-assisted work while retaining control
of their files, notes, tasks, reminders, and model assets. Its primary value is
local ownership with useful direct tools that do not depend on an LLM.

## Current functional requirements

| Area | Requirement |
| --- | --- |
| Interfaces | Provide a Tkinter desktop UI and Typer CLI backed by the same assistant state. |
| Direct tasks | Support time/date, system information, notes, to-dos, reminders, file search, and allowlisted app/folder opening. |
| Conversation | Prefer a ready local Colibri server for free-form chat; otherwise route ordinary chat to TinyLlama and complex chat to the configured stronger GGUF model. |
| OCR | Recognize image text, formulas, and tables through local GLM-OCR when configured; provide OCR fallbacks. |
| Screen reading | Provide an explicit desktop action that captures the current screen locally and extracts its visible text with the OCR stack. |
| Documents | Convert supported documents through an optional parser with fallback extraction. |
| File interaction | Accept file selection and drag-and-drop in the desktop UI. |
| Data | Persist personal workspace records locally in the configured data directory. |
| Safety | Require a follow-up confirmation for lock, shutdown, and restart requests. |
| Optional online work | Keep research explicit and independently disableable. GLM-OCR support files are present locally in this workspace. |

## Non-functional requirements

- The app remains usable when optional integrations are absent.
- User data receives no telemetry or automatic cloud synchronization.
- UI inference work does not block the Tk event loop.
- Large model assets are external to normal Git history.
- Commands should return clear errors and next steps when an optional runtime is
  missing.

## Explicit non-goals

No account system, cloud collaboration, voice recognition, recurring reminders,
security-grade encrypted storage, or guarantee of current web information is
currently included.
