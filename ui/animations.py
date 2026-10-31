"""
ui/animations.py
================
Animation engine for the UI.

All animations are driven by Tkinter's `after()` scheduler so they run
on the main thread and are safe to call Tkinter methods from.

Usage:
    engine = AnimationEngine(root_tk_widget)
    engine.schedule('my_anim', 50, callback_fn)   # every 50 ms
    engine.cancel('my_anim')
    engine.cancel_all()
"""

import math


class AnimationEngine:
    """
    Lightweight scheduler that manages named, recurring animation callbacks.

    Each animation is identified by a string name.  Scheduling the same name
    twice replaces the previous schedule.
    """

    def __init__(self, root):
        """
        Parameters
        ----------
        root : tk widget
            Any Tkinter widget whose ``after()`` / ``after_cancel()`` methods
            will be used as the timer backend.
        """
        self._root = root
        self._tasks: dict[str, str] = {}  # name → after-id
        self._running = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def schedule(self, name: str, interval_ms: int, callback) -> None:
        """
        Schedule a recurring callback identified by *name*.

        If *name* is already scheduled it is replaced (cancelled first).

        Parameters
        ----------
        name        : unique string key for this animation
        interval_ms : repeat interval in milliseconds
        callback    : callable with no arguments
        """
        self.cancel(name)                     # replace if already running

        def _tick():
            if not self._running:
                return
            if name not in self._tasks:
                return
            try:
                callback()
            except Exception:
                pass                          # never crash the event loop
            if name in self._tasks:
                self._tasks[name] = self._root.after(interval_ms, _tick)

        self._tasks[name] = self._root.after(interval_ms, _tick)

    def cancel(self, name: str) -> None:
        """Cancel the animation with the given *name* (if running)."""
        after_id = self._tasks.pop(name, None)
        if after_id is not None:
            try:
                self._root.after_cancel(after_id)
            except Exception:
                pass

    def cancel_all(self) -> None:
        """Cancel every scheduled animation."""
        self._running = False
        for name in list(self._tasks.keys()):
            self.cancel(name)

    # ------------------------------------------------------------------
    # Utility helpers used by the UI components
    # ------------------------------------------------------------------

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Smooth step easing for *t* in [0, 1]."""
        return t * t * (3 - 2 * t)

    @staticmethod
    def pulse(step: float) -> float:
        """
        Return a pulsing value in [0, 1] given an ever-increasing *step*.

        Typical usage::

            self._step = (self._step + 0.05) % (2 * math.pi)
            intensity  = AnimationEngine.pulse(self._step)
        """
        return (math.sin(step) + 1.0) / 2.0

    @staticmethod
    def bounce(step: float, dot_index: int, n_dots: int = 3) -> float:
        """
        Return a vertical offset (0-1) for a bouncing dot in a typing indicator.

        Parameters
        ----------
        step      : ever-increasing phase value (advance by ~0.15 per frame)
        dot_index : which dot (0-based) to compute for
        n_dots    : total number of dots
        """
        offset = dot_index * (2 * math.pi / n_dots)
        return (math.sin(step + offset) + 1.0) / 2.0

    @staticmethod
    def blend_hex(c1: str, c2: str, ratio: float) -> str:
        """
        Linear blend between two hex colour strings.

        Parameters
        ----------
        c1    : starting colour e.g. ``'#050810'``
        c2    : target colour  e.g. ``'#00d4ff'``
        ratio : 0.0 → full c1, 1.0 → full c2
        """
        try:
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return c1
