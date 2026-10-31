#!/usr/bin/env python3
"""
Main assistant class that orchestrates all components.
"""

import os
import json
import threading
import time
import datetime
import subprocess
import webbrowser
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import our modules
from config.config import Config as AppConfig
from core.intent import IntentDetector
from core.memory import RetrievalMemory

# Try to import TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 is not installed. Install with: pip install pyttsx3")


class FileSearch:
    """Offline file search functionality."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def search_files(self, query: str,
                     file_types: Optional[List[str]] = None,
                     max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for files matching query."""
        results = []
        query_lower = query.lower()

        # Walk through data directory
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file_types:
                    if not any(file.endswith(ext) for ext in file_types):
                        continue

                if query_lower in file.lower():
                    file_path = Path(root) / file
                    try:
                        stat = file_path.stat()
                        results.append({
                            "path": str(file_path),
                            "name": file,
                            "size": stat.st_size,
                            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    except OSError:
                        continue

                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        return results[:max_results]

    def _inside_data_dir(self, file_path: str) -> bool:
        """True when the path resolves to a location inside the data directory."""
        try:
            Path(file_path).resolve().relative_to(self.data_dir.resolve())
            return True
        except (ValueError, OSError):
            return False

    def search_in_file(self, file_path: str, query: str) -> List[Dict[str, Any]]:
        """Search for query within a file (only files inside the data directory)."""
        matches = []
        if not self._inside_data_dir(file_path):
            return matches
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if query.lower() in line.lower():
                        matches.append({
                            "line": i,
                            "text": line.strip()
                        })
        except (IOError, UnicodeDecodeError):
            pass
        return matches


class SystemInfo:
    """System information gathering."""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get basic system information."""
        import platform
        import psutil  # Optional, but useful

        info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

        try:
            # Try to get memory info
            info["memory_total"] = psutil.virtual_memory().total
            info["memory_available"] = psutil.virtual_memory().available
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_usage"] = psutil.cpu_percent(interval=0.1)
        except ImportError:
            info["memory_total"] = "unknown"
            info["memory_available"] = "unknown"
            info["cpu_count"] = "unknown"
            info["cpu_usage"] = "unknown"

        return info

    @staticmethod
    def get_battery_info() -> Dict[str, Any]:
        """Get battery information if available."""
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "seconds_left": battery.secsleft
                }
        except (ImportError, AttributeError):
            pass
        return {}


class NoteTaking:
    """Simple note-taking functionality."""

    def __init__(self, data_dir: str):
        self.notes_dir = Path(data_dir) / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def create_note(self, title: str, content: str) -> str:
        """Create a new note."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        if not safe_title:
            safe_title = "note"

        filename = f"{timestamp}_{safe_title}.txt"
        file_path = self.notes_dir / filename
        counter = 2
        while file_path.exists():
            file_path = self.notes_dir / f"{timestamp}_{safe_title}_{counter}.txt"
            counter += 1

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Created: {datetime.datetime.now().isoformat()}\n")
            f.write("-" * 50 + "\n")
            f.write(content)

        return str(file_path)

    def list_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent notes."""
        notes = []
        note_files = sorted(
            self.notes_dir.glob("*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for file_path in note_files[:limit]:
            try:
                stat = file_path.stat()
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    title = lines[0].replace("Title: ", "").strip() if lines else "Unknown"

                notes.append({
                    "path": str(file_path),
                    "title": title,
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except (IOError, IndexError):
                continue

        return notes

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search within notes."""
        results = []
        query_lower = query.lower()

        for file_path in self.notes_dir.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if query_lower in content.lower():
                        stat = file_path.stat()
                        # Extract title
                        lines = content.split('\n')
                        title = lines[0].replace("Title: ", "").strip() if lines else "Unknown"

                        results.append({
                            "path": str(file_path),
                            "title": title,
                            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            except (IOError, UnicodeDecodeError):
                continue

        return results


class TodoList:
    """To-do list management."""

    def __init__(self, data_dir: str):
        self.todo_file = Path(data_dir) / "todo.json"
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        self.todos = self.load_todos()

    def load_todos(self) -> List[Dict[str, Any]]:
        """Load to-do items from file."""
        if self.todo_file.exists():
            try:
                with open(self.todo_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_todos(self) -> None:
        """Save to-do items to file."""
        with open(self.todo_file, 'w') as f:
            json.dump(self.todos, f, indent=2)

    VALID_PRIORITIES = ("low", "medium", "high")

    def add_todo(self, task: str, priority: str = "medium") -> None:
        """Add a new to-do item. Raises ValueError for an unknown priority."""
        priority = str(priority).strip().lower()
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{priority}'. Choose from: {', '.join(self.VALID_PRIORITIES)}")
        new_id = int(time.time() * 1000)
        existing = {t["id"] for t in self.todos}
        while new_id in existing:
            new_id += 1
        todo = {
            "id": new_id,  # millisecond timestamp, made unique
            "task": task,
            "completed": False,
            "priority": priority,  # low, medium, high
            "created": datetime.datetime.now().isoformat(),
            "completed_at": None
        }
        self.todos.append(todo)
        self.save_todos()

    def complete_todo(self, todo_id: int) -> bool:
        """Mark a to-do item as completed."""
        for todo in self.todos:
            if todo["id"] == todo_id:
                if todo["completed"]:
                    return True  # already completed: keep the original completion time
                todo["completed"] = True
                todo["completed_at"] = datetime.datetime.now().isoformat()
                self.save_todos()
                return True
        return False

    def remove_todo(self, todo_id: int) -> bool:
        """Remove a to-do item."""
        for i, todo in enumerate(self.todos):
            if todo["id"] == todo_id:
                del self.todos[i]
                self.save_todos()
                return True
        return False

    def list_todos(self, show_completed: bool = False) -> List[Dict[str, Any]]:
        """List to-do items."""
        if show_completed:
            return self.todos
        return [todo for todo in self.todos if not todo["completed"]]

    def search_todos(self, query: str) -> List[Dict[str, Any]]:
        """Search to-do items."""
        query_lower = query.lower()
        return [
            todo for todo in self.todos
            if query_lower in todo["task"].lower()
        ]


class Reminders:
    """Reminder system."""

    def __init__(self, data_dir: str):
        self.reminder_file = Path(data_dir) / "reminders.json"
        self.reminder_file.parent.mkdir(parents=True, exist_ok=True)
        self.reminders = self.load_reminders()
        self.running = False
        self.thread = None
        self.callback = None
        self.check_interval = 30  # seconds between checks
        self._stop_event = threading.Event()

    def _wait(self, seconds: float) -> None:
        """Sleep that can be interrupted by stop_checking()."""
        self._stop_event.wait(seconds)

    def load_reminders(self) -> List[Dict[str, Any]]:
        """Load reminders from file."""
        if self.reminder_file.exists():
            try:
                with open(self.reminder_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_reminders(self) -> None:
        """Save reminders to file."""
        with open(self.reminder_file, 'w') as f:
            json.dump(self.reminders, f, indent=2)

    def add_reminder(self, text: str, remind_at: datetime.datetime) -> None:
        """Add a new reminder."""
        reminder = {
            "id": int(time.time() * 1000),
            "text": text,
            "remind_at": remind_at.isoformat(),
            "created": datetime.datetime.now().isoformat(),
            "triggered": False
        }
        self.reminders.append(reminder)
        self.save_reminders()

    def schedule_in(self, text: str, minutes: int = 5, hours: int = 0) -> datetime.datetime:
        """Add a reminder due after the given interval. Negative intervals are rejected."""
        if minutes < 0 or hours < 0:
            raise ValueError("Minutes and hours must not be negative.")
        remind_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes, hours=hours)
        self.add_reminder(text, remind_at)
        return remind_at

    def check_reminders(self) -> List[Dict[str, Any]]:
        """Check for triggered reminders."""
        now = datetime.datetime.now()
        triggered = []

        for reminder in self.reminders:
            if reminder.get("triggered"):
                continue

            try:
                remind_at = datetime.datetime.fromisoformat(reminder["remind_at"])
            except (KeyError, TypeError, ValueError):
                continue  # malformed record: skip it, keep checking the others
            if now >= remind_at:
                reminder["triggered"] = True
                triggered.append(reminder)

        if triggered:
            self.save_reminders()

        return triggered

    def start_checking(self, callback=None) -> None:
        """Start background thread to check reminders."""
        if callback is not None:
            self.callback = callback
        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()

    def stop_checking(self) -> None:
        """Stop background reminder checking."""
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)

    def _check_loop(self) -> None:
        """Background loop to check reminders."""
        while self.running:
            try:
                triggered = self.check_reminders()
                for reminder in triggered:
                    if self.callback:
                        self.callback(reminder)
                    else:
                        print(f"Reminder: {reminder['text']}")
            except Exception as exc:  # the checker thread must survive any error
                print(f"Reminder check failed: {exc}")
            self._wait(self.check_interval)


class OfflineAssistant:
    """Main assistant class that orchestrates all components.

    Request flow: empty-input guard -> pending confirmation -> intent detection
    -> keyword rules (strict patterns) -> local language model.
    """

    GREETING_REPLY = "Hello! I am ready. Try a quick action, or ask me to add a task."
    EMPTY_REPLY = "Please type a command or question."
    UNSUPPORTED_REPLY = "That action is not supported in this version."
    YES_WORDS = {"yes", "y", "confirm", "ok", "okay", "sure"}

    # Applications and folders that may be opened (allowlist).
    ALLOWED_APPS = ("chrome", "calculator", "calc", "spotify", "settings", "vs code", "vscode")
    ALLOWED_FOLDERS = ("downloads", "documents", "desktop")

    _TIME_RE = re.compile(
        r"^(?:what(?:'s| is)(?: the)?(?: current)? time(?: is it)?(?: now)?|what time is it(?: now)?"
        r"|current time|tell me the time|time now|time)$")
    _DATE_RE = re.compile(
        r"^(?:what(?:'s| is)(?: the)?(?: today'?s)? date(?: today)?|today'?s date"
        r"|what day is it(?: today)?|date today|date)$")
    _FIND_RE = re.compile(r"^(?:find|search for) files?\s+(.+)$")
    _NOTE_RE = re.compile(r"^(?:take|create|make)(?: a)? note(?:\s+(?:about|titled|called)?\s*(.*))?$")
    _REMIND_RE = re.compile(
        r"^remind me(?: to)?\s+(.+?)(?:\s+in\s+(\d+)\s*(minutes?|mins?|hours?|hrs?))?$")
    _OPEN_RE = re.compile(r"^(?:open|launch|start)\s+(.+)$")

    def __init__(self, config_path: Optional[str] = None, data_dir: Optional[str] = None):
        self.config = AppConfig(Path(config_path)) if config_path else AppConfig()
        self.data_dir = Path(data_dir or self.config.get("data_dir"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.tts = None
        self.file_search = None
        self.system_info = SystemInfo()
        self.note_taking = None
        self.todo_list = None
        self.reminders = None
        self.model_manager = None
        self.memory = None
        self.intent_detector = IntentDetector()
        self.conversation_history: List[Dict[str, str]] = []
        self.memory_limit = self.config.get("memory_limit", 100)
        self._pending_action: Optional[str] = None

        self._initialize_components()

    # ------------------------------------------------------------------ setup
    def _initialize_components(self) -> None:
        """Initialize all components based on configuration."""
        if self.config.get("features.time_telling", True) or \
           self.config.get("features.open_apps", True) or \
           self.config.get("features.play_music", True):
            if TTS_AVAILABLE:
                try:
                    self.tts = pyttsx3.init()
                    self.tts.setProperty('rate', self.config.get("tts_rate", 150))
                    self.tts.setProperty('volume', self.config.get("tts_volume", 0.9))
                    voices = self.tts.getProperty('voices')
                    if voices:
                        self.tts.setProperty('voice', voices[0].id)
                except Exception as e:
                    print(f"Failed to initialize TTS: {e}")
                    self.tts = None
            else:
                print("TTS not available - pyttsx3 not installed")

        try:
            from models.model import ModelManager
            self.model_manager = ModelManager(self.config.config)
            print(f"Discovered models: {list(self.model_manager.models.keys())}")
        except Exception as e:
            print(f"Failed to initialize ModelManager: {e}")

        if self.config.get("features.file_search", True):
            try:
                self.file_search = FileSearch(str(self.data_dir))
            except Exception as e:
                print(f"Failed to initialize FileSearch: {e}")
        if self.config.get("features.note_taking", True):
            try:
                self.note_taking = NoteTaking(str(self.data_dir))
            except Exception as e:
                print(f"Failed to initialize NoteTaking: {e}")
        if self.config.get("features.todo_list", True):
            try:
                self.todo_list = TodoList(str(self.data_dir))
            except Exception as e:
                print(f"Failed to initialize TodoList: {e}")
        if self.config.get("features.reminders", True):
            try:
                self.reminders = Reminders(str(self.data_dir))
                self.reminders.start_checking(self._reminder_callback)
            except Exception as e:
                print(f"Failed to initialize Reminders: {e}")
        if self.config.get("features.memory", True):
            try:
                self.memory = RetrievalMemory(str(self.data_dir / "chat.db"))
            except Exception as e:
                print(f"Failed to initialize RetrievalMemory: {e}")

    def shutdown(self) -> None:
        """Stop background work and release the model."""
        if self.reminders:
            self.reminders.stop_checking()
        if self.model_manager:
            self.model_manager.shutdown()

    def _reminder_callback(self, reminder: Dict[str, Any]) -> None:
        message = f"Reminder: {reminder['text']}"
        print(message)
        if self.tts:
            try:
                self.tts.say(message)
                self.tts.runAndWait()
            except Exception as e:
                print(f"TTS failed: {e}")

    def speak(self, text: str) -> None:
        """Speak text using TTS (does nothing when no engine is available)."""
        if self.tts:
            self.tts.say(text)
            self.tts.runAndWait()

    # --------------------------------------------------------------- history
    def add_to_history(self, user_text: str, assistant_text: str) -> None:
        """Record one exchange in short-term history and in retrieval memory."""
        self.conversation_history.append({"user": user_text, "assistant": assistant_text})
        if len(self.conversation_history) > self.memory_limit:
            del self.conversation_history[:len(self.conversation_history) - self.memory_limit]
        if self.memory:
            try:
                self.memory.add(user_text, assistant_text)
            except Exception as e:
                print(f"Memory write failed: {e}")

    def submit_command(self, text: str) -> str:
        """Entry point for interfaces: process a command and record the exchange."""
        response = self.process_command(text)
        if text and str(text).strip() and response != self.EMPTY_REPLY:
            self.add_to_history(str(text).strip(), response)
        return response

    # ---------------------------------------------------------------- helpers
    def _enabled(self, flag: str) -> bool:
        return bool(self.config.get(f"features.{flag}", True))

    @staticmethod
    def _disabled_message(label: str) -> str:
        return f"The {label} feature is disabled in the configuration."

    @staticmethod
    def _unavailable_message(label: str) -> str:
        return f"The {label} feature is unavailable because it failed to start."

    def _gate(self, flag: str, component, label: str) -> Optional[str]:
        """Return an explanatory message when a feature cannot be used, else None."""
        if not self._enabled(flag):
            return self._disabled_message(label)
        if component is None:
            return self._unavailable_message(label)
        return None

    # ------------------------------------------------------------ application
    def _open_target(self, target: str) -> None:
        """Ask the operating system to open a file, folder or URL."""
        if os.name == 'nt':
            os.startfile(target)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', target])
        else:
            subprocess.Popen(['xdg-open', target])

    def _launch_application(self, app: str) -> str:
        if app not in self.ALLOWED_APPS:
            return "I can only open: " + ", ".join(self.ALLOWED_APPS) + "."
        names = {
            'nt': {"chrome": "chrome", "calculator": "calc", "calc": "calc", "spotify": "spotify",
                   "settings": "ms-settings:", "vs code": "code", "vscode": "code"},
            'mac': {"chrome": "Google Chrome", "calculator": "Calculator", "calc": "Calculator",
                    "spotify": "Spotify", "settings": "System Settings",
                    "vs code": "Visual Studio Code", "vscode": "Visual Studio Code"},
            'posix': {"chrome": "google-chrome", "calculator": "gnome-calculator",
                      "calc": "gnome-calculator", "spotify": "spotify",
                      "settings": "gnome-control-center", "vs code": "code", "vscode": "code"},
        }
        try:
            if os.name == 'nt':
                os.startfile(names['nt'][app])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-a', names['mac'][app]])
            else:
                subprocess.Popen([names['posix'][app]])
            return f"Opening {app}"
        except Exception as e:
            return f"Failed to open {app}: {e}"

    def _open_folder(self, folder: str) -> str:
        if folder not in self.ALLOWED_FOLDERS:
            return "I can only open: " + ", ".join(self.ALLOWED_FOLDERS) + "."
        path = Path.home() / folder.capitalize()
        if not path.exists():
            return f"Folder not found: {path}"
        try:
            self._open_target(str(path))
            return f"Opening {folder}"
        except Exception as e:
            return f"Failed to open {folder}: {e}"

    # ------------------------------------------------- consequential actions
    def _execute_system_action(self, action: str) -> str:
        """Run a confirmed system action (lock, shutdown or restart)."""
        try:
            if action == "lock":
                if os.name == 'nt':
                    subprocess.Popen(['rundll32.exe', 'user32.dll,LockWorkStation'])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['pmset', 'displaysleepnow'])
                else:
                    subprocess.Popen(['loginctl', 'lock-session'])
                return "Locking the computer."
            if os.name == 'nt':
                flag = '/s' if action == "shutdown" else '/r'
                subprocess.Popen(['shutdown', flag, '/t', '60'])
            else:
                flag = '-h' if action == "shutdown" else '-r'
                subprocess.Popen(['shutdown', flag, '+1'])
            return f"The computer will {action} in one minute."
        except Exception as e:
            return f"Failed to {action}: {e}"

    def _request_confirmation(self, action: str) -> str:
        self._pending_action = action
        verb = {"lock": "lock the computer", "shutdown": "shut down the computer",
                "restart": "restart the computer"}[action]
        return f"Do you really want to {verb}? Reply 'yes' to confirm."

    # --------------------------------------------------------- command routing
    def process_command(self, command: str) -> str:
        """Process a text command and return the response."""
        if command is None or not str(command).strip():
            return self.EMPTY_REPLY
        raw = str(command).strip()
        lowered = raw.lower()

        if self._pending_action is not None:
            action, self._pending_action = self._pending_action, None
            if lowered.rstrip("!. ") in self.YES_WORDS:
                return self._execute_system_action(action)
            return "Action cancelled."

        result = self._route_intent(raw, lowered)
        if result is not None:
            return result
        result = self._route_rules(raw, lowered)
        if result is not None:
            return result
        return self._chat(raw)

    def _route_intent(self, raw: str, lowered: str) -> Optional[str]:
        intent = self.intent_detector.detect(lowered)
        name = intent.intent
        if name == "greeting":
            return self.GREETING_REPLY
        if name == "add_todo":
            blocked = self._gate("todo_list", self.todo_list, "to-do list")
            if blocked:
                return blocked
            task = intent.slots.get("task", "")
            if len(raw) == len(lowered):  # keep the user's capitalisation
                task = raw[len(raw) - len(task):] if task else task
            if not task:
                return "Please specify what task to add"
            self.todo_list.add_todo(task)
            return f"Added to-do: {task}"
        if name == "list_todos":
            blocked = self._gate("todo_list", self.todo_list, "to-do list")
            if blocked:
                return blocked
            todos = self.todo_list.list_todos()
            if todos:
                return f"You have {len(todos)} pending tasks: " + ", ".join(t['task'] for t in todos[:5])
            return "Your to-do list is empty"
        if name == "list_notes":
            blocked = self._gate("note_taking", self.note_taking, "note-taking")
            if blocked:
                return blocked
            notes = self.note_taking.list_notes()
            if notes:
                return f"You have {len(notes)} notes. Recent notes: " + ", ".join(n["title"] for n in notes[:5])
            return "You do not have any notes yet"
        if name in ("system_info", "battery"):
            if not self._enabled("system_info"):
                return self._disabled_message("system information")
            if name == "system_info":
                info = self.system_info.get_system_info()
                return f"System: {info['system']} {info['release']} on {info['machine']}"
            battery = self.system_info.get_battery_info()
            if battery:
                return f"Battery is at {battery['percent']}% {'charging' if battery['power_plugged'] else 'discharging'}"
            return "Battery information not available"
        if name == "open_application":
            if not self._enabled("open_apps"):
                return self._disabled_message("application launcher")
            return self._launch_application(intent.slots.get("app", ""))
        if name == "open_folder":
            if not self._enabled("open_apps"):
                return self._disabled_message("application launcher")
            return self._open_folder(intent.slots.get("folder", ""))
        if name in ("volume_up", "mute", "take_screenshot"):
            return self.UNSUPPORTED_REPLY
        if name == "lock_pc":
            return self._request_confirmation("lock")
        if name == "system_power":
            return self._request_confirmation(intent.slots.get("action", "shutdown"))
        return None

    def _route_rules(self, raw: str, lowered: str) -> Optional[str]:
        text = lowered.rstrip("?.! ")
        if self._TIME_RE.match(text):
            if not self._enabled("time_telling"):
                return self._disabled_message("time and date")
            return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}"
        if self._DATE_RE.match(text):
            if not self._enabled("time_telling"):
                return self._disabled_message("time and date")
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}"

        match = self._FIND_RE.match(lowered)
        if match:
            blocked = self._gate("file_search", self.file_search, "file search")
            if blocked:
                return blocked
            query = match.group(1).strip()
            results = self.file_search.search_files(query, max_results=5)
            if results:
                return f"Found {len(results)} files: " + ", ".join(r['name'] for r in results[:3])
            return f"No files found matching '{query}'"

        match = self._NOTE_RE.match(raw.lower())
        if match:
            blocked = self._gate("note_taking", self.note_taking, "note-taking")
            if blocked:
                return blocked
            body = (raw[len(raw) - len(match.group(1)):] if match.group(1) else "").strip()
            stamp = datetime.datetime.now()
            title = body[:40] if body else f"Note {stamp.strftime('%H%M%S')}"
            content = body or f"Note created at {stamp.strftime('%Y-%m-%d %H:%M:%S')}"
            path = self.note_taking.create_note(title, content)
            return f"Note created: {os.path.basename(path)}"

        match = self._REMIND_RE.match(lowered)
        if match:
            blocked = self._gate("reminders", self.reminders, "reminders")
            if blocked:
                return blocked
            what = match.group(1).strip()
            amount = int(match.group(2)) if match.group(2) else 5
            unit = match.group(3) or "minutes"
            minutes = amount * 60 if unit.startswith(("hour", "hr")) else amount
            self.reminders.schedule_in(what, minutes=minutes)
            return f"I'll remind you to '{what}' in {minutes} minutes"
        if text in ("add task", "add a task", "add todo", "add a todo", "new task", "create task", "create a task"):
            blocked = self._gate("todo_list", self.todo_list, "to-do list")
            return blocked or "Please specify what task to add"
        if lowered in ("remind me", "remind me to"):
            return "Please specify what to remind you about"

        if text in ("play music", "play some music"):
            if self._enabled("play_music"):
                return "Music playback feature not implemented in this version"
            return self._disabled_message("music")

        match = self._OPEN_RE.match(lowered)
        if match and len(match.group(1).split()) <= 3:
            if not self._enabled("open_apps"):
                return self._disabled_message("application launcher")
            return self._launch_application(match.group(1).strip())
        return None

    # ------------------------------------------------------------------ chat
    def _chat(self, raw: str) -> str:
        if not self.model_manager:
            return "I'm not sure how to help with that. Try asking about time, date, system info, or to-do list."
        try:
            system = "You are a helpful offline assistant. Keep responses concise and helpful."
            if self.memory:
                try:
                    related = self.memory.retrieve(raw, limit=2)
                except Exception:
                    related = []
                if related:
                    system += " Relevant earlier conversation: " + " | ".join(r["summary"] for r in related)
            messages = [{"role": "system", "content": system}]
            for exchange in self.conversation_history[-3:]:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["assistant"]})
            messages.append({"role": "user", "content": raw})
            return self.model_manager.chat(messages).strip()
        except Exception as e:
            return f"I'm having trouble processing that request: {e}"
