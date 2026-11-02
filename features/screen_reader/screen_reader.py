"""Capture the current display and pass it to Charlie's local OCR engine."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional


class ScreenReader:
    """Capture all visible displays and extract their text with a local OCR adapter.

    The capture is created only after an explicit user request and is stored in
    Charlie's local data directory.  No screen data is sent to a cloud service.
    """

    def __init__(
        self,
        ocr,
        data_dir: str | Path,
        capture: Optional[Callable[[], object]] = None,
        *,
        retain_captures: bool = False,
        max_captures: int = 10,
        retention_days: int = 7,
        mode: str = "primary",
    ) -> None:
        self.ocr = ocr
        self.data_dir = Path(data_dir)
        self.capture = capture or self._capture_screen
        self.retain_captures = retain_captures
        self.max_captures = max(1, max_captures)
        self.retention_days = max(1, retention_days)
        self.mode = mode if mode in {"primary", "all"} else "primary"

    def read_current_screen(self) -> str:
        """Save a screenshot and return OCR text, or a clear local error."""
        if self.ocr is None:
            return "Screen reading is unavailable because OCR is not configured."

        try:
            image = self.capture()
            output_dir = self.data_dir / "screens"
            output_dir.mkdir(parents=True, exist_ok=True)
            self._prune_captures(output_dir)
            screenshot_path = output_dir / (
                f"screen-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.png"
            )
            image.save(screenshot_path, "PNG")
        except Exception as exc:
            return f"Could not capture the current screen: {exc}"

        try:
            result = self.ocr.extract_text(screenshot_path)
        except Exception as exc:
            return f"Screen captured, but OCR failed: {exc}"
        finally:
            if not self.retain_captures:
                screenshot_path.unlink(missing_ok=True)

        saved_note = f"\n\n_Saved locally: {screenshot_path}_" if self.retain_captures else ""
        return f"**Screen text**\n\n{result}{saved_note}"

    def clear_captures(self) -> str:
        """Delete retained screen captures from Charlie's private data directory."""
        output_dir = self.data_dir / "screens"
        if not output_dir.exists():
            return "There are no saved screen captures."
        removed = 0
        for path in output_dir.glob("screen-*.png"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        return f"Cleared {removed} saved screen capture{'s' if removed != 1 else ''}."

    def _prune_captures(self, output_dir: Path) -> None:
        """Bound retained captures by age and count before creating a new one."""
        now = datetime.now()
        captures = sorted(output_dir.glob("screen-*.png"), key=lambda path: path.stat().st_mtime, reverse=True)
        for index, path in enumerate(captures):
            expired = datetime.fromtimestamp(path.stat().st_mtime) < now - timedelta(days=self.retention_days)
            if expired or index >= self.max_captures:
                try:
                    path.unlink()
                except OSError:
                    continue

    def _capture_screen(self):
        """Capture the configured desktop area through Pillow on supported OSes."""
        try:
            from PIL import ImageGrab
        except ImportError as exc:
            raise RuntimeError("Pillow is required for screen capture.") from exc

        try:
            return ImageGrab.grab(all_screens=self.mode == "all")
        except TypeError:
            # Older Pillow versions do not accept ``all_screens``.
            return ImageGrab.grab()
