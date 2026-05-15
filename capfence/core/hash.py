"""Deterministic payload hashing for audit logging.

Canonical JSON → SHA-256. Order-independent, whitespace-independent.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Return SHA-256 hex digest of canonical JSON serialization."""
    def _serialize(obj: Any) -> Any:
        if isinstance(obj, bytes):
            return hashlib.sha256(obj).hexdigest()
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError(f"Non-serializable type: {type(obj).__name__}")
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_serialize
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

