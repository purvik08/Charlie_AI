"""
features.system_info — System information feature for Charlie.

Provides:
- System info (OS, hostname, CPU, memory)
- Battery info (percent, charging status, seconds left)
- Registers commands:
  - 'system.info' → returns system info table
  - 'system.battery' → returns battery status
"""

from typing import Any, Dict, List

from core.base import BaseFeature, Command, CommandResult, FeatureConfig


class SystemInfoFeature(BaseFeature):
    """Feature that provides system information and battery status."""

    @property
    def name(self) -> str:
        return "system_info"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides system information and battery status"

    def initialize(self) -> None:
        """Register commands and emit feature ready event."""
        self.register_command(
            Command(
                name="system.info",
                handler=self._get_system_info,
                description="Show system information",
                aliases=["computer_info"],
            )
        )
        self.register_command(
            Command(
                name="system.battery",
                handler=self._get_battery_info,
                description="Show battery status",
            )
        )
        # Emit feature ready event
        from core.events import get_event_bus, Events
        bus = get_event_bus()
        bus.emit(Events.FEATURE_READY, feature=self.name)

    def shutdown(self) -> None:
        """Clean up resources."""
        pass  # no persistent resources

    def _get_system_info(self) -> CommandResult:
        """Handler for system.info command."""
        try:
            from core.assistant import SystemInfo
            info = SystemInfo.get_system_info()
            if not info:
                return CommandResult.ok("System information not available")
            parts = []
            for k, v in info.items():
                parts.append(f"  {k}: {v}")
            output = "System Information:\n" + "\n".join(parts)
            return CommandResult.ok(output)
        except Exception as exc:
            return CommandResult.fail(str(exc))

    def _get_battery_info(self) -> CommandResult:
        """Handler for system.battery command."""
        try:
            from core.assistant import SystemInfo
            info = SystemInfo.get_battery_info()
            if info:
                output = f"Battery: {info['percent']}% {'charging' if info['power_plugged'] else 'discharging'}"
                return CommandResult.ok(output)
            return CommandResult.ok("Battery information not available")
        except Exception as exc:
            return CommandResult.fail(str(exc))