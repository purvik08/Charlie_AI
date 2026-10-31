import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    """Handle configuration for the assistant."""

    def __init__(self, config_file: Path = Path("config.json")):
        self.config_file = config_file
        self.config = self.load_config()
        self._load_env_vars()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        default_config = {
            "tts_rate": 150,
            "tts_volume": 0.9,
            "llm_model_name": "qwen3:1.7b",
            "llm_base_url": "http://localhost:11434",
            "wake_word": "assistant",  # kept for compatibility but not used
            "memory_limit": 100,  # number of interactions to remember
            "data_dir": str(Path.home() / "offline_assistant_data"),
            "features": {
                "file_search": True,
                "system_info": True,
                "note_taking": True,
                "todo_list": True,
                "reminders": True,
                "time_telling": True,
                "open_apps": True,
                "play_music": True
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge with default config
                for key, value in default_config.items():
                    if key not in user_config:
                        user_config[key] = value
                    elif isinstance(value, dict) and isinstance(user_config.get(key), dict):
                        user_config[key] = {**value, **user_config[key]}
                return user_config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using default configuration.")
                return default_config
        else:
            # Create directory and default config
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            self.save_config(default_config)
            return default_config

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self.config
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value, supporting dot notation for nested keys."""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save, supporting dot notation for nested keys."""
        keys = key.split('.')
        config = self.config
        try:
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            # Set the value at the target key
            config[keys[-1]] = value
            self.save_config()
        except (KeyError, TypeError):
            # Fallback to setting top-level key if navigation fails
            self.config[key] = value
            self.save_config()

    def _load_env_vars(self) -> None:
        """Load environment variables from .env file if it exists."""
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
            except Exception as e:
                print(f"Warning: Could not load .env file: {e}")