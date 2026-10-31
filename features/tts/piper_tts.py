import logging
import queue
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class PiperConfig:
    executable: str = "piper"
    voice_model: str = ""
    output_device: str = ""
    volume: float = 0.9


class PiperTTS:
    """Offline Piper TTS queue with interrupt support."""

    def __init__(self, config: PiperConfig) -> None:
        self.config = config
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._running = True
        self._current: Optional[subprocess.Popen] = None
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    @property
    def available(self) -> bool:
        return bool(shutil.which(self.config.executable)) and bool(self.config.voice_model)

    def say(self, text: str) -> None:
        if text.strip():
            self._queue.put(text.strip())

    def interrupt(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        if self._current and self._current.poll() is None:
            self._current.terminate()

    def shutdown(self) -> None:
        self._running = False
        self.interrupt()
        self._queue.put("")
        self._thread.join(timeout=1)

    def _worker(self) -> None:
        while self._running:
            text = self._queue.get()
            if not self._running:
                break
            if not text or not self.available:
                continue
            try:
                model_path = Path(self.config.voice_model)
                if not model_path.exists():
                    logger.warning("piper_voice_missing", extra={"voice_model": str(model_path)})
                    continue
                self._current = subprocess.Popen(
                    [self.config.executable, "--model", str(model_path), "--output-raw"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                self._current.communicate(text, timeout=30)
            except Exception as exc:
                logger.warning("piper_tts_failed", extra={"error": str(exc)})

