"""
ui/main_panel.py
================
The main glassmorphism chat window that expands from the floating orb.

Layout (top → bottom)
----------------------
  ┌──────────────────────────────────────────┐
  │  ◉ ARIA · Offline AI Assistant  [—] [✕] │  ← HeaderBar  (draggable)
  ├──────────────────────────────────────────┤
  │  [🕐 Time] [📅 Date] [📋 Todos] …      │  ← QuickActions
  ├──────────────────────────────────────────┤
  │                                          │
  │  < message bubbles (scrollable) >        │  ← ChatArea
  │                                          │
  ├──────────────────────────────────────────┤
  │  [ Message ARIA… ……………………… ] [  ➤  ]  │  ← InputBar
  └──────────────────────────────────────────┘

Public classes
--------------
MainPanel               — the chat window
FloatingAssistantGUI    — top-level coordinator (used by gui.py)
"""

import queue
import threading
import tkinter as tk
from tkinter import messagebox

# System tray imports
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

from .theme          import (COLORS, FONTS, PANEL_W, PANEL_H, PANEL_CORNER,
                              HEADER_H, TRANSPARENT_KEY, WIDGET_W, WIDGET_H)
from .animations     import AnimationEngine
from .widgets        import draw_rounded_rect, draw_glow_rect, GlassButton
from .floating_widget import FloatingWidget
from .chat_area      import ChatArea
from .quick_actions  import QuickActions
from .input_bar      import InputBar


# ---------------------------------------------------------------------------
# HeaderBar
# ---------------------------------------------------------------------------

class _HeaderBar(tk.Frame):
    """
    Custom title-bar for the panel: branding, status, window controls.
    Supports drag-to-move the parent window.
    """

    def __init__(self, parent_window: tk.Toplevel, on_minimize, on_close):
        super().__init__(
            parent_window,
            bg=COLORS['bg_header'],
            height=HEADER_H,
        )
        self.pack_propagate(False)
        self._win        = parent_window
        self._drag_x     = 0
        self._drag_y     = 0

        self._build(on_minimize, on_close)

        # Bind drag on the whole header
        self.bind('<ButtonPress-1>',  self._drag_start)
        self.bind('<B1-Motion>',       self._drag_move)

    # ------------------------------------------------------------------

    def _build(self, on_minimize, on_close) -> None:
        # Bottom border line
        tk.Frame(self, bg=COLORS['border_subtle'], height=1).pack(
            side=tk.BOTTOM, fill=tk.X)

        # Left: orb icon + name
        left = tk.Frame(self, bg=COLORS['bg_header'])
        left.pack(side=tk.LEFT, padx=12, pady=0, fill=tk.Y)

        # Tiny orb dot
        dot_canvas = tk.Canvas(
            left, width=12, height=12,
            bg=COLORS['bg_header'], highlightthickness=0,
        )
        dot_canvas.pack(side=tk.LEFT, padx=(0, 8), pady=18)
        dot_canvas.create_oval(1, 1, 11, 11,
                                fill=COLORS['accent_cyan'], outline='')

        # Name
        tk.Label(
            left,
            text='ARIA',
            font=FONTS['header'],
            bg=COLORS['bg_header'],
            fg=COLORS['text_accent'],
        ).pack(side=tk.LEFT)

        tk.Label(
            left,
            text='  ·  Offline AI',
            font=FONTS['subheader'],
            bg=COLORS['bg_header'],
            fg=COLORS['text_muted'],
        ).pack(side=tk.LEFT)

        # Right: status + window buttons
        right = tk.Frame(self, bg=COLORS['bg_header'])
        right.pack(side=tk.RIGHT, padx=8, fill=tk.Y)

        # Close button
        close_btn = tk.Label(
            right, text='  ✕  ',
            font=FONTS['small_bold'],
            bg=COLORS['bg_header'],
            fg=COLORS['text_secondary'],
            cursor='hand2',
        )
        close_btn.pack(side=tk.RIGHT, pady=16)
        close_btn.bind('<Enter>',    lambda _e: close_btn.config(
            bg=COLORS['btn_close_hover'], fg=COLORS['accent_red']))
        close_btn.bind('<Leave>',    lambda _e: close_btn.config(
            bg=COLORS['bg_header'],      fg=COLORS['text_secondary']))
        close_btn.bind('<Button-1>', lambda _e: on_close())

        # Minimise / hide button
        min_btn = tk.Label(
            right, text='  —  ',
            font=FONTS['small_bold'],
            bg=COLORS['bg_header'],
            fg=COLORS['text_secondary'],
            cursor='hand2',
        )
        min_btn.pack(side=tk.RIGHT, pady=16)
        min_btn.bind('<Enter>',    lambda _e: min_btn.config(
            bg=COLORS['bg_glass_light'], fg=COLORS['accent_cyan']))
        min_btn.bind('<Leave>',    lambda _e: min_btn.config(
            bg=COLORS['bg_header'],      fg=COLORS['text_secondary']))
        min_btn.bind('<Button-1>', lambda _e: on_minimize())

        # Status indicator dot + text
        self._status_dot = tk.Canvas(
            right, width=8, height=8,
            bg=COLORS['bg_header'], highlightthickness=0,
        )
        self._status_dot.pack(side=tk.RIGHT, padx=(0, 4), pady=20)

        self._status_lbl = tk.Label(
            right,
            text='Ready',
            font=FONTS['tiny'],
            bg=COLORS['bg_header'],
            fg=COLORS['status_ready'],
        )
        self._status_lbl.pack(side=tk.RIGHT, padx=(8, 2), pady=0)

        self._update_dot(COLORS['status_ready'])

    def _update_dot(self, color: str) -> None:
        self._status_dot.delete('all')
        self._status_dot.create_oval(1, 1, 7, 7, fill=color, outline='')

    def set_status(self, status: str) -> None:
        """Update status label & dot. status: 'ready'|'busy'|'error'"""
        cfg = {
            'ready':   ('Ready',       COLORS['status_ready']),
            'busy':    ('Thinking…',   COLORS['status_busy']),
            'error':   ('Error',       COLORS['status_error']),
            'offline': ('Offline',     COLORS['status_offline']),
        }
        label, color = cfg.get(status, ('Ready', COLORS['status_ready']))
        self._status_lbl.config(text=label, fg=color)
        self._update_dot(color)

        # Bind drag on children too
        for widget in (self._status_lbl, self._status_dot):
            widget.bind('<ButtonPress-1>', self._drag_start)
            widget.bind('<B1-Motion>',      self._drag_move)

    # ------------------------------------------------------------------
    # Drag (move panel window)
    # ------------------------------------------------------------------

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self._win.winfo_x()
        self._drag_y = event.y_root - self._win.winfo_y()

    def _drag_move(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self._win.geometry(f'+{x}+{y}')


# ---------------------------------------------------------------------------
# MainPanel
# ---------------------------------------------------------------------------

class MainPanel:
    """
    The glassmorphism chat window.

    Parameters
    ----------
    root       : tk.Tk master
    assistant  : OfflineAssistant instance
    engine     : AnimationEngine (shared)
    orb        : FloatingWidget (used to position the panel beside the orb)
    on_close   : callable() — called when user closes the panel
    """

    def __init__(self, root, assistant, engine: AnimationEngine,
                 orb: FloatingWidget, on_close):
        self._root      = root
        self._assistant = assistant
        self._engine    = engine
        self._orb       = orb
        self._on_close  = on_close
        self._queue     = queue.Queue()
        self._last_resp = ''

        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.wm_attributes('-topmost', True)
        self._win.wm_attributes('-alpha', 0.97)
        self._win.configure(bg=COLORS['bg_root'])
        self._win.withdraw()          # start hidden

        self._position_near_orb()
        self._build()
        self._start_queue_poll()

        # Welcome message
        self._chat.add_message(
            'assistant',
            'Hello! I\'m ARIA — your offline AI assistant. '
            'Ask me anything, or use the quick buttons above.',
        )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self._win.geometry(f'{PANEL_W}x{PANEL_H}')

        # Glass background frame (draws the rounded border)
        bg_canvas = tk.Canvas(
            self._win,
            width=PANEL_W, height=PANEL_H,
            bg=COLORS['bg_root'],
            highlightthickness=0,
        )
        bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Outer glow + border
        draw_glow_rect(
            bg_canvas, 2, 2, PANEL_W - 3, PANEL_H - 3,
            radius=PANEL_CORNER,
            glow_color=COLORS['accent_cyan'],
            glow_layers=3,
            base_bg=COLORS['bg_root'],
        )
        draw_rounded_rect(
            bg_canvas, 2, 2, PANEL_W - 3, PANEL_H - 3,
            radius=PANEL_CORNER,
            fill=COLORS['bg_panel'],
            outline=COLORS['border_cyan_glow'],
            width=1,
        )

        # Content container on top of the canvas
        content = tk.Frame(self._win, bg=COLORS['bg_panel'])
        content.place(x=3, y=3,
                      width=PANEL_W - 6,
                      height=PANEL_H - 6)

        # ── Header ───────────────────────────────────────────────────
        self._header = _HeaderBar(
            self._win,
            on_minimize=self._hide,
            on_close=self._close,
        )
        self._header.pack(side=tk.TOP, fill=tk.X)

        # ── Quick actions ─────────────────────────────────────────────
        self._quick = QuickActions(content, on_command=self._on_send)
        self._quick.pack(side=tk.TOP, fill=tk.X)

        # ── Chat area ─────────────────────────────────────────────────
        self._chat = ChatArea(content, self._engine)
        self._chat.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ── Input bar ─────────────────────────────────────────────────
        self._input = InputBar(content, on_send=self._on_send)
        self._input.pack(side=tk.BOTTOM, fill=tk.X)

    def _position_near_orb(self) -> None:
        """Place the panel beside the floating orb."""
        ox, oy  = self._orb.get_position()
        ow, oh  = self._orb.get_size()
        sw      = self._win.winfo_screenwidth()
        sh      = self._win.winfo_screenheight()

        # Try to open to the left of the orb
        x = ox - PANEL_W - 12
        y = oy + oh - PANEL_H

        # Clamp to screen bounds
        x = max(8, min(x, sw - PANEL_W - 8))
        y = max(8, min(y, sh - PANEL_H - 8))

        self._win.geometry(f'{PANEL_W}x{PANEL_H}+{x}+{y}')

    # ------------------------------------------------------------------
    # Show / Hide
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Show the panel with fade-in animation."""
        self._position_near_orb()
        # Start fully transparent
        self._win.wm_attributes('-alpha', 0.0)
        self._win.deiconify()
        self._win.lift()
        # Animate alpha from 0 to 0.97
        self._engine.schedule('fade_in', 16, self._fade_in_step)  # ~60 FPS
        self._fade_in_target = 0.97
        self._fade_in_start = 0.0
        self._fade_in_value = 0.0

    def _fade_in_step(self):
        """Step function for fade-in animation."""
        # Simple linear interpolation for now
        self._fade_in_value += 0.03  # Adjust speed as needed
        if self._fade_in_value >= self._fade_in_target:
            self._fade_in_value = self._fade_in_target
            self._engine.cancel('fade_in')
            # Focus input when animation completes
            self._input.focus_input()
        self._win.wm_attributes('-alpha', self._fade_in_value)

    def hide(self) -> None:
        """Hide the panel with fade-out animation."""
        # Animate alpha from current value to 0
        current_alpha = self._win.wm_attributes('-alpha')
        self._fade_out_start = current_alpha
        self._fade_out_target = 0.0
        self._fade_out_value = current_alpha
        # Animate alpha from current to 0
        self._engine.schedule('fade_out', 16, self._fade_out_step)  # ~60 FPS

    def _fade_out_step(self):
        """Step function for fade-out animation."""
        # Simple linear interpolation for now
        self._fade_out_value -= 0.03  # Adjust speed as needed
        if self._fade_out_value <= self._fade_out_target:
            self._fade_out_value = self._fade_out_target
            self._engine.cancel('fade_out')
            # Actually hide the window when animation completes
            self._win.withdraw()
        self._win.wm_attributes('-alpha', self._fade_out_value)

    def _hide(self) -> None:
        self.hide()
        self._on_close()

    def _close(self) -> None:
        self.hide()
        self._on_close()

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    def _on_send(self, text: str) -> None:
        """Called when user submits a message."""
        if not text.strip():
            return

        # Show user message immediately
        self._chat.add_message('user', text)

        # Disable input + show typing
        self._input.set_enabled(False)
        self._chat.show_typing(True)
        self._set_status('busy')

        # Process in background thread
        threading.Thread(
            target=self._process_in_background,
            args=(text,),
            daemon=True,
        ).start()

    def _process_in_background(self, text: str) -> None:
        try:
            if hasattr(self._assistant, 'submit_command'):
                response = self._assistant.submit_command(text)
            else:
                response = self._assistant.process_command(text)
                self._assistant.add_to_history(text, response)
            response = response or "I did not get a response for that."
            self._last_resp = response
            self._queue.put(('response', response))
        except Exception as exc:
            self._queue.put(('error', str(exc)))

    def _start_queue_poll(self) -> None:
        """Poll the result queue every 100 ms on the main thread."""
        self._engine.schedule('queue_poll', 100, self._poll_queue)

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, data = self._queue.get_nowait()
                self._handle_worker_result(kind, data)
        except queue.Empty:
            pass

    def _handle_worker_result(self, kind: str, data: str) -> None:
        """Apply a worker result without leaving the input disabled."""
        try:
            self._chat.show_typing(False)
            if kind == 'response':
                self._chat.add_message('assistant', data)
                self._set_status('ready')
            elif kind == 'error':
                self._chat.add_message('system', f'Error: {data}')
                self._set_status('error')
        except Exception as exc:
            try:
                self._chat.show_typing(False)
                self._chat.add_message('system', f'UI error while showing response: {exc}')
            except Exception:
                pass
            self._set_status('error')
        finally:
            self._input.set_enabled(True)
            self._input.focus_input()

    def _set_status(self, status: str) -> None:
        """Sync status across header and orb widget."""
        self._header.set_status(status)
        self._orb.set_status(status)

    # ------------------------------------------------------------------

    def get_last_response(self) -> str:
        return self._last_resp

    def destroy(self) -> None:
        self._engine.cancel('queue_poll')
        self._win.destroy()


# ---------------------------------------------------------------------------
# FloatingAssistantGUI  — top-level coordinator
# ---------------------------------------------------------------------------

class FloatingAssistantGUI:
    """
    Top-level coordinator that owns both the floating orb and the main panel.

    Parameters
    ----------
    assistant : OfflineAssistant — the core logic instance

    Usage::

        app = FloatingAssistantGUI(assistant)
        app.run()
    """

    def __init__(self, assistant):
        self._assistant    = assistant
        self._panel_open   = False

        # Hidden master root (keeps the app alive without its own window)
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.title('ARIA — Offline AI Assistant')
        self._root.protocol('WM_DELETE_WINDOW', self._quit)

        # Shared animation engine
        self._engine = AnimationEngine(self._root)

        # Floating orb
        self._orb = FloatingWidget(self._root, on_toggle_panel=self._toggle_panel)

        # Main chat panel (starts hidden)
        self._panel = MainPanel(
            root=self._root,
            assistant=self._assistant,
            engine=self._engine,
            orb=self._orb,
            on_close=self._on_panel_closed,
        )

        # Start reminder callback routing
        if self._assistant.reminders:
            self._assistant.reminders.start_checking(self._on_reminder)

        # System tray setup
        self._tray_icon = None
        if TRAY_AVAILABLE:
            self._setup_system_tray()

    # ------------------------------------------------------------------
    # Panel toggle
    # ------------------------------------------------------------------

    def _toggle_panel(self) -> None:
        if self._panel_open:
            self._panel.hide()
            self._panel_open = False
            self._orb.set_panel_open(False)
        else:
            self._panel.show()
            self._panel_open = True
            self._orb.set_panel_open(True)

    def _on_panel_closed(self) -> None:
        """Called when the panel is closed via its own close button."""
        self._panel_open = False
        self._orb.set_panel_open(False)

    # ------------------------------------------------------------------
    # Reminder callback
    # ------------------------------------------------------------------

    def _on_reminder(self, reminder: dict) -> None:
        """Show reminder in the panel (called from background thread)."""
        msg = f"⏰ Reminder: {reminder['text']}"
        # Route to main thread via root.after
        self._root.after(0, lambda: self._panel._chat.add_message('system', msg))
        if self._assistant.tts:
            try:
                self._assistant.tts.say(msg)
                self._assistant.tts.runAndWait()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # System Tray
    # ------------------------------------------------------------------

    def _setup_system_tray(self):
        """Set up the system tray icon and menu."""
        # Create a simple icon for the system tray
        image = Image.new('RGB', (64, 64), color='black')
        dc = ImageDraw.Draw(image)
        # Draw a simple circle in the center
        dc.ellipse([16, 16, 48, 48], fill='#00d4ff')
        dc.ellipse([20, 20, 44, 44], fill='#050810')

        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem('Show/Hide', self._toggle_window, default=True),
            pystray.MenuItem('Quit', self._quit_app)
        )

        # Create tray icon
        self._tray_icon = pystray.Icon("aria_assistant", image, "ARIA - AI Assistant", menu)

        # Start the tray icon in a separate thread
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _toggle_window(self, icon=None, item=None):
        """Show or hide the main window from tray."""
        if self._panel_open:
            self._panel.hide()
            self._orb.set_panel_open(False)
            self._panel_open = False
        else:
            self._panel.show()
            self._orb.set_panel_open(True)
            self._panel_open = True

    def _quit_app(self, icon=None, item=None):
        """Quit the application from tray."""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self._exit_app()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the Tkinter main loop (blocks until quit)."""
        self._root.mainloop()

    def _exit_app(self) -> None:
        """Actually exit the application (called from tray menu or when tray not available)."""
        if self._assistant.reminders:
            self._assistant.reminders.stop_checking()
        if self._tray_icon:
            self._tray_icon.stop()
        self._engine.cancel_all()
        self._root.quit()
        self._root.destroy()

    def _quit(self) -> None:
        """Handle window close event - hide to tray if available, otherwise exit."""
        if TRAY_AVAILABLE and self._tray_icon:
            # Hide window to tray instead of quitting
            self._panel.hide()
            self._orb.set_panel_open(False)
            self._panel_open = False
        else:
            # No tray available, actually exit
            self._exit_app()
