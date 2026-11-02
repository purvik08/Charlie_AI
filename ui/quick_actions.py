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
    ('◷  Time',    'What is the current time?'),
    ('▣  Date',    'What is today\'s date?'),
    ('✓  Todos',   'List todos'),
    ('⌁  System',  'system info'),
    ('⌁  Battery', 'battery status'),
    ('✎  Notes',   'List my notes'),
    ('◉  Read screen', 'Read screen'),
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
        super().__init__(parent, bg=COLORS['bg_header'], height=52)
        self.pack_propagate(False)
        self._on_command = on_command
        self._enabled = True
        self._buttons = []
        self._build()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        # A small label establishes the shortcuts as optional helpers rather
        # than competing with the conversation itself.
        top = tk.Frame(self, bg=COLORS['bg_header'])
        top.pack(fill=tk.X, padx=12, pady=(5, 0))
        tk.Label(
            top, text='QUICK ACTIONS', font=FONTS['tiny'],
            bg=COLORS['bg_header'], fg=COLORS['text_muted'],
        ).pack(side=tk.LEFT)
        tk.Label(
            top, text='One-click tools', font=FONTS['tiny'],
            bg=COLORS['bg_header'], fg=COLORS['text_muted'],
        ).pack(side=tk.RIGHT)

        # Scrollable inner row (in case buttons overflow)
        container = tk.Frame(self, bg=COLORS['bg_header'])
        container.pack(fill=tk.BOTH, expand=True, padx=9, pady=(0, 3))

        for label, command in ACTIONS:
            self._make_button(container, label, command)

    def _make_button(self, parent, label: str, command: str) -> None:
        """Create a single pill-shaped shortcut button."""
        btn = tk.Label(
            parent,
            text=label,
            font=FONTS['quick_btn'],
            bg=COLORS['bg_raised'],
            fg=COLORS['text_secondary'],
            padx=7,
            pady=3,
            cursor='hand2',
            relief=tk.FLAT,
        )
        btn.pack(side=tk.LEFT, padx=2, pady=3)
        self._buttons.append(btn)

        # Hover effect
        def on_enter(_e):
            btn.config(bg=COLORS['bg_glass_light'], fg=COLORS['accent_cyan'])

        def on_leave(_e):
            btn.config(bg=COLORS['bg_raised'],     fg=COLORS['text_secondary'])

        def on_click(_e):
            if self._enabled:
                self._on_command(command)

        btn.bind('<Enter>',    on_enter)
        btn.bind('<Leave>',    on_leave)
        btn.bind('<Button-1>', on_click)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or dim quick actions while the assistant is busy."""
        self._enabled = enabled
        for button in self._buttons:
            button.config(
                bg=COLORS['bg_raised'] if enabled else COLORS['bg_header'],
                fg=COLORS['text_secondary'] if enabled else COLORS['text_muted'],
                cursor='hand2' if enabled else '',
            )
