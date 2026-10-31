"""
ui/chat_area.py
===============
Scrollable chat display with styled glassmorphism message bubbles.

Features
--------
• User messages  — right-aligned, cyan border bubble
• Assistant msgs  — left-aligned,  green border bubble
• System msgs     — centered,       violet border bubble
• Timestamps      — shown below each bubble
• Typing indicator — animated 3-dot bounce, shown while processing
• Auto-scroll to latest message
• Mouse-wheel scrolling

Public API
----------
    area = ChatArea(parent)
    area.add_message('user',      'Hello!')
    area.add_message('assistant', 'Hi there!')
    area.add_message('system',    'Connected to Ollama.')
    area.show_typing(True)
    area.show_typing(False)
"""

import datetime
import math
import tkinter as tk
from tkinter import font as tkfont

from .theme  import (COLORS, FONTS, MSG_MAX_WIDTH, MSG_PAD_X, MSG_PAD_Y,
                     BUBBLE_CORNER, TYPING_DOTS, TYPING_DOT_R, TYPING_DOT_GAP)
from .animations import AnimationEngine
from .widgets    import draw_rounded_rect, draw_gradient_rect


class _MessageBubble(tk.Frame):
    """
    A single chat message rendered as a styled bubble.

    Parameters
    ----------
    parent     : parent frame (the inner scrollable frame)
    role       : 'user' | 'assistant' | 'system'
    text       : message content
    timestamp  : formatted time string
    """

    _ROLE_CONFIG = {
        'user': {
            'anchor':    'e',
            'bg':        COLORS['bubble_user_bg'],
            'border':    COLORS['bubble_user_border'],
            'fg':        COLORS['text_primary'],
            'label_fg':  COLORS['accent_cyan'],
            'label':     'You',
        },
        'assistant': {
            'anchor':    'w',
            'bg':        COLORS['bubble_asst_bg'],
            'border':    COLORS['bubble_asst_border'],
            'fg':        COLORS['text_primary'],
            'label_fg':  COLORS['accent_green'],
            'label':     'ARIA',
        },
        'system': {
            'anchor':    'center',
            'bg':        COLORS['bubble_sys_bg'],
            'border':    COLORS['bubble_sys_border'],
            'fg':        COLORS['text_secondary'],
            'label_fg':  COLORS['accent_violet_soft'],
            'label':     'System',
        },
    }

    def __init__(self, parent, role: str, text: str, timestamp: str):
        cfg = self._ROLE_CONFIG.get(role, self._ROLE_CONFIG['system'])

        # Outer row frame — controls left/right alignment
        super().__init__(parent, bg=COLORS['bg_panel'])
        self.pack(fill=tk.X, padx=8, pady=3)

        # Inner wrapper to control max width
        wrapper = tk.Frame(self, bg=COLORS['bg_panel'])
        anchor  = cfg['anchor']
        if anchor == 'e':
            wrapper.pack(side=tk.RIGHT)
        elif anchor == 'w':
            wrapper.pack(side=tk.LEFT)
        else:
            wrapper.pack(anchor='center')

        # Canvas for glass bubble with rounded corners
        # We measure text first to size the canvas
        test_lbl = tk.Label(
            wrapper,
            text=text,
            font=FONTS['body'],
            wraplength=MSG_MAX_WIDTH,
            justify=tk.LEFT,
        )
        test_lbl.update_idletasks()
        req_w = min(test_lbl.winfo_reqwidth()  + MSG_PAD_X * 2 + 4, MSG_MAX_WIDTH + MSG_PAD_X * 2)
        req_h = test_lbl.winfo_reqheight()     + MSG_PAD_Y * 2 + 20  # +20 for label row
        test_lbl.destroy()

        bubble_canvas = tk.Canvas(
            wrapper,
            width=req_w,
            height=req_h,
            bg=COLORS['bg_panel'],
            highlightthickness=0,
            bd=0,
        )
        bubble_canvas.pack()

        # Draw gradient background
        # Create a subtle gradient from slightly lighter to the base color
        bg_color = cfg['bg']
        # Make a slightly lighter version for the gradient start
        r = int(bg_color[1:3], 16)
        g = int(bg_color[3:5], 16)
        b = int(bg_color[5:7], 16)
        # Lighten by 15% for gradient start
        r_light = min(255, int(r * 1.15))
        g_light = min(255, int(g * 1.15))
        b_light = min(255, int(b * 1.15))
        bg_light = f'#{r_light:02x}{g_light:02x}{b_light:02x}'

        draw_gradient_rect(
            bubble_canvas,
            1, 1, req_w - 2, req_h - 2,
            color1=bg_light,
            color2=bg_color,
            vertical=True,
        )

        # Draw border on top
        draw_rounded_rect(
            bubble_canvas,
            1, 1, req_w - 2, req_h - 2,
            radius=BUBBLE_CORNER,
            fill='',  # No fill
            outline=cfg['border'],
            width=1,
        )

        # Sender label (top of bubble)
        bubble_canvas.create_text(
            MSG_PAD_X, MSG_PAD_Y // 2 + 6,
            text=cfg['label'],
            font=FONTS['small_bold'],
            fill=cfg['label_fg'],
            anchor='w',
        )

        # Message text
        bubble_canvas.create_text(
            MSG_PAD_X, MSG_PAD_Y + 18,
            text=text,
            font=FONTS['body'],
            fill=cfg['fg'],
            width=MSG_MAX_WIDTH,
            anchor='nw',
        )

        # Timestamp (bottom-right of bubble)
        bubble_canvas.create_text(
            req_w - MSG_PAD_X, req_h - 5,
            text=timestamp,
            font=FONTS['timestamp'],
            fill=COLORS['text_muted'],
            anchor='se',
        )


class _TypingIndicator(tk.Frame):
    """Three bouncing dots shown while the assistant is typing."""

    def __init__(self, parent, engine: AnimationEngine):
        super().__init__(parent, bg=COLORS['bg_panel'])
        self._engine = engine
        self._step   = 0.0
        self._dots   = []

        # Outer bubble frame
        row = tk.Frame(self, bg=COLORS['bg_panel'])
        row.pack(side=tk.LEFT, padx=8, pady=4)

        # Canvas for the bubble + dots
        w = TYPING_DOTS * (TYPING_DOT_R * 2 + TYPING_DOT_GAP) + 24
        h = 36
        self._canvas = tk.Canvas(
            row,
            width=w, height=h,
            bg=COLORS['bg_panel'],
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack()

        # Draw background bubble
        draw_rounded_rect(
            self._canvas,
            1, 1, w - 2, h - 2,
            radius=BUBBLE_CORNER,
            fill=COLORS['bubble_asst_bg'],
            outline=COLORS['bubble_asst_border'],
            width=1,
        )

        # Initial dot positions
        self._draw_dots(0.0)

        # Start animation
        self._engine.schedule('typing', 60, self._tick)

    def _tick(self) -> None:
        self._step = (self._step + 0.18) % (2 * math.pi)
        self._draw_dots(self._step)

    def _draw_dots(self, step: float) -> None:
        self._canvas.delete('dot')
        cx_base = 12
        cy_mid  = 18

        for i in range(TYPING_DOTS):
            bounce   = AnimationEngine.bounce(step, i, TYPING_DOTS)
            offset_y = int(bounce * 6) - 3
            cx       = cx_base + i * (TYPING_DOT_R * 2 + TYPING_DOT_GAP)
            cy       = cy_mid + offset_y

            # Glow behind dot
            self._canvas.create_oval(
                cx - TYPING_DOT_R - 2, cy - TYPING_DOT_R - 2,
                cx + TYPING_DOT_R + 2, cy + TYPING_DOT_R + 2,
                fill=COLORS['accent_cyan_dim'], outline='', tags='dot',
            )
            self._canvas.create_oval(
                cx - TYPING_DOT_R, cy - TYPING_DOT_R,
                cx + TYPING_DOT_R, cy + TYPING_DOT_R,
                fill=COLORS['accent_cyan'], outline='', tags='dot',
            )

    def stop(self) -> None:
        self._engine.cancel('typing')


class ChatArea(tk.Frame):
    """
    Scrollable container that holds all message bubbles.

    Parameters
    ----------
    parent  : parent Tkinter widget
    engine  : AnimationEngine shared with the rest of the UI
    """

    def __init__(self, parent, engine: AnimationEngine):
        super().__init__(parent, bg=COLORS['bg_panel'])
        self._engine   = engine
        self._typing   = None         # _TypingIndicator instance or None

        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Custom styled scrollbar
        style_sb = tk.Frame(self, bg=COLORS['bg_panel'], width=6)
        style_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._scrollbar = tk.Scrollbar(
            style_sb,
            orient='vertical',
            bg=COLORS['scrollbar_bg'],
            troughcolor=COLORS['scrollbar_bg'],
            activebackground=COLORS['scrollbar_thumb_hover'],
            width=6,
            bd=0,
            relief=tk.FLAT,
            elementborderwidth=0,
        )
        self._scrollbar.pack(fill=tk.Y, expand=True)

        self._canvas = tk.Canvas(
            self,
            bg=COLORS['bg_panel'],
            highlightthickness=0,
            bd=0,
            yscrollcommand=self._scrollbar.set,
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.config(command=self._canvas.yview)

        # Inner frame that holds all message bubbles
        self._inner = tk.Frame(self._canvas, bg=COLORS['bg_panel'])
        self._window_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor='nw',
        )

        # Keep canvas width in sync with window width
        self._canvas.bind('<Configure>', self._on_canvas_configure)
        self._inner.bind('<Configure>',  self._on_inner_configure)

        # Mouse-wheel scrolling
        self._canvas.bind('<MouseWheel>',   self._on_mousewheel)
        self._inner.bind('<MouseWheel>',    self._on_mousewheel)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfig(self._window_id, width=event.width)

    def _on_inner_configure(self, _event: tk.Event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_mousewheel(self, event: tk.Event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(self, role: str, text: str) -> None:
        """
        Append a message bubble.

        Parameters
        ----------
        role : 'user' | 'assistant' | 'system'
        text : message content
        """
        timestamp = datetime.datetime.now().strftime('%H:%M')
        _MessageBubble(self._inner, role, text, timestamp)
        self._scroll_to_bottom()

    def show_typing(self, visible: bool) -> None:
        """Show or hide the typing indicator."""
        if visible and self._typing is None:
            self._typing = _TypingIndicator(self._inner, self._engine)
            self._typing.pack(fill=tk.X, anchor='w')
            self._scroll_to_bottom()
        elif not visible and self._typing is not None:
            self._typing.stop()
            self._typing.destroy()
            self._typing = None

    def clear(self) -> None:
        """Remove all messages."""
        self.show_typing(False)
        for child in self._inner.winfo_children():
            child.destroy()

    def _scroll_to_bottom(self) -> None:
        self._inner.update_idletasks()
        self._canvas.yview_moveto(1.0)
