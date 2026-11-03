"""Testable CCE reference core.

This module is a hardened reference implementation for unit/integration testing.
It is not a production financial system or a claim of immutable storage.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any

PREMIUM_RATE = 0.003
PRA_RATE = 0.10
DEFAULT_RISK_THRESHOLD = 0.85
GENESIS_HASH = "0" * 64


def _finite_number(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def calculate_zdav(transaction_value: float, risk_score: float) -> float:
    transaction_value = _finite_number("transaction_value", transaction_value)
    risk_score = _finite_number("risk_score", risk_score)
    if transaction_value < 0:
        raise ValueError("Transaction value cannot be negative.")
    if not 0.0 <= risk_score <= 1.0:
        raise ValueError("Risk score must be between 0.0 and 1.0.")
    return round(transaction_value * (1.0 - risk_score), 4)


def calculate_premium(zdav: float) -> float:
    zdav = _finite_number("zdav", zdav)
    if zdav < 0:
        raise ValueError("ZDAV cannot be negative.")
    return round(zdav * PREMIUM_RATE, 4)


def calculate_pra(premium: float) -> float:
    premium = _finite_number("premium", premium)
    if premium < 0:
        raise ValueError("Premium cannot be negative.")
    return round(premium * PRA_RATE, 4)


def is_risk_alert_triggered(
    risk_score: float, threshold: float = DEFAULT_RISK_THRESHOLD
) -> bool:
    risk_score = _finite_number("risk_score", risk_score)
    threshold = _finite_number("threshold", threshold)
    if not 0.0 <= risk_score <= 1.0:
        raise ValueError("Risk score must be between 0.0 and 1.0.")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Threshold must be between 0.0 and 1.0.")
    return risk_score >= threshold


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


class CoherenceLedger:
    """In-memory SHA-256 hash chain; not durable or inherently immutable."""

    def __init__(self) -> None:
        self.chain: list[dict[str, Any]] = []
        self.prev_hash = GENESIS_HASH

    def record_entry(
        self,
        source_id: str,
        zdav: float,
        premium: float,
        pra: float,
        risk_score: float,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        zdav = _finite_number("zdav", zdav)
        premium = _finite_number("premium", premium)
        pra = _finite_number("pra", pra)
        risk_score = _finite_number("risk_score", risk_score)
        if min(zdav, premium, pra) < 0:
            raise ValueError("zdav, premium, and pra cannot be negative")
        if not 0.0 <= risk_score <= 1.0:
            raise ValueError("Risk score must be between 0.0 and 1.0.")

        # Explicit timestamp injection makes tests reproducible; live calls use UTC.
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if not isinstance(timestamp, str) or not timestamp:
            raise ValueError("timestamp must be a non-empty string")

        payload = {
            "timestamp": timestamp,
            "source_id": source_id,
            "zdav": round(zdav, 4),
            "premium": round(premium, 4),
            "pra": round(pra, 4),
            "risk_score": round(risk_score, 4),
            "prev_hash": self.prev_hash,
        }
        entry_hash = hashlib.sha256(_canonical_json(payload)).hexdigest()
        entry = {"payload": payload, "hash": entry_hash}
        self.chain.append(entry)
        self.prev_hash = entry_hash
        return entry

    def verify_integrity(self) -> bool:
        expected_prev_hash = GENESIS_HASH
        try:
            for entry in self.chain:
                payload = entry["payload"]
                entry_hash = entry["hash"]
                if payload["prev_hash"] != expected_prev_hash:
                    return False
                recalculated = hashlib.sha256(_canonical_json(payload)).hexdigest()
                if not isinstance(entry_hash, str) or recalculated != entry_hash:
                    return False
                expected_prev_hash = entry_hash
        except (KeyError, TypeError, ValueError, AttributeError):
            return False
        return True
