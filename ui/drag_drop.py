"""
ui/drag_drop.py
===============
Drag-and-drop integration for Charlie's chat panel.

Strategy
--------
1. Try to use `tkinterdnd2` (pip install tkinterdnd2) which provides proper
   OS-level drag-and-drop on Windows/macOS/Linux.
2. If tkinterdnd2 is not installed, fall back to a file-picker button so the
   feature is never completely absent.

Drop handling
-------------
When a file is dropped the handler inspects the extension and either:
  • image / scanned PDF    → passes `"ocr <path>"` to the assistant
  • document (PDF, DOCX …) → passes `"parse <path>"` to the assistant
  • anything else          → pastes the raw path into the chat input

Visual feedback
---------------
While a drag is hovering over the window:
  • The chat area shows a semi-transparent overlay with a dashed cyan border
    and a descriptive label ("Drop file to extract text / parse document").
  • On drop the overlay fades out and the appropriate command fires.
"""

import logging
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

from .theme import COLORS, FONTS

logger = logging.getLogger(__name__)

# ── tkinterdnd2 availability check ──────────────────────────────────────────
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
    DND_AVAILABLE = True
    logger.info("tkinterdnd2 is available — native drag-and-drop enabled.")
except ImportError:
    DND_AVAILABLE = False
    DND_FILES = None
    TkinterDnD = None
    logger.info(
        "tkinterdnd2 not installed — drag-and-drop will use file-picker fallback. "
        "Install with: pip install tkinterdnd2"
    )

# ── File-type routing ────────────────────────────────────────────────────────
_IMAGE_EXT  = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
_DOC_EXT    = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".epub", ".md", ".txt", ".text", ".rst",
    ".odt", ".ods", ".odp", ".pages", ".numbers", ".key", ".eml", ".msg",
}


def _route_file(path: Path) -> str:
    """
    Return the chat command string that should be sent for *path*.

    Images / scanned PDFs  → OCR command
    Office / text docs      → parse command
    Everything else         → just the raw path (user can decide)
    """
    ext = path.suffix.lower()
    if ext in _IMAGE_EXT:
        return f"extract text from {path}"
    if ext in _DOC_EXT:
        return f"parse {path}"
    # Unknown type — put the path in the input field for the user to edit
    return str(path)


def _clean_dnd_path(raw: str) -> Optional[Path]:
    """
    Normalise the path string returned by tkinterdnd2.

    tkinterdnd2 wraps paths with braces when they contain spaces:
      {C:/Users/me/my file.pdf}
    Multiple dropped files come as space-separated tokens:
      {file1.pdf} file2.png
    We handle the first file only.
    """
    raw = raw.strip()
    # Extract the first path token
    if raw.startswith('{'):
        # Braced path
        m = re.match(r'^\{([^}]+)\}', raw)
        if m:
            raw = m.group(1)
    else:
        # Unbraced — take everything up to the next brace or end
        raw = raw.split('} ')[0].split(' {')[0].strip()

    path = Path(raw)
    return path if path.exists() else None


# ════════════════════════════════════════════════════════════════════════════
class DropOverlay(tk.Frame):
    """
    A semi-transparent overlay drawn on top of the chat area while a file
    is being dragged over the window.

    Usage::

        overlay = DropOverlay(parent_frame)
        overlay.show()   # when drag enters
        overlay.hide()   # when drag leaves / drops
    """

    _LABEL_LINES = [
        "📂  Drop file here",
        "",
        "🖼  Image / scanned PDF  →  OCR",
        "📄  Document (PDF, DOCX…) →  Parse",
    ]

    def __init__(self, parent: tk.Widget):
        super().__init__(
            parent,
            bg=COLORS.get("bg_drop_overlay", "#030712"),
            highlightthickness=2,
            highlightbackground=COLORS.get("accent_cyan", "#00d4ff"),
            highlightcolor=COLORS.get("accent_cyan", "#00d4ff"),
        )
        self._visible = False
        self._build()

    def _build(self) -> None:
        # Dashed-border canvas
        self._canvas = tk.Canvas(
            self,
            bg=COLORS.get("bg_drop_overlay", "#030712"),
            highlightthickness=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.bind("<Configure>", self._redraw)

    def _redraw(self, _event=None) -> None:
        self._canvas.delete("all")
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 10 or h < 10:
            return

        cyan = COLORS.get("accent_cyan", "#00d4ff")

        # Dashed border rectangle
        r = 12
        self._canvas.create_rectangle(
            r, r, w - r, h - r,
            outline=cyan,
            width=2,
            dash=(8, 6),
        )

        # Icon + labels centred
        for i, line in enumerate(self._LABEL_LINES):
            font = FONTS.get("body_bold", ("Segoe UI", 11, "bold")) if i == 0 else FONTS.get("small", ("Segoe UI", 9))
            color = cyan if i == 0 else COLORS.get("text_secondary", "#8899bb")
            self._canvas.create_text(
                w // 2,
                h // 2 - 30 + i * 20,
                text=line,
                fill=color,
                font=font,
                anchor="center",
            )

    def show(self) -> None:
        if not self._visible:
            self.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.lift()
            self._visible = True
            self._canvas.after(10, self._redraw)

    def hide(self) -> None:
        if self._visible:
            self.place_forget()
            self._visible = False

    @property
    def visible(self) -> bool:
        return self._visible


# ════════════════════════════════════════════════════════════════════════════
class DragDropManager:
    """
    Attaches drag-and-drop behaviour to a Tkinter window and its chat area.

    Parameters
    ----------
    window      : The Toplevel window (must be a TkinterDnD.Tk/Toplevel when
                  DND_AVAILABLE is True, otherwise a plain tk.Toplevel).
    chat_frame  : The Frame widget that contains the chat scrollable area.
                  The drop overlay is placed on top of this frame.
    on_drop     : Callable(command: str) — called with the routed command
                  string after a file is dropped.
    on_pick_path: Callable(path: str) — called with raw path when the user
                  picks a file via the file-picker fallback (no assistant call).
    """

    def __init__(
        self,
        window: tk.Toplevel,
        chat_frame: tk.Widget,
        on_drop: Callable[[str], None],
        on_pick_path: Optional[Callable[[str], None]] = None,
    ):
        self._window     = window
        self._chat_frame = chat_frame
        self._on_drop    = on_drop
        self._on_pick    = on_pick_path
        self._enabled    = True

        # Drop overlay (always created; shown only during drag-hover)
        self._overlay = DropOverlay(chat_frame)

        if DND_AVAILABLE:
            self._register_dnd()
        else:
            logger.debug("DnD unavailable; file-picker fallback only.")

    # ------------------------------------------------------------------ DnD
    def _register_dnd(self) -> None:
        """Register tkinterdnd2 drop handlers on the window."""
        try:
            self._window.drop_target_register(DND_FILES)
            self._window.dnd_bind("<<DropEnter>>", self._on_drag_enter)
            self._window.dnd_bind("<<DropLeave>>", self._on_drag_leave)
            self._window.dnd_bind("<<Drop>>",       self._on_drop_event)
            logger.debug("DnD handlers registered on window.")
        except Exception as exc:
            logger.warning("Could not register DnD handlers: %s", exc)

    def _on_drag_enter(self, event) -> None:
        if not self._enabled:
            return
        self._overlay.show()
        # Pulse the panel border cyan
        try:
            self._window.config(
                highlightthickness=2,
                highlightbackground=COLORS.get("accent_cyan", "#00d4ff"),
            )
        except Exception:
            pass

    def _on_drag_leave(self, event) -> None:
        self._overlay.hide()

    def _on_drop_event(self, event) -> None:
        self._overlay.hide()
        if not self._enabled:
            return
        raw = getattr(event, "data", "")
        path = _clean_dnd_path(raw)
        if path:
            cmd = _route_file(path)
            self._on_drop(cmd)
        else:
            logger.warning("Dropped path could not be resolved: %r", raw)

    # ------------------------------------------------------------------ picker
    def open_file_picker(self) -> None:
        """Open a native file dialog and route the chosen file."""
        if not self._enabled:
            return
        filetypes = [
            ("All supported files",
             " ".join(f"*{e}" for e in sorted(_IMAGE_EXT | _DOC_EXT))),
            ("Images",        " ".join(f"*{e}" for e in sorted(_IMAGE_EXT))),
            ("Documents",     " ".join(f"*{e}" for e in sorted(_DOC_EXT))),
            ("All files",     "*.*"),
        ]
        path_str = filedialog.askopenfilename(
            parent=self._window,
            title="Attach file to Charlie",
            filetypes=filetypes,
        )
        if not path_str:
            return
        path = Path(path_str)
        cmd = _route_file(path)
        self._on_drop(cmd)

    # ------------------------------------------------------------------ info
    @property
    def native_dnd(self) -> bool:
        return DND_AVAILABLE

    def set_enabled(self, enabled: bool) -> None:
        """Prevent drops and file-picking while an assistant request is active."""
        self._enabled = enabled
        if not enabled:
            self._overlay.hide()
