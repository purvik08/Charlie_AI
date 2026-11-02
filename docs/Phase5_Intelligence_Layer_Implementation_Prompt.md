# Intelligence Layer: Current Implementation Notes

This document supersedes the earlier implementation prompt. The intelligence
layer is now part of the application rather than a planned rewrite.

## Implemented behavior

1. `OfflineAssistant.process_command()` rejects empty input and handles pending
   confirmation before any routing.
2. `IntentDetector` identifies direct tasks such as OCR, document parsing, web
   search, system operations, and productivity commands.
3. Strict rules cover natural-language command variants.
4. General questions use the configured local model manager and include a short
   recent conversation window plus retrieval-memory summaries when available.
5. `submit_command()` records successful exchanges in in-memory history and
   SQLite retrieval memory.
6. Optional adapters are feature-gated and return explanatory status instead of
   failing the entire request.

## Extension rules

- Add a direct intent/rule before extending the LLM prompt for deterministic
  tasks.
- Keep model calls local by default.
- Treat external research as optional and clearly surfaced.
- Preserve confirmation behavior for consequential computer actions.
- Add focused tests for new routes and fallback behavior.
