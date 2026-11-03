import copy
import math

import pytest

from cce_core import (
    CoherenceLedger,
    calculate_pra,
    calculate_premium,
    calculate_zdav,
    is_risk_alert_triggered,
)


@pytest.mark.parametrize(
    "value,risk,zdav,premium,pra",
    [
        (1_000_000.0, 0.10, 900_000.0, 2700.0, 270.0),
        (50_000.0, 0.50, 25_000.0, 75.0, 7.5),
        (100_000.0, 0.00, 100_000.0, 300.0, 30.0),
        (100_000.0, 1.00, 0.0, 0.0, 0.0),
        (0.0, 0.20, 0.0, 0.0, 0.0),
    ],
)
def test_financial_pipeline(value, risk, zdav, premium, pra):
    actual_zdav = calculate_zdav(value, risk)
    actual_premium = calculate_premium(actual_zdav)
    actual_pra = calculate_pra(actual_premium)
    assert actual_zdav == pytest.approx(zdav, abs=1e-4)
    assert actual_premium == pytest.approx(premium, abs=1e-4)
    assert actual_pra == pytest.approx(pra, abs=1e-4)


@pytest.mark.parametrize("value", [-1, -100.0])
def test_negative_transaction_rejected(value):
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_zdav(value, 0.1)


@pytest.mark.parametrize("risk", [-0.01, 1.01, math.nan, math.inf, -math.inf])
def test_invalid_risk_rejected(risk):
    with pytest.raises(ValueError):
        calculate_zdav(1000, risk)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True])
def test_invalid_transaction_number_rejected(value):
    with pytest.raises(ValueError):
        calculate_zdav(value, 0.1)


@pytest.mark.parametrize("value", [-1, math.nan, math.inf])
def test_invalid_premium_input_rejected(value):
    with pytest.raises(ValueError):
        calculate_premium(value)


@pytest.mark.parametrize("value", [-1, math.nan, math.inf])
def test_invalid_pra_input_rejected(value):
    with pytest.raises(ValueError):
        calculate_pra(value)


@pytest.mark.parametrize(
    "risk,threshold,expected",
    [(0.90, 0.85, True), (0.85, 0.85, True), (0.8499, 0.85, False),
     (0.20, 0.85, False), (0.50, 0.40, True), (0.0, 0.0, True),
     (1.0, 1.0, True)],
)
def test_risk_threshold_boundaries(risk, threshold, expected):
    assert is_risk_alert_triggered(risk, threshold) is expected


@pytest.mark.parametrize("risk,threshold", [(-0.1, 0.85), (1.1, 0.85), (0.5, -0.1), (0.5, 1.1),
                                             (math.nan, 0.85), (0.5, math.inf)])
def test_invalid_threshold_inputs_rejected(risk, threshold):
    with pytest.raises(ValueError):
        is_risk_alert_triggered(risk, threshold)


@pytest.fixture
def ledger():
    return CoherenceLedger()


def record(ledger, source="SENTINEL-01", timestamp="2026-01-01T00:00:00Z"):
    return ledger.record_entry(source, 100000, 300, 30, 0.1, timestamp=timestamp)


def test_genesis_hash_and_valid_chain(ledger):
    first = record(ledger)
    second = record(ledger, "SENTINEL-02")
    assert first["payload"]["prev_hash"] == "0" * 64
    assert second["payload"]["prev_hash"] == first["hash"]
    assert len(first["hash"]) == 64
    assert ledger.verify_integrity()


def test_identical_payloads_produce_identical_hashes():
    a, b = CoherenceLedger(), CoherenceLedger()
    assert record(a) == record(b)


def test_payload_tampering_detected(ledger):
    record(ledger)
    record(ledger, "SENTINEL-02")
    ledger.chain[1]["payload"]["zdav"] = 999999.0
    assert not ledger.verify_integrity()


def test_broken_link_detected(ledger):
    record(ledger)
    record(ledger, "SENTINEL-02")
    ledger.chain[1]["payload"]["prev_hash"] = "f" * 64
    assert not ledger.verify_integrity()


def test_reordering_entries_detected(ledger):
    record(ledger, "A")
    record(ledger, "B")
    ledger.chain.reverse()
    assert not ledger.verify_integrity()


def test_truncation_is_not_detected_without_external_checkpoint(ledger):
    record(ledger, "A")
    record(ledger, "B")
    record(ledger, "C")
    del ledger.chain[-1]
    # Documented limitation: a shortened valid prefix still verifies.
    assert ledger.verify_integrity()


def test_full_chain_rewrite_can_verify_without_external_anchor(ledger):
    record(ledger, "A")
    record(ledger, "B")
    # Simulate an attacker rebuilding the entire chain from altered content.
    rewritten = copy.deepcopy(ledger.chain)
    rewritten[0]["payload"]["zdav"] = 123.0
    rewritten[0]["hash"] = __import__("hashlib").sha256(
        __import__("json").dumps(
            rewritten[0]["payload"], sort_keys=True, separators=(",", ":"),
            allow_nan=False
        ).encode()
    ).hexdigest()
    rewritten[1]["payload"]["prev_hash"] = rewritten[0]["hash"]
    rewritten[1]["hash"] = __import__("hashlib").sha256(
        __import__("json").dumps(
            rewritten[1]["payload"], sort_keys=True, separators=(",", ":"),
            allow_nan=False
        ).encode()
    ).hexdigest()
    rebuilt = CoherenceLedger()
    rebuilt.chain = rewritten
    assert rebuilt.verify_integrity()


@pytest.mark.parametrize("source", ["", "  ", None])
def test_invalid_source_id_rejected(ledger, source):
    with pytest.raises(ValueError):
        ledger.record_entry(source, 1, 1, 1, 0.1, timestamp="2026-01-01T00:00:00Z")
