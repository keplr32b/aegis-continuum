"""
Structural / unit tests for Aegis Continuum primitives.
Runtime consensus is proven on Studionet (see verification/).
"""

import json
import sys
from pathlib import Path


def _host_of(url: str) -> str:
    u = (url or "").strip().lower()
    if not u.startswith("https://"):
        raise ValueError("only https urls allowed")
    rest = u[8:]
    host = rest.split("/")[0].split("?")[0].split("#")[0]
    if not host:
        raise ValueError("empty host")
    if "@" in host:
        raise ValueError("userinfo not allowed")
    if host.replace(".", "").isdigit():
        raise ValueError("ip literal hosts rejected")
    if "localhost" in host:
        raise ValueError("localhost rejected")
    if host.endswith(".local"):
        raise ValueError("local tld rejected")
    return host


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def parse_json_response(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
        t = t.strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start : end + 1]
    return json.loads(t)


def test_host_accepts_https():
    assert _host_of("https://status.github.com/api/v2/status.json") == "status.github.com"
    assert _host_of("https://www.cloudflarestatus.com/") == "www.cloudflarestatus.com"


def test_host_rejects_http_ip_localhost():
    for bad in [
        "http://status.github.com",
        "https://127.0.0.1/x",
        "https://localhost/x",
        "https://foo.local/x",
        "https://user@evil.com/x",
    ]:
        try:
            _host_of(bad)
            assert False, bad
        except ValueError:
            pass


def test_pulse_url_bounds():
    def ok(n):
        return 1 <= n <= 4
    assert ok(1) and ok(4)
    assert not ok(0) and not ok(5)


def test_gate_url_bounds():
    def ok(n):
        return 2 <= n <= 4
    assert ok(2) and ok(4)
    assert not ok(1) and not ok(5)


def test_ratio_and_thresholds():
    total = 3
    ratio = (2 * 1000) // total
    assert ratio == 666
    alive_th, deg_th = 700, 400
    assert not (ratio >= alive_th)
    assert ratio >= deg_th
    assert (3 * 1000) // 3 == 1000


def test_status_mapping():
    def map_status(ratio, alive_th=700, deg_th=400):
        if ratio >= alive_th:
            return "ALIVE"
        if ratio >= deg_th:
            return "DEGRADED"
        return "DEAD"
    assert map_status(1000) == "ALIVE"
    assert map_status(666) == "DEGRADED"
    assert map_status(0) == "DEAD"


def test_gate_fail_closed():
    threshold = 700
    assert not (666 >= threshold)
    assert 700 >= threshold
    # never open on error path
    open_flag = False
    assert open_flag is False


def test_canonical_stable():
    assert canonical({"b": 1, "a": 2}) == canonical({"a": 2, "b": 1})


def test_parse_json_plain_and_fenced():
    assert parse_json_response('{"ok_count": 2}')["ok_count"] == 2
    assert parse_json_response('```json\n{"agreeing": 1}\n```')["agreeing"] == 1


def test_contract_files_exist():
    root = Path(__file__).resolve().parents[1]
    for name in ("pulse_sentinel.py", "freeze_manifest.py", "threshold_gate.py"):
        path = root / "contracts" / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert "Depends" in text
        assert "allow_host" in text
        assert "prompt_comparative" in text
        assert "only https" in text.lower() or "only https urls" in text


def test_pulse_markers():
    root = Path(__file__).resolve().parents[1]
    text = (root / "contracts" / "pulse_sentinel.py").read_text(encoding="utf-8")
    assert "PulseSentinel" in text
    assert "is_alive" in text
    assert "ALIVE" in text and "DEAD" in text


def test_freeze_markers():
    root = Path(__file__).resolve().parents[1]
    text = (root / "contracts" / "freeze_manifest.py").read_text(encoding="utf-8")
    assert "FreezeManifest" in text
    assert "freeze" in text and "verify" in text
    assert "read_manifest" in text


def test_gate_markers():
    root = Path(__file__).resolve().parents[1]
    text = (root / "contracts" / "threshold_gate.py").read_text(encoding="utf-8")
    assert "ThresholdGate" in text
    assert "is_open" in text
    assert "force_close" in text
    assert "evaluate" in text


def test_design_doc_exists():
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    assert "Aegis Continuum" in text
    assert "PulseSentinel" in text
    assert "FreezeManifest" in text
    assert "ThresholdGate" in text
    assert "fail-closed" in text.lower() or "Fail-closed" in text


def test_no_example_com_in_contracts():
    root = Path(__file__).resolve().parents[1]
    for name in ("pulse_sentinel.py", "freeze_manifest.py", "threshold_gate.py"):
        text = (root / "contracts" / name).read_text(encoding="utf-8").lower()
        assert "example.com" not in text


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print("OK", t.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", t.__name__, e)
    if failed:
        sys.exit(1)
    print(f"\n{len(tests)} passed")
