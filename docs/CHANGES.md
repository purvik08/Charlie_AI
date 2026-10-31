# Changes made while preparing the Software Engineering practical file

Every item below was found by running the new test suite (tests/test_charlie_suite.py)
against the original code, or by reading it. SD numbers match Practical 6.

| ID | Problem | Fix |
|----|---------|-----|
| SD-01 | `core/tools.py` had an extra `)` (SyntaxError) and used the undefined `Tool.SAFETY_SAFE`. | Removed the bracket; use `TOOL_SAFETY_SAFE`. |
| SD-02 | GUI/CLI called `submit_command` / `add_to_history`, which did not exist. | Added both to `OfflineAssistant`. |
| SD-03 | Loose keyword rules ("open", "date", "time") captured ordinary questions. | Strict full-match patterns for time/date; open-requests only when the command starts with open/launch/start. |
| SD-04 | Reminder checker thread died on a malformed record. | Records are skipped; the loop catches all errors; interval is configurable. |
| SD-05 | Conversation history was never appended. | `submit_command` records every exchange. |
| SD-06 | RetrievalMemory not connected. | Connected (stores each exchange in chat.db; retrieves 2 related records for the prompt). |
| SD-07 | `core/tool_registry.py` imported non-existent modules. | Replaced by a small `build_registry(assistant)`. |
| SD-08 | `timeout_seconds` was never enforced. | Generation stops after the timeout (partial text, or an InferenceError if nothing was produced). |
| SD-09 | Any text could be passed to the OS "open" call (assistant and `app open`). | Allowlist applied everywhere. |
| SD-10 | Housekeeping. | Added `main.py`; moved requirements/pyproject/.gitignore/LICENSE to the root; removed duplicate `__init__`; relative `data_dir`; README corrected; version 0.9.0. |
| SD-11 | Intents without handlers (volume, mute, screenshot, lock, shutdown, restart). | Explicit "not supported" reply; lock/shutdown/restart ask for confirmation. |
| SD-12 | Model routing by file name ending in `.gguf` never matched. | `.gguf` suffix is stripped before matching. |
| SD-13 | `search_in_file` read any path. | Restricted to the data directory. |
| SD-14 | Invalid to-do priorities accepted by `TodoList`. | `ValueError` for anything but low/medium/high; case-insensitive. |
| SD-15 | Disabled feature answered "Please specify what task to add". | Accurate "disabled" / "unavailable" messages. |
| SD-16 | Completing a completed item overwrote `completed_at`. | Original time kept. |
| SD-17 | Two notes with the same title in one second overwrote each other. | Numeric suffix added. |
| SD-18 | Negative reminder intervals accepted. | `Reminders.schedule_in` rejects them (used by CLI and assistant). |
| SD-19 | Task text was lower-cased. | Original capitalisation kept. |
| SD-20 | Empty input reached the language model through `process_command`. | Returns "Please type a command or question." |

Run the suite: `python tests/run_suite.py` (standard library only; also works with pytest).
Tests that need typer, llama-cpp-python, a model file, a display or another OS report **Blocked**
until you run them on a machine that has those.
