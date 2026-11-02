# Contributor Guide

## Current entry points

- GUI: `python main.py`
- CLI: `python main.py --help` or `python -m cli.main --help`
- Tests: `python -m pytest tests -q`

`main.py` starts the GUI without arguments and forwards arguments to the Typer
CLI. Both entry points construct `core.assistant.OfflineAssistant` and share
the configured data directory.

## Architecture map

- `core/assistant.py` owns request routing, feature initialization, conversation
  history, and reminder lifecycle.
- `core/intent.py` performs rule-based intent recognition before general chat.
- `core/complexity.py` keeps TinyLlama as the default chat model and assigns
  long, multi-step, code/structured, and analytical requests to the configured
  stronger local route.
- `models/model.py` discovers and invokes local GGUF models through
  `llama-cpp-python`; `features/local_llm/colibri_adapter.py` integrates a
  separately-running Colibri server.
- `ui/` is the Tkinter floating-orb chat interface. Keep UI work on the Tk
  thread; `MainPanel` uses a queue to receive worker results.
- `features/` contains integrations for OCR, document conversion, research,
  local LLM services, and productivity modules.

## Commands worth checking

```bash
python main.py time now
python main.py todo add "Review report" --priority high
python main.py ocr glm path/to/image.png --task text
python main.py parse info
python main.py colibri status
```

## Local assets and configuration

`config.json` is the repository-level configuration. `.env`, virtual
environments, generated data, GGUF files, GLM-OCR weights, and bundled vendor
source trees are intentionally not tracked. The default `data_dir` holds
`chat.db`, notes, to-dos, reminders, OCR output, and document output.

GLM-OCR uses `models/image_to_text/model.safetensors`; it loads lazily and
downloads only its small support files on first use. Do not commit the weight
file or generated support files.

## Change discipline

- Preserve the local-first default and explicitly label any network path.
- Keep feature failures graceful: optional runtimes must not stop core commands.
- Add or update focused tests with behavior changes.
- Run `python -m pytest tests -q` and `git diff --check` before handoff.
