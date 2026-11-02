# Known Issues and Follow-up Fixes

Audit date: 2026-11-03. Items marked **verified** were reproduced during the
audit or are directly reachable from the current code path. The remaining
items are implementation risks found by code review and should be addressed
before treating the relevant feature as production-ready.

## High priority

### 1. Nested Llama settings are ignored (**verified**)

`ModelManager` receives the raw configuration dictionary but reads values such
as `llama.context_size` as literal top-level dictionary keys. A standard nested
configuration such as `{"llama": {"context_size": 1024}}` therefore still
uses the defaults (`2048` context and `30` seconds timeout). This means users
cannot reliably tune model context, CPU threads, GPU layers, or timeouts.

**Fix:** give `ModelManager` a dot-path lookup helper (or pass the `Config`
object rather than its raw dictionary) and add tests for every supported
`llama.*` setting.

### 2. Complex requests silently fall back to TinyLlama (**verified**)

When `model_routing.complex` names a model that is not installed, model
resolution chooses the smallest available GGUF instead of reporting that the
stronger model is unavailable. With only TinyLlama present, a complex request
is therefore processed by TinyLlama without any warning, defeating the
delegation policy.

**Fix:** resolve an explicitly configured task route strictly. Return a clear
message naming the missing route/model, or expose an explicit
`allow_task_fallback` setting that defaults to `false` for the `complex` route.
Show the selected model in the UI response or status area.

### 3. Screen captures are retained indefinitely (**verified by code review**)

Every **Read screen** action writes a full-resolution PNG to
`<data_dir>/screens/`. There is no retention count, age limit, encryption, or
UI action to review/delete captures. Screenshots can contain credentials,
personal messages, or proprietary data, and their storage can grow without
bound.

**Fix:** make capture storage opt-in or temporary by default; delete it after
OCR unless the user chooses **Keep capture**. Add configurable maximum age and
count, a **Clear screen captures** action, and documentation of the privacy
behavior.

### 4. GUI requests can run concurrently and race (**verified by code review**)

`MainPanel._on_send()` starts a worker for every call without checking whether
a request is already active. The text input is disabled during processing, but
the quick-action buttons and file-drop path remain active. Rapid clicks can
start concurrent OCR/model requests; responses can arrive out of order, status
can flip incorrectly, and two large local models may contend for memory.

**Fix:** maintain a single `request_in_progress` guard in `MainPanel`, disable
quick actions and attachment/drop handling while it is true, and offer an
explicit cancellation control. If concurrency is desired later, use request
IDs so only the active request can update the status/UI.

## Medium priority

### 5. `pytest` from the repository root collects vendor tests (**verified**)

Running `python -m pytest` traverses `PaddleOCR-main/` and stops during
collection because its optional `paddle` dependency is not installed. This
prevents a normal project-level test run.

**Fix:** add a `pytest.ini` or `[tool.pytest.ini_options]` entry with
`testpaths = ["tests"]` and `norecursedirs` for bundled vendor trees. Keep
vendor tests in their upstream environment instead of the Charlie suite.

### 6. Inference timeout/recovery path is brittle (**verified**)

The project test `UnitTimeout.test_UT_45` fails with
`AttributeError: 'LlamaCppEngine' object has no attribute '_needs_reload'`.
The normal constructor creates the attribute, but the recovery path assumes it
is present even on partially constructed/test-injected engines. The test also
expects an all-empty timed-out response to raise an `InferenceError`, while the
implementation returns a timeout string, so the intended contract is unclear.

**Fix:** initialize recovery state defensively (for example with
`getattr(self, "_needs_reload", False)`), define one timeout contract, and
cover normal, partial, empty, cancellation, and reload-after-timeout cases.

### 7. Screen reading has no monitor/region selection (**verified by code review**)

The current capture uses `ImageGrab.grab(all_screens=True)`. On multi-monitor
systems it OCRs the entire virtual desktop, which is slower, less accurate,
and may include Charlie's own always-on-top panel. Users cannot choose a
monitor or a smaller region.

**Fix:** offer **Current monitor**, **Choose region**, and **All monitors**
capture modes. Hide Charlie briefly before capture when requested and scale
large images before OCR with an accuracy/performance setting.

### 8. Loaded local models are never automatically evicted (**verified by code review**)

`ModelManager` caches each loaded engine. After a simple request and a complex
request, TinyLlama and Gemma can both remain resident until application exit.
This is likely to cause avoidable RAM/VRAM pressure on machines with limited
memory.

**Fix:** add a one-model cache by default or configurable LRU eviction, unload
the prior model before loading a different route, and show a useful message
when memory is insufficient.

### 9. Model prompt formatting is not model-family aware (**implementation risk)

All GGUF models receive the same generic `<|system|>`/`<|user|>` prompt
format. TinyLlama and other GGUF chat models can require different templates,
so responses may be poor or may include prompt artifacts even when inference
is working.

**Fix:** read the GGUF chat-template metadata when available, provide model
template presets, and test TinyLlama/Gemma with a short conversational smoke
suite.

### 10. GUI callback failures are largely silent (**verified by code review**)

The animation scheduler and several UI cleanup paths catch broad exceptions
and discard them. A broken callback can leave the UI stale without an error in
the chat or an actionable log record.

**Fix:** replace bare suppression with structured logging, preserve the event
loop, and show a non-blocking diagnostic notification for user-visible
failures.

## Low priority and test quality

### 11. SQLite test cleanup is flaky on Windows (**verified**)

`UnitMemory.test_UT_38` can fail cleanup with `WinError 32` because another
test opens `m.db` through raw `sqlite3.connect(...)` and does not close it.
This is a test-harness resource leak rather than a user-facing memory feature
failure, but it makes the suite unreliable on Windows.

**Fix:** use a context manager for every test SQLite connection and run tests
in isolated temporary directories. Add a CI job on Windows to catch file-handle
regressions.

### 12. Optional features still have uneven end-to-end coverage

GLM-OCR weights/runtime, PaddleOCR/Tesseract, Docling, Colibri, GUI display
behavior, and real GGUF inference are only smoke-tested or skipped when their
optional dependency is absent. The focused non-optional test subset passed
59 tests during this audit, but that does not prove those integrations work in
every supported setup.

**Fix:** maintain a separate, opt-in integration test matrix with pinned
models/dependencies, real image/document fixtures, and a Windows GUI smoke
test. Keep it separate from the fast default unit suite.

## Existing product limitations

- General chat requires a usable local GGUF model or an available Colibri
  service.
- GLM-OCR is image-only; PDFs use the fallback OCR path.
- The first GLM-OCR run can require downloading support files.
- Web/deep research is an optional online feature.
- The desktop UI remains primarily validated on Windows, not comprehensively
  on macOS or Linux.
