"""Policy-as-code Engine.

YAML-based policy engine supporting capabilities, risk levels, and contextual conditions.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    capability: str
    action: str  # "allow", "deny", "require_approval", "warn"
    conditions: dict[str, Any] = field(default_factory=dict)

    def matches(self, capability: str, context: dict[str, Any], payload: dict[str, Any] | None = None) -> bool:
        if self.capability != capability:
            # Check wildcard match or prefix match if implemented
            if self.capability.endswith(".*"):
                prefix = self.capability[:-2]
                if not capability.startswith(prefix):
                    return False
            else:
                return False

        payload_dict = payload or {}
        # Evaluate conditions
        for k, v in self.conditions.items():
            if k == "amount_gt":
                amount = self._extract_amount(payload_dict)
                if amount is None or amount <= v:
                    return False
            elif k == "amount_lt":
                amount = self._extract_amount(payload_dict)
                if amount is None or amount >= v:
                    return False
            else:
                # Direct context match
                if context.get(k) != v:
                    return False
        return True

    def _extract_amount(self, payload: dict[str, Any]) -> float | None:
        for key in ("amount", "total", "value", "sum", "quantity", "price"):
            val = payload.get(key)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    continue
        return None


class Policy:
    """A loaded and parsed policy."""

    def __init__(self, raw_data: dict[str, Any], policy_id: str = "default") -> None:
        self.id = policy_id
        self.raw_data = raw_data
        self.rules: list[Rule] = []
        self.risk_levels: dict[str, str] = {}
        self._parse()

    def _parse(self) -> None:
        # Parse deny
        for item in self.raw_data.get("deny", []):
            if isinstance(item, dict) and "capability" in item:
                conditions = {k: v for k, v in item.items() if k != "capability"}
                self.rules.append(Rule(capability=item["capability"], action="deny", conditions=conditions))
        
        # Parse require_approval
        for item in self.raw_data.get("require_approval", []):
            if isinstance(item, dict) and "capability" in item:
                conditions = {k: v for k, v in item.items() if k != "capability"}
                self.rules.append(Rule(capability=item["capability"], action="require_approval", conditions=conditions))

        # Parse allow
        for item in self.raw_data.get("allow", []):
            if isinstance(item, dict) and "capability" in item:
                conditions = {k: v for k, v in item.items() if k != "capability"}
                self.rules.append(Rule(capability=item["capability"], action="allow", conditions=conditions))

        # Parse risk_levels
        rl = self.raw_data.get("risk_levels", {})
        for level, config in rl.items():
            if isinstance(config, dict) and "action" in config:
                self.risk_levels[level] = config["action"]

    def merge(self, other: Policy) -> None:
        """Merge another policy into this one (layering)."""
        # other policy takes precedence
        self.rules = other.rules + self.rules
        self.risk_levels.update(other.risk_levels)
        # Deep merge raw_data for audit purposes
        self.raw_data.update(copy.deepcopy(other.raw_data))

    def evaluate(self, capability: str, context: dict[str, Any], payload: dict[str, Any] | None = None) -> str | None:
        """Evaluate rules and return action if matched. Evaluates in order."""
        for rule in self.rules:
            if rule.matches(capability, context, payload):
                return rule.action
        return None

    def evaluate_risk_level(self, risk_level: str) -> str | None:
        """Evaluate action based on risk level."""
        return self.risk_levels.get(risk_level)


class PolicyLoader:
    """Loads and merges YAML policies."""

    def __init__(self, search_paths: list[str | Path] | None = None) -> None:
        self.search_paths = [Path(p) for p in (search_paths or [])]
        self._cache: dict[str, Policy] = {}

    def load(self, path: str | Path) -> Policy:
        path_str = str(path)
        if path_str in self._cache:
            return self._cache[path_str]

        file_path = Path(path)
        if not file_path.is_absolute():
            # Search in search_paths
            for sp in self.search_paths:
                candidate = sp / file_path
                if candidate.exists():
                    file_path = candidate
                    break

        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        policy = Policy(data, policy_id=file_path.stem)
        
        # Check for inheritance/composition (e.g. `extends: "base.yaml"`)
        extends = data.get("extends")
        if extends:
            if isinstance(extends, str):
                extends = [extends]
            
            base_policy = Policy({}, policy_id="merged")
            for base_path in extends:
                parent = self.load(base_path)
                base_policy.merge(parent)
            
            base_policy.merge(policy)
            policy = base_policy
            policy.id = file_path.stem

        self._cache[path_str] = policy
        return policy

