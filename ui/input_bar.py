"""
ui/input_bar.py
===============
The bottom input bar of the chat panel.

Layout (left → right)
----------------------
  [ text entry field …………………………… ] [  ➤ Send  ]

Features
--------
• GlassEntry with cyan-border focus glow
• Send button (filled cyan) with hover state
• Enter key submits
• Emits the entered text via on_send callback; clears field automatically
• Microphone button placeholder (toggleable)
• Visual "disabled" state while assistant is processing

Public API
----------
    bar = InputBar(parent, on_send=callback)
    bar.set_enabled(True / False)   — enable / disable while processing
    bar.focus_input()               — focus the entry
"""

import tkinter as tk
from .theme   import COLORS, FONTS, INPUT_H
from .widgets import draw_rounded_rect


class InputBar(tk.Frame):
    """
    Styled input bar with text entry + send button.

    Parameters
    ----------
    parent  : parent Tkinter widget
    on_send : callable(text: str) — called with the trimmed input text
    """

    def __init__(self, parent, on_send):
        super().__init__(parent, bg=COLORS['bg_header'], height=INPUT_H)
        self.pack_propagate(False)
        self._on_send  = on_send
        self._enabled  = True
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Top separator line
        tk.Frame(self, bg=COLORS['border_subtle'], height=1).pack(fill=tk.X)

        inner = tk.Frame(self, bg=COLORS['bg_header'])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # ── Entry field ───────────────────────────────────────────────
        entry_frame = tk.Frame(
            inner,
            bg=COLORS['bg_input'],
            highlightthickness=1,
            highlightbackground=COLORS['border_subtle'],
            highlightcolor=COLORS['accent_cyan'],
        )
        entry_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self._entry = tk.Entry(
            entry_frame,
            bg=COLORS['bg_input'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['accent_cyan'],
            relief=tk.FLAT,
            font=FONTS['body'],
            bd=4,
        )
        self._entry.pack(fill=tk.BOTH, expand=True)
        self._entry.insert(0, 'Message Charlie…')
        self._entry.config(fg=COLORS['text_muted'])
        self._placeholder_on = True

        self._entry.bind('<FocusIn>',  self._on_focus_in)
        self._entry.bind('<FocusOut>', self._on_focus_out)
        self._entry.bind('<Return>',   lambda _e: self._submit())

        # Focus glow
        entry_frame.bind('<FocusIn>', lambda _e: entry_frame.config(
            highlightbackground=COLORS['accent_cyan']))
        self._entry.bind('<FocusIn>', lambda _e: entry_frame.config(
            highlightbackground=COLORS['accent_cyan']), add='+')
        self._entry.bind('<FocusOut>', lambda _e: entry_frame.config(
            highlightbackground=COLORS['border_subtle']), add='+')

        # ── Send button ───────────────────────────────────────────────
        self._send_btn = tk.Label(
            inner,
            text='  ➤  ',
            font=FONTS['btn'],
            bg=COLORS['accent_cyan'],
            fg=COLORS['btn_primary_fg'],
            padx=10,
            pady=6,
            cursor='hand2',
            relief=tk.FLAT,
        )
        self._send_btn.pack(side=tk.RIGHT)

        self._send_btn.bind('<Enter>',    self._btn_enter)
        self._send_btn.bind('<Leave>',    self._btn_leave)
        self._send_btn.bind('<Button-1>', lambda _e: self._submit())

    # ------------------------------------------------------------------
    # Placeholder helpers
    # ------------------------------------------------------------------

    def _on_focus_in(self, _event) -> None:
        if self._placeholder_on:
            self._entry.delete(0, tk.END)
            self._entry.config(fg=COLORS['text_primary'])
            self._placeholder_on = False

    def _on_focus_out(self, _event) -> None:
        if not self._entry.get().strip():
            self._entry.delete(0, tk.END)
            self._entry.insert(0, 'Message Charlie…')
            self._entry.config(fg=COLORS['text_muted'])
            self._placeholder_on = True

    # ------------------------------------------------------------------
    # Button hover
    # ------------------------------------------------------------------

    def _btn_enter(self, _event) -> None:
        if self._enabled:
            self._send_btn.config(bg=COLORS['btn_primary_hover'])

    def _btn_leave(self, _event) -> None:
        if self._enabled:
            self._send_btn.config(bg=COLORS['accent_cyan'])

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def _submit(self) -> None:
        if not self._enabled:
            return
        text = '' if self._placeholder_on else self._entry.get().strip()
        if not text:
            return
        # Clear field
        self._entry.delete(0, tk.END)
        self._on_focus_out(None)       # restore placeholder
        # Fire callback
        self._on_send(text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the input while the assistant is processing."""
        self._enabled = enabled
        state = tk.NORMAL if enabled else tk.DISABLED
        self._entry.config(state=state)

        if enabled:
            self._send_btn.config(
                bg=COLORS['accent_cyan'],
                fg=COLORS['btn_primary_fg'],
                cursor='hand2',
                text='  ➤  ',
            )
        else:
            self._send_btn.config(
                bg=COLORS['border_subtle'],
                fg=COLORS['text_muted'],
                cursor='',
                text='  ⋯  ',
            )

    def focus_input(self) -> None:
        """Move keyboard focus into the text entry."""
        self._entry.focus_set()
