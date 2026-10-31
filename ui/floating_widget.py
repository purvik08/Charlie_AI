"""
ui/floating_widget.py
=====================
The always-on-top draggable orb that lives on the user's desktop.

• Draws itself as a glowing circular icon via Canvas
• Uses the Windows ``-transparentcolor`` trick for a true circular shape
• Pulsing cyan glow animation (driven by AnimationEngine)
• Status dot changes colour: green=ready, yellow=busy, red=error
• Single-click → toggle the main panel
• Click-and-drag → reposition anywhere on screen
"""

import math
import tkinter as tk

from .theme import COLORS, FONTS, TRANSPARENT_KEY, WIDGET_W, WIDGET_H, ORB_RADIUS
from .animations import AnimationEngine


class FloatingWidget:
    """
    Floating orb widget.

    Parameters
    ----------
    root            : tk.Tk root window (hidden master)
    on_toggle_panel : callable() — called when the user clicks the orb
    """

    def __init__(self, root: tk.Tk, on_toggle_panel):
        self._root             = root
        self._on_toggle_panel  = on_toggle_panel
        self._panel_open       = False
        self._status           = 'ready'

        # Animation state
        self._glow_step        = 0.0
        self._drag_start_x     = 0
        self._drag_start_y     = 0
        self._dragging         = False

        self._create_window()
        self._engine = AnimationEngine(self._win)
        self._start_glow()

    # ------------------------------------------------------------------
    # Window creation
    # ------------------------------------------------------------------

    def _create_window(self) -> None:
        """Create the borderless, always-on-top Toplevel."""
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.wm_attributes('-topmost', True)
        self._win.wm_attributes('-alpha',   0.97)
        self._win.configure(bg=TRANSPARENT_KEY)

        # True circular window on Windows via transparent-color key
        try:
            self._win.wm_attributes('-transparentcolor', TRANSPARENT_KEY)
        except tk.TclError:
            pass                           # not supported on all platforms

        # Position: bottom-right corner
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        x  = sw - WIDGET_W - 24
        y  = sh - WIDGET_H - 64
        self._win.geometry(f'{WIDGET_W}x{WIDGET_H}+{x}+{y}')

        # Canvas — fill entire window
        self._canvas = tk.Canvas(
            self._win,
            width=WIDGET_W,
            height=WIDGET_H,
            bg=TRANSPARENT_KEY,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Event bindings
        self._canvas.bind('<ButtonPress-1>',   self._on_press)
        self._canvas.bind('<B1-Motion>',        self._on_drag)
        self._canvas.bind('<ButtonRelease-1>',  self._on_release)
        self._canvas.bind('<Enter>',            self._on_enter)
        self._canvas.bind('<Leave>',            self._on_leave)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, glow_intensity: float = 0.5) -> None:
        """Redraw the orb on each animation frame."""
        self._canvas.delete('all')

        cx = WIDGET_W // 2
        cy = WIDGET_H // 2
        r  = ORB_RADIUS

        # ── Outer glow rings ──────────────────────────────────────────
        glow_src = {
            'ready': COLORS['accent_cyan'],
            'busy':  COLORS['accent_yellow'],
            'error': COLORS['accent_red'],
        }.get(self._status, COLORS['accent_cyan'])

        for i in range(6, 0, -1):
            pad       = i * 3
            ratio     = glow_intensity * (6 - i + 1) / 7.0 * 0.35
            col       = AnimationEngine.blend_hex(TRANSPARENT_KEY, glow_src, ratio)
            self._canvas.create_oval(
                cx - r - pad, cy - r - pad,
                cx + r + pad, cy + r + pad,
                fill=col, outline='', tags='glow',
            )

        # ── Main circle body (layered for depth) ──────────────────────
        layers = [
            (r,     COLORS['orb_bg']),
            (r - 3, COLORS['orb_inner']),
            (r - 6, COLORS['bg_glass']),
        ]
        for lr, lc in layers:
            self._canvas.create_oval(
                cx - lr, cy - lr, cx + lr, cy + lr,
                fill=lc, outline='', tags='body',
            )

        # ── Outer border ring ─────────────────────────────────────────
        ring_col = (COLORS['accent_violet'] if self._panel_open
                    else glow_src)
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill='', outline=ring_col, width=2, tags='ring',
        )

        # ── Inner decorative ring ─────────────────────────────────────
        ir = r - 7
        self._canvas.create_oval(
            cx - ir, cy - ir, cx + ir, cy + ir,
            fill='', outline=COLORS['border_subtle'], width=1, tags='ring',
        )

        # ── Neural network icon ───────────────────────────────────────
        self._draw_ai_icon(cx, cy)

        # ── Status dot (top-right of circle) ─────────────────────────
        dot_col = {
            'ready': COLORS['status_ready'],
            'busy':  COLORS['status_busy'],
            'error': COLORS['status_error'],
        }.get(self._status, COLORS['status_ready'])

        dx = cx + r - 7
        dy = cy - r + 7
        self._canvas.create_oval(
            dx - 5, dy - 5, dx + 5, dy + 5,
            fill=dot_col, outline=COLORS['bg_root'], width=1.5, tags='dot',
        )

    def _draw_ai_icon(self, cx: int, cy: int) -> None:
        """Draw a mini neural-network graphic inside the orb."""
        # Central hub
        self._canvas.create_oval(
            cx - 5, cy - 5, cx + 5, cy + 5,
            fill=COLORS['orb_node'], outline='', tags='icon',
        )

        # Six surrounding nodes at 60° intervals
        spoke_r = 14
        for i in range(6):
            angle = math.radians(i * 60 - 30)
            nx = cx + int(spoke_r * math.cos(angle))
            ny = cy + int(spoke_r * math.sin(angle))

            # Connector line
            self._canvas.create_line(
                cx, cy, nx, ny,
                fill=COLORS['orb_line'], width=1, tags='icon',
            )
            # Outer node
            self._canvas.create_oval(
                nx - 2, ny - 2, nx + 2, ny + 2,
                fill=COLORS['accent_cyan_soft'], outline='', tags='icon',
            )

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _start_glow(self) -> None:
        self._engine.schedule('glow', 50, self._tick_glow)

    def _tick_glow(self) -> None:
        self._glow_step = (self._glow_step + 0.06) % (2 * math.pi)
        intensity       = AnimationEngine.pulse(self._glow_step)
        self._draw(glow_intensity=intensity)

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def _on_press(self, event: tk.Event) -> None:
        self._drag_start_x = event.x_root - self._win.winfo_x()
        self._drag_start_y = event.y_root - self._win.winfo_y()
        self._dragging     = False

    def _on_drag(self, event: tk.Event) -> None:
        self._dragging = True
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self._win.geometry(f'+{x}+{y}')

    def _on_release(self, event: tk.Event) -> None:
        if not self._dragging:
            # It was a clean click, not a drag → toggle panel
            self._panel_open = not self._panel_open
            self._on_toggle_panel()
        self._dragging = False

    def _on_enter(self, _event: tk.Event) -> None:
        self._win.wm_attributes('-alpha', 1.0)

    def _on_leave(self, _event: tk.Event) -> None:
        self._win.wm_attributes('-alpha', 0.97)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, status: str) -> None:
        """
        Update the status indicator.

        Parameters
        ----------
        status : 'ready' | 'busy' | 'error' | 'offline'
        """
        self._status = status

    def set_panel_open(self, is_open: bool) -> None:
        """Keep internal state in sync when the panel is opened/closed externally."""
        self._panel_open = is_open

    def get_position(self) -> tuple[int, int]:
        """Return current (x, y) position of the orb window."""
        return self._win.winfo_x(), self._win.winfo_y()

    def get_size(self) -> tuple[int, int]:
        """Return (width, height) of the orb window."""
        return WIDGET_W, WIDGET_H

    def destroy(self) -> None:
        self._engine.cancel_all()
        self._win.destroy()
