"""
UI Package for the Offline AI Assistant.

Provides the futuristic glassmorphism floating widget interface.
Import `FloatingAssistantGUI` to start the application.
"""

from .main_panel import FloatingAssistantGUI, MainPanel
from .floating_widget import FloatingWidget
from .onboarding import run_first_launch_wizard

__all__ = ['FloatingAssistantGUI', 'MainPanel', 'FloatingWidget', 'run_first_launch_wizard']

