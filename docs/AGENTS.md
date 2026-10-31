# AGENTS.md - Offline AI Assistant

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure you have a GGUF model in ./models/ (e.g., qwen3-1.7b-q4_k_m.gguf)
# Download from Hugging Face if needed

# Run the application
python main.py
```

## Key Commands
| Task | Command |
|------|---------|
| Run app (GUI) | `python main.py` |
| Run CLI | `python -m cli.main --help` |
| Run all tests | `python tests/run_tests.py` |
| Run single test | `python tests/test_config.py` |
| Install deps | `pip install -r requirements.txt` |

## Architecture
- **Entry point**: `main.py` → creates `OfflineAssistant` + `FloatingAssistantGUI`
- **CLI**: `cli/` package (Typer + Rich). Entry: `cli/main.py`. Reuses `OfflineAssistant` via singleton in `cli/core.py`
- **Core logic**: `assistant.py` (feature classes: FileSearch, SystemInfo, NoteTaking, TodoList, Reminders)
- **Config**: `config.py` (loads `config.json`, merges with `.env`, user dir at `~/offline_assistant_data/`)
- **LLM**: `model.py` (llama-cpp-python wrapper, ModelManager for GGUF models)
- **GUI**: `ui/` package (Tkinter glassmorphism UI with floating orb)

## Charlie CLI
Typer-based command line interface named "Charlie" with Rich output.

```bash
python -m cli.main --help          # All commands
python -m cli.main time now        # Current time
python -m cli.main date today      # Today's date
python -m cli.main system info     # System info (table)
python -m cli.main system battery  # Battery status
python -m cli.main file find <q>   # Search files in data dir
python -m cli.main file search <path> <q>  # Search text in a file
python -m cli.main note create <title> <content>
python -m cli.main note list
python -m cli.main note search <q>
python -m cli.main note show <path>
python -m cli.main todo add <task> --priority high
python -m cli.main todo list --all
python -m cli.main todo done <id>
python -m cli.main todo remove <id>
python -m cli.main todo search <q>
python -m cli.main remind add <text> --in <minutes>
python -m cli.main remind list
python -m cli.main app open <name>
python -m cli.main chat             # Interactive chat mode
python -m cli.main config           # Show current config JSON
python -m cli.main version          # Version info
```

Notes:
- `chat` interactive mode: `--voice/--no-voice` toggles TTS; prompts for voice choice if omitted; always displays the answer.
- The `charlie` console script (in `pyproject.toml`) is the installed entry point; `python -m cli.main` works without installation.
- CLI and GUI share the same data directory and config.

## Testing
- Test runner: `tests/run_tests.py` discovers and runs all `test_*.py` files
- Each test file is standalone (not pytest)
- Run single test: `python tests/test_<name>.py`

## Configuration Priority
1. User config: `~/offline_assistant_data/config.json`
2. Environment: `.env` (not committed)
3. Defaults: `config.json` in repo root

## Data Storage
All user data in `~/offline_assistant_data/`:
- `chat.db` - SQLite conversation history
- `notes/` - Text note files
- `todo.json` - To-do list
- `reminders.json` - Scheduled reminders

## External Dependencies
- **llama-cpp-python** for local LLM inference (GGUF models in `./models/`)
- **pyttsx3** for TTS (offline)
- **psutil** optional for battery/CPU info

## Common Gotchas
- No lint/typecheck configured - add if needed
- `.env` is gitignored; copy `.env.example` if it exists
- `offline_assistant_data/` is gitignored (user data)
- TTS initialization only happens if time_telling/open_apps/play_music features enabled
- GGUF model files must be present in `./models/` or discovered from Ollama blobs
- Model auto-discovery includes `~/.ollama/models/blobs` if enabled in config