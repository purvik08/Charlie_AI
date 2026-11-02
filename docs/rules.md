# Engineering and Product Rules

## Local-first operation

- Core productivity features must work without external accounts or network
  access.
- No telemetry, automatic cloud sync, or silent transfer of user content.
- Network-dependent features must be optional and clearly described.

## Data and models

- Store user workspace data only under the configured `data_dir`.
- Keep model weights, vendor repositories, caches, credentials, virtual
  environments, and generated data out of Git.
- Do not delete or overwrite user model/data files without explicit approval.

## Runtime behavior

- Optional adapters must fail locally with actionable guidance.
- Prefer a ready local Colibri server for free-form chat; fall back to the
  configured GGUF route when it is unavailable.
- Do not block the Tk UI thread with inference or document processing.
- Allow only one active desktop request at a time; disable quick actions and
  attachments while that request is running.
- Direct deterministic commands should be routed before calling an LLM.
- Preserve confirmation handling for lock, shutdown, and restart.
- Restrict app/folder launch requests to the project's allowlist.

## Quality bar

- Use focused tests for behavior changes and run the full project suite before
  handoff when practical.
- Keep `README.md`, `docs/architecture.md`, and configuration examples aligned
  with the implementation.
- Keep `KNOWN_ISSUES.md` limited to current operational limits and record
  resolved reliability fixes in `CHANGES.md`.
- Use plain language in user-facing errors and state which dependency or
  configuration is missing.
