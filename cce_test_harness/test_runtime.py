"""Direct tests of the repository's actual top-level CCE runtime."""
import importlib.machinery, importlib.util, math
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[1] / "CCE"
loader = importlib.machinery.SourceFileLoader("cce_runtime_under_test", str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
CCE = importlib.util.module_from_spec(spec)
loader.exec_module(CCE)

@pytest.fixture(autouse=True)
def clean_ledger():
    CCE.LEDGER.clear()
    yield
    CCE.LEDGER.clear()

@pytest.mark.parametrize("risk,expected", [(0,False),(.8499,False),(.85,True),(.9,True),(1,True)])
def test_actual_runtime_threshold(risk, expected):
    assert CCE.RiskReport("source", risk, 1000).is_alert is expected

@pytest.mark.parametrize("risk", [-.01,1.01,math.nan,math.inf,-math.inf,True])
def test_runtime_rejects_invalid_risk(risk):
    with pytest.raises(ValueError): CCE.RiskReport("source",risk,100)

@pytest.mark.parametrize("value", [-1,math.nan,math.inf,-math.inf,True])
def test_runtime_rejects_invalid_value(value):
    with pytest.raises(ValueError): CCE.RiskReport("source",.2,value)

@pytest.mark.parametrize("source", ["","  ",None])
def test_runtime_rejects_invalid_source(source):
    with pytest.raises(ValueError): CCE.RiskReport(source,.2,100)

def test_runtime_financial_pipeline():
    zdav = CCE.calculate_zdav(1_000_000,.1)
    premium = CCE.calculate_premium(zdav)
    assert (zdav,premium,CCE.calculate_pra(premium)) == (900000.0,2700.0,270.0)

def test_runtime_calculations_reject_invalid_inputs():
    for fn,args in [(CCE.calculate_zdav,(-1,.2)),(CCE.calculate_zdav,(100,math.nan)),
                    (CCE.calculate_premium,(math.inf,)),(CCE.calculate_pra,(-1,))]:
        with pytest.raises(ValueError): fn(*args)

def test_alert_records_local_decision_not_external_block(capsys):
    report = CCE.RiskReport("source-1",.9,100000)
    assert CCE.g_shield_enforce(report) == "Blocked"
    assert report.zdav == 10000.0 and len(CCE.LEDGER) == 2
    output = capsys.readouterr().out
    assert "no external transaction blocking is claimed" in output
    assert "does not override law" in output

def test_stable_path_records_status():
    assert CCE.g_shield_enforce(CCE.RiskReport("source-2",.2,100000)) == "Stable"
    assert len(CCE.LEDGER) == 1
    assert CCE.LEDGER[0]["payload"]["status"] == "STABLE"

def test_runtime_hashes_and_links_entries():
    CCE.ultra_strang_commit({"action":"one"})
    CCE.ultra_strang_commit({"action":"two"})
    assert CCE.LEDGER[0]["hash"] != CCE.LEDGER[1]["hash"]
    assert CCE.LEDGER[0]["payload"]["prev_hash"] == CCE.GENESIS_HASH
    assert CCE.LEDGER[1]["payload"]["prev_hash"] == CCE.LEDGER[0]["hash"]
    assert CCE.verify_ledger()

def test_runtime_detects_payload_tampering():
    CCE.ultra_strang_commit({"action":"one"})
    CCE.LEDGER[0]["payload"]["action"] = "altered"
    assert not CCE.verify_ledger()

def test_runtime_detects_broken_link():
    CCE.ultra_strang_commit({"action":"one"}); CCE.ultra_strang_commit({"action":"two"})
    CCE.LEDGER[1]["payload"]["prev_hash"] = "f"*64
    assert not CCE.verify_ledger()

def test_runtime_prefix_truncation_limit_is_documented():
    CCE.ultra_strang_commit({"action":"one"}); CCE.ultra_strang_commit({"action":"two"})
    del CCE.LEDGER[-1]
    assert CCE.verify_ledger()

def test_scanner_is_explicitly_synthetic(monkeypatch,capsys):
    monkeypatch.setattr(CCE.random,"uniform",lambda a,b:.1)
    monkeypatch.setattr(CCE.random,"random",lambda:.99)
    score,context = CCE.aether_sentinel_scan("HIGH_FREQ_TRADE")
    assert 0 <= score <= 1 and "Synthetic" in context
    assert "SIMULATION ONLY" in capsys.readouterr().out

@pytest.mark.parametrize("count", [-1,1.5,True])
def test_demo_rejects_invalid_count(count):
    with pytest.raises(ValueError): CCE.live_coherence_stream(count)

def test_enforcement_rejects_wrong_object():
    with pytest.raises(ValueError): CCE.g_shield_enforce(object())
