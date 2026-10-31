"""
ui/quick_actions.py
===================
A horizontal row of shortcut buttons that send preset commands to the
assistant with a single click.

Public API
----------
    qa = QuickActions(parent, on_command_callback)
    # on_command_callback(command_text: str) is called with the preset text

Add or edit the ACTIONS list below to customise which shortcuts appear.
"""

import tkinter as tk
from .theme   import COLORS, FONTS
from .widgets import draw_rounded_rect


# ---------------------------------------------------------------------------
# Preset shortcuts — edit freely
# ---------------------------------------------------------------------------
ACTIONS = [
    ('Time',    'What is the current time?'),
    ('Date',    'What is today\'s date?'),
    ('Todos',   'List todos'),
    ('System',  'system info'),
    ('Battery', 'battery status'),
    ('Notes',   'List my notes'),
]


class QuickActions(tk.Frame):
    """
    Horizontal strip of pill-shaped quick-action buttons.

    Parameters
    ----------
    parent      : parent Tkinter widget
    on_command  : callable(str) — receives the preset command text on click
    """

    def __init__(self, parent, on_command):
        super().__init__(parent, bg=COLORS['bg_header'], height=44)
        self.pack_propagate(False)
        self._on_command = on_command
        self._build()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Subtle top border
        separator = tk.Frame(self, bg=COLORS['border_subtle'], height=1)
        separator.pack(fill=tk.X, side=tk.TOP)

        # Scrollable inner row (in case buttons overflow)
        container = tk.Frame(self, bg=COLORS['bg_header'])
        container.pack(fill=tk.BOTH, expand=True, padx=6)

        for label, command in ACTIONS:
            self._make_button(container, label, command)

    def _make_button(self, parent, label: str, command: str) -> None:
        """Create a single pill-shaped shortcut button."""
        btn = tk.Label(
            parent,
            text=label,
            font=FONTS['quick_btn'],
            bg=COLORS['bg_glass'],
            fg=COLORS['text_secondary'],
            padx=8,
            pady=3,
            cursor='hand2',
            relief=tk.FLAT,
        )
        btn.pack(side=tk.LEFT, padx=3, pady=8)

        # Hover effect
        def on_enter(_e):
            btn.config(bg=COLORS['bg_glass_light'], fg=COLORS['accent_cyan'])

        def on_leave(_e):
            btn.config(bg=COLORS['bg_glass'],      fg=COLORS['text_secondary'])

        def on_click(_e):
            self._on_command(command)

        btn.bind('<Enter>',    on_enter)
        btn.bind('<Leave>',    on_leave)
        btn.bind('<Button-1>', on_click)
