"""
ui/widgets.py
=============
Reusable, themed Tkinter widget primitives.

Components
----------
draw_rounded_rect   — draw a rounded rectangle on a Canvas
GlassFrame          — Frame with glass-like dark background
GlassButton         — Themed button with hover glow effect
GlassEntry          — Styled single-line text entry
Tooltip             — Lightweight hover tooltip
"""

import tkinter as tk
from .theme import COLORS, FONTS


# ---------------------------------------------------------------------------
# Canvas drawing utilities
# ---------------------------------------------------------------------------

def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float, y1: float,
    x2: float, y2: float,
    radius: int = 10,
    **kwargs,
) -> int:
    """
    Draw a rectangle with rounded corners on *canvas*.

    Returns the Canvas item id of the polygon.

    Extra keyword arguments (fill, outline, width, tags …) are forwarded
    directly to ``canvas.create_polygon``.
    """
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2,     y1,
        x2,     y1 + r,
        x2,     y2 - r,
        x2,     y2,
        x2 - r, y2,
        x1 + r, y2,
        x1,     y2,
        x1,     y2 - r,
        x1,     y1 + r,
        x1,     y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_glow_rect(
    canvas: tk.Canvas,
    x1: float, y1: float,
    x2: float, y2: float,
    radius: int = 10,
    glow_color: str = '#00d4ff',
    glow_layers: int = 4,
    base_bg: str = '#050810',
) -> None:
    """
    Draw concentric rounded rectangles to simulate a glowing border.

    The outermost layer is the most faded; the innermost is the brightest.
    """
    from .animations import AnimationEngine
    for i in range(glow_layers, 0, -1):
        ratio = (glow_layers - i + 1) / (glow_layers + 1)
        col = AnimationEngine.blend_hex(base_bg, glow_color, ratio * 0.25)
        pad = i * 2
        draw_rounded_rect(
            canvas,
            x1 - pad, y1 - pad, x2 + pad, y2 + pad,
            radius=radius + pad,
            fill=col,
            outline='',
        )


def draw_gradient_rect(
    canvas: tk.Canvas,
    x1: float, y1: float,
    x2: float, y2: float,
    color1: str, color2: str,
    vertical: bool = True,
    steps: int = 20,
    **kwargs
) -> None:
    """
    Draw a gradient rectangle on the canvas.

    Parameters
    ----------
    canvas : tk.Canvas
        The canvas to draw on
    x1, y1, x2, y2 : float
        Rectangle coordinates
    color1, color2 : str
        Start and end colors in hex format
    vertical : bool
        If True, gradient goes top to bottom; if False, left to right
    steps : int
        Number of gradient steps (more = smoother but slower)
    **kwargs
        Additional arguments passed to create_rectangle
    """
    if vertical:
        # Vertical gradient: top to bottom
        y_step = (y2 - y1) / steps
        for i in range(steps):
            y_start = y1 + i * y_step
            y_end = y_start + y_step
            # Calculate interpolated color
            ratio = i / (steps - 1) if steps > 1 else 0
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'

            canvas.create_rectangle(
                x1, y_start, x2, y_end,
                fill=color, outline='', **kwargs
            )
    else:
        # Horizontal gradient: left to right
        x_step = (x2 - x1) / steps
        for i in range(steps):
            x_start = x1 + i * x_step
            x_end = x_start + x_step
            # Calculate interpolated color
            ratio = i / (steps - 1) if steps > 1 else 0
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'

            canvas.create_rectangle(
                x_start, y1, x_end, y2,
                fill=color, outline=''
            )


# ---------------------------------------------------------------------------
# GlassFrame
# ---------------------------------------------------------------------------

class GlassFrame(tk.Frame):
    """
    A tk.Frame pre-configured with the glass panel background color.
    Accepts all normal tk.Frame keyword arguments.
    """

    def __init__(self, parent, bg=None, **kwargs):
        bg = bg or COLORS['bg_glass']
        super().__init__(parent, bg=bg, **kwargs)


# ---------------------------------------------------------------------------
# GlassButton
# ---------------------------------------------------------------------------

class GlassButton(tk.Label):
    """
    A custom button built from a Label (allows full background control).

    Supports two styles:
        style='primary'  — filled cyan background
        style='ghost'    — transparent with cyan border and text
        style='icon'     — no border, just text/symbol, hover glow on text
        style='danger'   — red accent for close / destructive actions

    Parameters
    ----------
    parent      : parent Tkinter widget
    text        : button label text
    command     : callable called on click
    style       : 'primary' | 'ghost' | 'icon' | 'danger'
    width       : fixed width in pixels (optional)
    """

    _STYLE_DEFAULTS = {
        'primary': {
            'bg':       COLORS['btn_primary_bg'],
            'fg':       COLORS['btn_primary_fg'],
            'bg_hover': COLORS['btn_primary_hover'],
            'fg_hover': COLORS['btn_primary_fg'],
        },
        'ghost': {
            'bg':       COLORS['btn_ghost_bg'],
            'fg':       COLORS['btn_ghost_fg'],
            'bg_hover': COLORS['btn_ghost_hover'],
            'fg_hover': COLORS['accent_cyan'],
        },
        'icon': {
            'bg':       COLORS['bg_panel'],
            'fg':       COLORS['text_secondary'],
            'bg_hover': COLORS['bg_glass'],
            'fg_hover': COLORS['accent_cyan'],
        },
        'danger': {
            'bg':       COLORS['bg_header'],
            'fg':       COLORS['text_secondary'],
            'bg_hover': COLORS['btn_close_hover'],
            'fg_hover': COLORS['accent_red'],
        },
    }

    def __init__(
        self,
        parent,
        text: str = '',
        command=None,
        style: str = 'ghost',
        font=None,
        padx: int = 12,
        pady: int = 6,
        cursor: str = 'hand2',
        **kwargs,
    ):
        theme = self._STYLE_DEFAULTS.get(style, self._STYLE_DEFAULTS['ghost'])
        self._bg      = theme['bg']
        self._fg      = theme['fg']
        self._bg_h    = theme['bg_hover']
        self._fg_h    = theme['fg_hover']
        self._command = command

        super().__init__(
            parent,
            text=text,
            font=font or FONTS['btn'],
            bg=self._bg,
            fg=self._fg,
            padx=padx,
            pady=pady,
            cursor=cursor,
            **kwargs,
        )

        self.bind('<Enter>',          self._on_enter)
        self.bind('<Leave>',          self._on_leave)
        self.bind('<Button-1>',       self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)

    def _on_enter(self, _event):
        self.config(bg=self._bg_h, fg=self._fg_h)

    def _on_leave(self, _event):
        self.config(bg=self._bg, fg=self._fg)

    def _on_press(self, _event):
        if self._command:
            self._command()

    def _on_release(self, _event):
        pass


# ---------------------------------------------------------------------------
# GlassEntry
# ---------------------------------------------------------------------------

class GlassEntry(tk.Entry):
    """
    Styled single-line text entry with placeholder support.

    The placeholder text is shown in ``COLORS['text_muted']`` when the
    entry is empty and unfocused; it disappears automatically on focus.
    """

    def __init__(
        self,
        parent,
        placeholder: str = '',
        on_submit=None,
        **kwargs,
    ):
        self._placeholder     = placeholder
        self._placeholder_on  = False
        self._on_submit       = on_submit

        defaults = dict(
            bg=COLORS['bg_input'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['accent_cyan'],
            relief=tk.FLAT,
            font=FONTS['body'],
            bd=0,
            highlightthickness=1,
            highlightcolor=COLORS['accent_cyan'],
            highlightbackground=COLORS['border_subtle'],
        )
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        self.bind('<FocusIn>',  self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
        if on_submit:
            self.bind('<Return>', lambda _e: on_submit())

        self._show_placeholder()

    # ------------------------------------------------------------------

    def _show_placeholder(self):
        if not self.get():
            self.insert(0, self._placeholder)
            self.config(fg=COLORS['text_muted'])
            self._placeholder_on = True

    def _hide_placeholder(self):
        if self._placeholder_on:
            self.delete(0, tk.END)
            self.config(fg=COLORS['text_primary'])
            self._placeholder_on = False

    def _on_focus_in(self, _event):
        self._hide_placeholder()

    def _on_focus_out(self, _event):
        self._show_placeholder()

    def get_text(self) -> str:
        """Return entry text, or empty string if showing placeholder."""
        if self._placeholder_on:
            return ''
        return self.get()

    def clear(self):
        """Clear the entry and restore placeholder."""
        self.delete(0, tk.END)
        self._placeholder_on = False
        self._show_placeholder()


# ---------------------------------------------------------------------------
# Tooltip
# ---------------------------------------------------------------------------

class Tooltip:
    """
    Minimal hover tooltip attached to any Tkinter widget.

    Usage::

        Tooltip(widget, 'Helpful hint text')
    """

    def __init__(self, widget, text: str, delay_ms: int = 600):
        self._widget   = widget
        self._text     = text
        self._delay    = delay_ms
        self._win      = None
        self._after_id = None

        widget.bind('<Enter>', self._schedule_show, add='+')
        widget.bind('<Leave>', self._cancel,         add='+')

    def _schedule_show(self, _event):
        self._cancel(None)
        self._after_id = self._widget.after(self._delay, self._show)

    def _show(self):
        if self._win:
            return
        x = self._widget.winfo_rootx() + 10
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4

        self._win = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f'+{x}+{y}')
        tw.wm_attributes('-topmost', True)
        tw.configure(bg=COLORS['bg_glass_light'])

        tk.Label(
            tw,
            text=self._text,
            bg=COLORS['bg_glass_light'],
            fg=COLORS['text_secondary'],
            font=FONTS['tiny'],
            padx=8,
            pady=4,
            relief=tk.FLAT,
        ).pack()

    def _cancel(self, _event):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._win:
            self._win.destroy()
            self._win = None
