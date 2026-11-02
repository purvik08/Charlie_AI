# Known Issues and Operational Limits

Audit updated: 2026-11-03.

## Fixed in the current workspace

- Nested `llama.*` configuration now applies correctly to model context,
  threads, GPU layers, generation limits, and timeouts.
- A missing configured `complex` model now produces a clear local error; it
  cannot silently downgrade to TinyLlama unless `allow_task_fallback` is
  explicitly enabled.
- Only one GGUF model is resident by default. Loading a different model evicts
  the prior engine to control RAM/VRAM use.
- TinyLlama and Gemma use model-family prompt templates instead of one generic
  chat format.
- Timeout recovery is defensive and an empty timed-out generation now reports
  an `InferenceError` rather than pretending to have a response.
- Screen captures are temporary by default. Retention is opt-in, bounded by age
  and count, and `Clear screen captures` removes retained files.
- GUI requests are serialized: input, quick actions, attachments, and drops are
  disabled while an active request runs.
- Animation callback failures are logged instead of being silently swallowed.
- `pytest` is scoped to `tests/`, excluding bundled vendor test trees.
- Retrieval-memory connections and test SQLite connections are explicitly
  closed, removing the Windows test-cleanup handle leak.

## Remaining limits

### Optional runtime coverage

GLM-OCR, PaddleOCR/Tesseract, Docling, Colibri, and real GGUF inference depend
on locally installed models/runtimes. The default suite tests their safe
fallback behavior, but full end-to-end verification requires those optional
assets on the target machine.

**Mitigation:** keep optional integration checks separate from the fast test
suite and run them after installing the intended runtime/model combination.

### Screen reading scope

The UI button reads the primary display by default. Set
`screen_capture.mode` to `all` to capture all connected displays. Arbitrary
drag-to-select regions are not yet exposed in the UI.

**Mitigation:** use primary-display mode for speed/privacy, or `all` where the
extra coverage is necessary. A visual region-selection overlay remains a
future UX enhancement.

### Platform validation

The desktop UI has been exercised on Windows. macOS and Linux behavior,
particularly transparent windows and desktop capture permissions, still needs
platform-specific smoke testing.
