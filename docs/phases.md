# Development Roadmap

## Completed foundation

- Modular assistant, configuration, local persistence, intent routing, and
  productivity features.
- Desktop GUI and CLI interfaces.
- Colibri-first chat with GGUF fallback, OCR/GLM-OCR, document parsing,
  research, screen reading, and drag-and-drop integrations.
- Unit and integration coverage for the core and adapter contracts.

## Stabilization (next)

- Establish test/CI profiles for core-only and optional-runtime coverage.
- Benchmark startup, chat, document parsing, and GLM-OCR memory/latency.
- Validate GUI behavior across supported Windows configurations.
- Improve install, diagnostic, and missing-dependency guidance.
- Add screen-region selection and platform-specific GUI smoke coverage.

## Product polish (later)

- GUI settings for feature flags and model engines.
- Accessible keyboard navigation, stronger screen-reader semantics, and
  cross-platform UI review.
- Recurring reminders, data export/import, and backup guidance.
- Packaging strategy that handles external runtimes and large local assets.

## Principles

Keep the application local-first, modular, explicit about optional networking,
and resilient when a model or feature backend is unavailable.
