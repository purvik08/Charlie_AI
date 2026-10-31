import json
import tempfile
import os
from pathlib import Path
import sys

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import Config

def test_config_default_values():
    """Test that Config loads with default values when no config file exists"""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"

        # Initialize config with non-existent file
        config = Config(config_file=config_path)

        # Check default values
        assert config.get("tts_rate") == 150
        assert config.get("tts_volume") == 0.9
        assert config.get("llm_model_name") == "qwen3:1.7b"
        assert config.get("llm_base_url") == "http://localhost:11434"
        assert config.get("wake_word") == "assistant"
        assert config.get("memory_limit") == 100

        # Check features
        features = config.get("features")
        assert features["file_search"] == True
        assert features["system_info"] == True
        assert features["note_taking"] == True
        assert features["todo_list"] == True
        assert features["reminders"] == True
        assert features["time_telling"] == True
        assert features["open_apps"] == True
        assert features["play_music"] == True

def test_config_save_and_load():
    """Test that Config can save and load values"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"

        # Create config and modify some values
        config = Config(config_file=config_path)
        config.set("tts_rate", 200)
        config.set("tts_volume", 0.5)
        config.set("llm_model_name", "test_model")

        # Create a new config instance loading the same file
        config2 = Config(config_file=config_path)

        # Check that values were saved and loaded correctly
        assert config2.get("tts_rate") == 200
        assert config2.get("tts_volume") == 0.5
        assert config2.get("llm_model_name") == "test_model"

def test_config_nested_update():
    """Test that nested config values are updated correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"

        config = Config(config_file=config_path)

        # Update a nested feature value
        config.set("features.file_search", False)

        # Reload and check
        config2 = Config(config_file=config_path)
        assert config2.get("features.file_search") == False

        # Other features should remain unchanged
        assert config2.get("features.note_taking") == True

if __name__ == "__main__":
    test_config_default_values()
    test_config_save_and_load()
    test_config_nested_update()
    print("All config tests passed!")