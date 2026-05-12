"""Plugin System.

Extensibility architecture for ShadowAudit.
Supports plugins for risk evaluators, policy evaluators, capability providers,
audit sinks, and approval providers.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

class PluginRegistry:
    """Central registry for all ShadowAudit plugins."""

    def __init__(self) -> None:
        self.risk_evaluators: dict[str, Any] = {}
        self.policy_evaluators: dict[str, Any] = {}
        self.capability_providers: dict[str, Any] = {}
        self.audit_sinks: dict[str, Any] = {}
        self.approval_providers: dict[str, Any] = {}

    def register_risk_evaluator(self, name: str, evaluator_cls: Any) -> None:
        self.risk_evaluators[name] = evaluator_cls
        logger.info("Registered risk evaluator plugin: %s", name)

    def register_policy_evaluator(self, name: str, evaluator_cls: Any) -> None:
        self.policy_evaluators[name] = evaluator_cls
        logger.info("Registered policy evaluator plugin: %s", name)

    def register_capability_provider(self, name: str, provider_cls: Any) -> None:
        self.capability_providers[name] = provider_cls
        logger.info("Registered capability provider plugin: %s", name)

    def register_audit_sink(self, name: str, sink_cls: Any) -> None:
        self.audit_sinks[name] = sink_cls
        logger.info("Registered audit sink plugin: %s", name)

    def register_approval_provider(self, name: str, provider_cls: Any) -> None:
        self.approval_providers[name] = provider_cls
        logger.info("Registered approval provider plugin: %s", name)


default_registry = PluginRegistry()


def load_plugins() -> None:
    """Discover and load plugins.
    
    In a real implementation, this would use entry points (e.g., via importlib.metadata).
    For now, we just rely on explicit registration.
    """
    pass
