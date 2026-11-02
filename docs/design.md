# Product Design

## Product intent

Charlie is a private, local-first assistant for lightweight daily work. It
combines a minimal desktop surface with a full CLI so users can choose quick
visual interaction or automation-friendly commands.

## Experience principles

1. **Local by default** — store user work locally and make online behavior
   explicit.
2. **Fast path first** — quick actions and direct commands should reach common
   operations without requiring an LLM.
3. **Graceful optionality** — unavailable OCR, document, research, or model
   runtimes explain how to proceed instead of breaking the app.
4. **Visible state** — the UI exposes ready, thinking, error, and the most
   recently used chat model while background work is running.
5. **Conservative side effects** — requests that lock, restart, or shut down a
   computer require a confirmation response.

## Interface design

The desktop design centers on a draggable floating orb. Opening it reveals a
compact dark chat panel with status, quick-action shortcuts, an attachment
control, typed input, messages, timestamps, and a typing indicator. File drops
are routed by extension to OCR or document parsing.

The CLI exposes the same task domains through dedicated commands. General chat
prefers a running local Colibri server, then falls back to the configured GGUF
route; direct commands avoid model inference. The UI accepts only one active
request at a time so responses cannot arrive out of order.

## Non-goals

Charlie does not claim to be a cloud assistant, collaboration platform, or
replacement for specialist software. It does not provide voice input, account
management, cloud sync, recurring reminders, model-training workflows, or a
guaranteed web-free install for optional model runtimes.
