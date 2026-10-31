"""
FeatureRegistry: discovers, manages, and provides access to features.
"""

import importlib
import logging
import pkgutil
from typing import Any, Dict, List, Optional, Type

from .base import BaseFeature, FeatureConfig
from .events import EventBus, get_event_bus


logger = logging.getLogger(__name__)


class FeatureRegistry:
    """
    Registry for feature discovery and lifecycle management.

    Features can be registered explicitly or discovered from a package.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self.event_bus = event_bus or get_event_bus()
        self._features: Dict[str, BaseFeature] = {}
        self._feature_classes: Dict[str, Type[BaseFeature]] = {}
        self._command_map: Dict[str, BaseFeature] = {}

    def register(self, feature_class: Type[BaseFeature]) -> None:
        """Register a feature class for later instantiation."""
        # Create temporary instance to get name
        temp_config = FeatureConfig()
        temp_instance = feature_class(temp_config, self.event_bus)
        name = temp_instance.name

        if name in self._feature_classes:
            logger.warning("feature_override", extra={"name": name})

        self._feature_classes[name] = feature_class
        logger.debug("feature_class_registered", extra={"name": name})

    def register_instance(self, feature: BaseFeature) -> None:
        """Register an already-initialized feature instance."""
        name = feature.name
        if name in self._features:
            logger.warning("feature_instance_override", extra={"name": name})
        self._features[name] = feature
        self._rebuild_command_map()
        logger.debug("feature_instance_registered", extra={"name": name})

    def create_and_register(self, name: str, config: Optional[FeatureConfig] = None) -> Optional[BaseFeature]:
        """Create and register a feature by registered class name."""
        if name not in self._feature_classes:
            logger.error("feature_class_not_found", extra={"name": name})
            return None

        feature_class = self._feature_classes[name]
        feature_config = config or FeatureConfig()
        feature = feature_class(feature_config, self.event_bus)

        self._features[name] = feature
        self._rebuild_command_map()
        logger.info("feature_created", extra={"name": name})
        return feature

    def get(self, name: str) -> Optional[BaseFeature]:
        """Get a feature instance by name."""
        return self._features.get(name)

    def get_all(self) -> List[BaseFeature]:
        """Get all registered feature instances."""
        return list(self._features.values())

    def get_enabled(self) -> List[BaseFeature]:
        """Get all enabled feature instances."""
        return [f for f in self._features.values() if f.config.enabled]

    def has_feature(self, name: str) -> bool:
        return name in self._features

    def get_command_owner(self, command_name: str) -> Optional[BaseFeature]:
        """Find which feature owns a command."""
        return self._command_map.get(command_name)

    def execute_command(self, command_name: str, *args, **kwargs) -> Optional[Any]:
        """Execute a command by name, finding the owning feature."""
        owner = self.get_command_owner(command_name)
        if not owner:
            return None
        return owner.execute_command(command_name, *args, **kwargs)

    def list_commands(self) -> Dict[str, str]:
        """Return mapping of command_name -> feature_name."""
        return {cmd: feat.name for cmd, feat in self._command_map.items()}

    def initialize_all(self) -> None:
        """Initialize all registered features."""
        for feature in self._features.values():
            if feature.config.enabled and not feature.is_initialized():
                try:
                    feature.initialize()
                    feature._mark_initialized()
                    self.event_bus.emit("feature.ready", feature=feature.name)
                    logger.info("feature_initialized", extra={"name": feature.name})
                except Exception as exc:
                    logger.exception("feature_init_failed", extra={"name": feature.name, "error": str(exc)})

    def shutdown_all(self) -> None:
        """Shutdown all features."""
        for feature in self._features.values():
            if feature.is_initialized():
                try:
                    feature.shutdown()
                    self.event_bus.emit("feature.shutdown", feature=feature.name)
                    logger.info("feature_shutdown", extra={"name": feature.name})
                except Exception as exc:
                    logger.exception("feature_shutdown_failed", extra={"name": feature.name, "error": str(exc)})

    def discover_from_package(self, package_name: str) -> int:
        """
        Discover feature classes from a package.

        Looks for modules with a `Feature` class that inherits from BaseFeature.
        """
        count = 0
        try:
            package = importlib.import_module(package_name)
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                full_name = f"{package_name}.{module_name}"
                try:
                    module = importlib.import_module(full_name)
                    if hasattr(module, "Feature"):
                        feature_class = module.Feature
                        if issubclass(feature_class, BaseFeature) and feature_class is not BaseFeature:
                            self.register(feature_class)
                            count += 1
                except Exception as exc:
                    logger.warning("feature_module_load_failed", extra={"module": full_name, "error": str(exc)})
        except Exception as exc:
            logger.error("package_discovery_failed", extra={"package": package_name, "error": str(exc)})

        return count

    def _rebuild_command_map(self) -> None:
        """Rebuild the command-to-feature mapping."""
        self._command_map.clear()
        for feature in self._features.values():
            for cmd_name in feature.get_commands():
                if cmd_name not in self._command_map:
                    self._command_map[cmd_name] = feature
                else:
                    logger.warning("command_conflict", extra={"command": cmd_name, "feature": feature.name})


# Global registry instance
_registry: Optional[FeatureRegistry] = None


def get_feature_registry() -> FeatureRegistry:
    """Get the global FeatureRegistry instance (singleton)."""
    global _registry
    if _registry is None:
        _registry = FeatureRegistry()
    return _registry


def set_feature_registry(registry: FeatureRegistry) -> None:
    """Set the global FeatureRegistry instance (for testing)."""
    global _registry
    _registry = registry