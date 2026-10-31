# Test Suite for Offline AI Assistant

This directory contains unit tests for the Offline AI Assistant project.

## Test Files

- `test_config.py` - Tests for the Config class
- `test_file_search.py` - Tests for the FileSearch class
- `test_note_taking.py` - Tests for the NoteTaking class
- `test_reminders.py` - Tests for the Reminders class
- `test_system_info.py` - Tests for the SystemInfo class
- `test_todo_list.py` - Tests for the TodoList class
- `run_tests.py` - Test runner script

## Running the Tests

To run all tests:

```bash
python run_tests.py
```

To run individual test files:

```bash
python test_<name>.py
```

## Test Coverage

The tests cover:
- Class initialization
- Core functionality
- Data persistence (save/load)
- Edge cases and error conditions