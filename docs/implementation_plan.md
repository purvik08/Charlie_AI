# Architecture: Charlie CLI + Modular Assistant

## Overview

Charlie is a **Typer-based CLI** with **Rich output** that reuses the existing `OfflineAssistant` class via a `FeatureRegistry` + `EventBus` architecture. Three layers:

1. **Core** (`core/`) — EventBus, FeatureRegistry, BaseFeature, Command, CommandResult
2. **Features** (`features/`) — Extracted feature modules (system_info, notes, todos, reminders, file_search, tts)
3. **Interface** (`cli/`) — CLI entry point; GUI (`ui/`) unchanged

## Core Infrastructure (`core/`)

| File | Purpose |
|------|---------|
| `core/events.py` | EventBus + Event types (`Events` namespace) |
| `core/registry.py` | `FeatureRegistry` — discover, register, lifecycle |
| `core/base.py` | `BaseFeature`, `Command`, `CommandResult`, `FeatureConfig` |
| `core/__init__.py` | Package exports |

## Feature Modules (`features/`)

| Module | Commands | Key |
|--------|----------|-----|
| `features/system_info/` | `system.info`, `system.battery` | Uses `assistant.SystemInfo` |
| `features/notes/` | `note.create`, `note.list`, `note.search`, `note.show` | Uses `assistant.NoteTaking` |
| `features/todos/` | `todo.add`, `todo.list`, `todo.done`, `todo.remove`, `todo.search` | Uses `assistant.TodoList` |
| `file_search/` | `file.find`, `file.search` | Uses `assistant.FileSearch` |
| `reminders/` | `remind.add`, `remind.list`, `remind.remove` | Uses `assistant.Reminders` |
| `tts/` | `tts.say`, `tts.stop` | Pyttsx3Backend + optional PiperBackend |

## CLI (`cli/`)

- **Framework**: Typer + Rich
- **Entry**: `cli/main.py` → `app` (Typer object)
- **Console script**: `charlie` (via `pyproject.toml`)
- **Subcommands**: `time`, `date`, `system`, `file`, `note`, `todo`, `remind`, `app`, `chat`, `config`, `version`
- **Shared**: `get_assistant()` singleton from `cli.core`

## GUI (`ui/`)

- **Unchanged** — `FloatingAssistantGUI` / `MainPanel` still work
- Depends on `OfflineAssistant` directly (no breaking changes)
- Quick actions map to CLI commands

## Dead Code Removed

- `llama_engine.py` — duplicate of `model.py`
- `test_model.py`, `test_model2.py` — referenced removed `OllamaModel`
- `debug_test.py` — standalone test script
- `gui.py` — legacy GUI wrapper

## Key Files

| File | Role |
|------|------|
| `assistant.py` | `OfflineAssistant` + `FeatureRegistry` integration |
| `config.py` / `config.json` | Single config source (llama + features + features flags) |
| `model.py` | `ModelManager` / `LlamaCppEngine` for GGUF |
| `requirements.txt` | `typer`, `rich`, `llama-cpp-python`, `pyttsx3` |
| `pyproject.toml` | `charlie` console script entry point |
| `tests/run_tests.py` | 7 standalone test files, all passing |

## Running Charlie

```bash
# GUI
python main.py

# CLI
python -m cli.main --help              # all commands
python -m cli.main time now           # current time
python -m cli.main system info        # system info (table)
python -m cli.main note create "Title" "Content"  # create note
python -m cli.main todo add "Task" --priority high  # add todo
python -m cli.main remind add "Remember this" --in 30  # set reminder
python -m cli.main chat                 # interactive chat
python -m cli.main config               # show config JSON
python -m cli.main version              # version info
```

## Testing

- **7 test files** pass: `test_cli.py`, `test_config.py`, `test_file_search.py`, `test_note_taking.py`, `test_reminders.py`, `test_system_info.py`, `test_todo_list.py`
- Run: `python tests/run_tests.py`
- All CLI commands verified via `charlie <command>` (installed console script)
- GUI: `python main.py` launches without errors