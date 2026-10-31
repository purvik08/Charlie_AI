# Known Issues

## LLM Integration Issues

### Slow/Empty Responses from Ollama (Fixed)
- **Issue**: The Ollama LLM integration sometimes returned empty responses due to certain models (like qwen3:1.7b) placing the response content in the 'thinking' field instead of the 'response' field.
- **Status**: Fixed
- **Workaround**: Updated the model.py generate() method to check both 'response' and 'thinking' fields.
- **Details**: 
  - The model `qwen3:1.7b` is properly installed and accessible via `ollama list`
  - Fixed the generate method in model.py to properly extract responses from either the 'response' field or fall back to the 'thinking' field
  - This resolves the AI conversational capabilities issue
  - Response times may still vary based on system load and model complexity

## UI Enhancement Features

### System Tray Integration (Implemented)
- **Feature**: Added system tray icon awareness allowing the application to minimize to tray instead of closing
- **Status**: Implemented
- **Details**:
  - Added system tray icon with show/hide and quit options
  - When window is closed, application hides to tray instead of exiting
  - Can be restored from tray or quit via tray menu
  - Requires pystray and Pillow dependencies (added to requirements.txt)

### Gradient Message Bubbles (Implemented)
- **Feature**: Enhanced message bubbles with gradient backgrounds instead of solid colors
- **Status**: Implemented
- **Details**:
  - Added gradient drawing capability to widgets module
  - Message bubbles now use vertical gradients from slightly lighter to base color
  - Provides subtle depth and visual enhancement to chat interface
  - Maintains all existing styling and theming capabilities

### Smooth UI Transitions (Implemented)
- **Feature**: Added smooth fade-in/fade-out animations for panel show/hide
- **Status**: Implemented
- **Details**:
  - Panel now fades in/out using alpha animation instead of instant show/hide
  - Provides more polished and professional user experience
  - Maintains all existing positioning and functionality

### Missing Features (Phase 1)

These features are planned for Phase 1 but not yet implemented:

1. **Test Suite** - ✅ COMPLETED
   - Created comprehensive unit tests for all core components
   - All tests are passing

2. **Documented Known Issues** - ✅ COMPLETED
   - This document

3. **Performance Benchmarks** - ❌ PENDING
   - Need to measure startup time, memory usage, and response times

## Completed Work

### Phase 0: Foundation - ✅ COMPLETED
- Modular code structure
- Professional Tkinter-based GUI
- Text-to-speech integration
- Configuration system (JSON + .env)
- All original features ported:
  - Time/date information
  - System information
  - File search
  - Note taking
  - To-do list management
  - Reminders
  - Application launcher
- Documentation (README, LICENSE, .gitignore)

### Phase 1: Stability and Testing - ⬇️ IN PROGRESS
- ✅ Test suite created and passing
- ✅ Documentation updated (README)
- ✅ Known issues documented
- ✅ LLM integration stabilization
- ⏳ Performance benchmarking
- ⏳ Official beta release (v0.1.0)

## Resolved Issues

### Documentation Issues
- **Problem**: README.md still described the original single-file version with speech recognition
- **Solution**: Completely rewritten README to reflect the current modular architecture

### Testing Issues
- **Problem**: No automated tests existed
- **Solution**: Created comprehensive test suite covering all core components

### Configuration Issues
- **Problem**: Config.get() and Config.set() did not support dot notation for nested keys
- **Solution**: Enhanced Config class to support dot notation (e.g., "features.file_search")

### LLM Integration Issues
- **Problem**: Ollama LLM integration returned empty responses for certain models (like qwen3:1.7b) due to response content being placed in the 'thinking' field.
- **Solution**: Updated model.py generate() method to check both 'response' and 'thinking' fields, falling back to thinking when response is empty.

## Testing Instructions

To verify the fix for configuration dot notation:

```bash
python -c "
from config import Config
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as tmpdir:
    config_path = Path(tmpdir) / 'test_config.json'
    config = Config(config_path)
    config.set('features.file_search', False)
    assert config.get('features.file_search') == False
    assert config.get('features.note_taking') == True  # Should remain unchanged
    print('Config dot notation test passed!')
"
```

## Next Steps

1. Complete performance benchmarks
2. Prepare for beta release (v0.1.0)
3. Consider additional UI enhancements:
   - Message appearance animations (fade-in/slide-in)
   - Further refinement of gradient effects
   - Additional accessibility features