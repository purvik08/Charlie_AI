# System Architecture

## Overview
This document describes the architectural structure of the Offline AI Assistant, including file organization, data flow, component responsibilities, and storage mechanisms.

## Directory Structure
```
OFFLINE_ASSISTANT/
│
├── docs/                     # Documentation files
│   ├── architecture.md       # This file
│   ├── design.md             # W5HH analysis
│   ├── issues.md             # Known issues
│   ├── memory.md             # Project status log
│   ├── phases.md             # Development roadmap
│   ├── prd.md                # Product requirements
│   └── rules.md              # Constraints and guidelines
│
├── assistant.py              # Core assistant logic and feature modules
├── config.py                 # Configuration management (JSON + environment)
├── config.json               # Primary configuration file
├── .env                      # Environment variables (optional, not in repo)
├── gui.py                    # Tkinter-based graphical user interface
├── main.py                   # Application entry point
├── model.py                  # Ollama LLM interface wrapper
├── modelfile                 # Ollama model configuration template
├── requirements.txt          # Python dependencies
├── system_prompts.txt        # LLM system prompt instructions
├── LICENSE                   # MIT license
└── README.md                 # User documentation
```

## Data Storage Structure
All user data is stored locally in the user's home directory under `~/offline_assistant_data/` (configurable via `config.json`):

```
~/offline_assistant_data/
│
├── chat.db                   # SQLite database for conversation history
├── config.json               # User-specific configuration override
├── notes/                    # Directory containing text notes
│   ├── YYYYMMD_HH_title.txt
│   └── ...
├── reminders.json 2.0
│   └── ...
```

### Detailed Data Components

#### 1. Configuration System
- **Primary**: `config.json` in application directory (default values)
- **Override**: `.env` file for environment variables (not committed)
- **User Customization**: `~/offline_assistant_data/config.json` (user-specific settings)
- **Priority**: User config > Environment > Default config

#### 2. Conversation History
- **Storage**: SQLite database (`chat.db`)
- **Table Structure**:
  ```sql
  CREATE IF NOT EXISTS conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      user_input TEXT NOT NULL,
      assistant_response TEXT NOT NULL
  );
  ```
- **Management**: Limited by `memory_limit` setting (default 100 entries)

#### 3. Notes
- **Location**: `~/offline_assistant_data/notes/`
- **Format**: Plain text files with metadata header
- **Filename Pattern**: `{timestamp}_{sanitized_title}.txt`
- **Content Format**:
  ```
  Title: [note title]
  Created: [ISO timestamp]
  --------------------------------
  [note content]
  ```

#### 4. To-Do List
- **Storage**: `~/offline_assistant_data/todo.json`
- **Format**: JSON array of objects
- **Object Structure**:
  ```json
  {
    "id": 1234567890000,
    "task": "Task description",
    "completed": false,
    "priority": "medium",
    "created": "2026-07-29T10:30:00",
    "completed_at": null
  }
  ```

#### 5. Reminders
- **Storage**: `~/offline_assistant_data/reminders.json`
- **Format**: JSON array of objects
- **Object Structure**:
  ```json
  {
    "id": 1234567890000,
    "text": "Reminder description",
    "remind_at": "2026-07-29T15:30:00",
    "created": "2026-07-29T10:30:00",
    "triggered": false
  }
  ```

## Component Responsibilities

### 1. Main (`main.py`)
- **Role**: Application entry point and lifecycle manager
- **Responsibilities**:
  - Initialize configuration
  - Create assistant instance
  - Launch GUI
  - Handle graceful shutdown
  - Global exception handling

### 2. Assistant (`assistant.py`)
- **Role**: Core business logic and feature implementation
- **Responsibilities**:
  - Initialize all feature modules
  - Process user commands
  - Manage conversation history
  - Coordinate between features
  - Handle background services (reminders)
  - Provide text-to-speech interface

### 3. GUI (`gui.py`)
- **Role**: User interface and interaction layer
- **Responsibilities**:
  - Create and manage Tkinter window
  - Display conversation history
  - Handle user input events
  - Show status and feedback
  - Manage threading for responsive UI
  - Handle window closing events

### 4. Model (`model.py`)
- **Role**: Interface to Ollama LLM service
- **Responsibilities**:
  - Manage HTTP connection to Ollama
  - Handle model loading and status checking
  - Process chat and generation requests
  - Format prompts with system instructions
  - Handle connection errors and timeouts
  - Provide model listing and pulling capabilities

### 5. Configuration (`config.py`)
- **Role**: Centralized configuration management
- **Responsibilities**:
  - Load default configuration
  - Merge with user configuration
  - Load environment variables
  - Provide get/set methods for configuration
  - Persist changes to disk
  - Validate configuration values

## Data Flow

### User Interaction Flow
1. User types message in GUI input field
2. GUI captures Enter key or button click
3. GUI disables input, shows "Processing" status
4. GUI sends message to assistant via thread
5. Assistant processes command:
   - Checks for feature-specific commands (time, file, etc.)
   - If none, sends to LLM via model.py
   - Adds to conversation history
   - Gets response
6. Assistant returns response to GUI thread
7. GUI enables input, displays response
8. GUI triggers TTS to speak response
9. GUI scrolls to show latest message

### Background Services
- **Reminder Checker**:
  - Runs in separate daemon thread
  - Wakes every 30 seconds to check due reminders
  - Triggers callback in main thread when reminder fires
  - Callback shows notification and speaks reminder

## External Dependencies

### 1. Ollama Service
- **Type**: Local LLM server
- **Interface**: HTTP API (default: http://localhost:11434)
- **Responsibility**: Model inference and text generation
- **Failure Mode**: Graceful degradation to feature-only mode

### 2. System Libraries
- **pyttsx3**: Text-to-speech (offline)
- **requests**: HTTP client for Ollama communication
- **psutil** (optional): System information gathering
- **tkinter**: GUI framework (standard library)

## Security and Privacy Considerations

### Data Locality
- ✅ All data stored locally
- ✅ No network calls except to local Ollama
- ✅ No telemetry or data collection
- ✅ User controls all data retention

### Communication Security
- ⚠️ Local HTTP to Ollama (not encrypted, but localhost-only)
- ✅ No external internet connections by default
- ✅ Firewall-friendly (only binds to localhost)

### Data Protection
- ✅ Files stored in user's home directory
- ✅ No automatic cloud sync
- ✅ Manual export/import planned for future
- ✅ Sensitive data (reminders, notes) stored in plain text (consider encryption in future)

## Scalability and Performance

### Horizontal Scaling
- Not applicable (single-user desktop application)

### Vertical Scaling
- **Memory Usage**: 
  - Base: ~50MB (Python + Tkinter)
  - LLM: Depends on model size (qwen3:1.7b ~2-4GB RAM)
  - Conversation history: Minimal (text only)
- **CPU Usage**:
  - Idle: Minimal
  - Processing: Spikes during LLM inference
  - TTS: Low continuous during speech
- **Storage**: 
  - Grows linearly with usage
  - Text-based storage is efficient
  - Configurable limits for history

## Extensibility Points

### Adding New Features
1. Create new class in `assistant.py` following existing patterns
2. Register initialization in `_initialize_components()` method
3. Add command parsing in `process_command()` method
4. Add GUI elements if needed in `gui.py`
5. Update configuration if feature requires settings

### Customizing LLM Behavior
1. Modify `system_prompts.txt` for different AI persona
2. Adjust parameters in `modelfile` and recreate model
3. Change model name in `config.json`
4. Adjust temperature/max_tokens in `model.py` calls

### Alternative Storage Backends
1. Modify storage methods in feature classes
2. Update file paths in configuration
3. Maintain backward compatibility with migration scripts

## Deployment Considerations

### Packaging
- **Windows**: PyInstaller to create .exe
- **macOS**: py2app to create .app bundle
- **Linux**: AppImage or distribution-specific packages
- **Cross-platform**: Consider Briefcase or BeeWare

### Installation Requirements
- Python 3.8+
- Ollama installed and running
- Compatible language model pulled
- Optional: espeak for better TTS on Linux

### Configuration for Deployment
- Set `llm_model_name` in config.json
- Adjust `tts_rate` and `tts_volume` as needed
- Disable features via `features` object if required
- Set custom data directory if preferred

## Diagram of Component Interactions

```
[User] 
    ↓ (GUI Input)
[GUI Layer] ←→ [Assistant Core] 
    ↓ (Command)        ↓ (Feature Calls)
[Feature Modules]    [Model Interface] 
    ↓ (LLM Request)       ↓ (HTTP)
[Ollama Service] ←→ [Local LLM Model]
    ↑ (Response)         ↑ (Formatted)
[Assistant Core] ←→ [Conversation History]
    ↓ (Response)
[GUI Display] ←→ [TTS Engine]
    ↓ (Speech)
[User Hears Response]
```
