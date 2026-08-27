# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
ThresholdGate — Aegis Continuum
===============================

Integration gate: stays CLOSED unless allowlisted HTTPS sources
corroborate a condition above threshold under consensus.

Fail-closed: errors and low ratio never open the gate.
"""

from genlayer import *
import json
from dataclasses import dataclass


try:
    _UserError = gl.vm.UserError
except Exception:
    _UserError = Exception


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise _UserError(msg)


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


def _host_of(url: str) -> str:
    u = (url or "").strip().lower()
    require(u.startswith("https://"), "only https urls allowed")
    rest = u[8:]
    host = rest.split("/")[0].split("?")[0].split("#")[0]
    require(len(host) > 0, "empty host")
    require("@" not in host, "userinfo not allowed")
    require(not host.replace(".", "").isdigit(), "ip literal hosts rejected")
    require("localhost" not in host, "localhost rejected")
    require(not host.endswith(".local"), "local tld rejected")
    return host


_MILLI = 1000


@allow_storage
@dataclass
class GateEval:
    open: bool
    ratio_milli: u256
    agreeing: u256
    total: u256
    question: str
    manifest_hash: str


class ThresholdGate(gl.Contract):
    owner: Address
    allowed_hosts: TreeMap[str, bool]
    threshold_milli: u256
    tolerance_milli: u256
    history: DynArray[GateEval]
    latest: u256
    is_open_flag: bool

    def __init__(self, threshold_milli: int = 700, tolerance_milli: int = 150):
        require(0 < threshold_milli <= 1000, "threshold out of range")
        require(0 < tolerance_milli <= 500, "tolerance out of range")
        self.owner = gl.message.sender_address
        self.threshold_milli = u256(threshold_milli)
        self.tolerance_milli = u256(tolerance_milli)
        self.latest = u256(0)
        self.is_open_flag = False

    @gl.public.write
    def allow_host(self, host: str) -> None:
        require(gl.message.sender_address == self.owner, "only owner")
        h = (host or "").strip().lower()
        require(len(h) > 0, "empty host")
        require("://" not in h, "pass host only, not url")
        require("@" not in h, "userinfo not allowed")
        require(not h.replace(".", "").isdigit(), "ip literal rejected")
        self.allowed_hosts[h] = True

    @gl.public.write
    def disallow_host(self, host: str) -> None:
        require(gl.message.sender_address == self.owner, "only owner")
        h = (host or "").strip().lower()
        if h in self.allowed_hosts:
            self.allowed_hosts[h] = False

    @gl.public.write
    def evaluate(self, question: str, urls: str) -> str:
        q = (question if isinstance(question, str) else "").strip()
        require(len(q) > 0, "empty question")
        require(len(q) <= 400, "question too long")

        raw_urls = urls if isinstance(urls, str) else ""
        url_list = [u.strip() for u in raw_urls.split(",") if u.strip()]
        require(2 <= len(url_list) <= 4, "need 2 to 4 comma-separated urls")

        seen = {}
        for u in url_list:
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)
            require(u not in seen, "duplicate url")
            seen[u] = True

        tol = int(self.tolerance_milli)
        threshold = int(self.threshold_milli)
        total = len(url_list)
        urls_for_nondet = list(url_list)

        def judge() -> str:
            parts = []
            for i, u in enumerate(urls_for_nondet):
                try:
                    content = gl.nondet.web.render(u, mode="text")
                    snippet = (content[:2500] if content else "[EMPTY PAGE]")
                except Exception as e:
                    snippet = ("[FETCH FAILED: " + str(e) + "]")[:240]
                parts.append("SOURCE " + str(i + 1) + " (" + u + "):\n---\n" + snippet + "\n---")
            block = "\n\n".join(parts)
            prompt = (
                "You evaluate whether sources SUPPORT the following condition.\n\n"
                "CONDITION: " + q + "\n\n"
                "There are " + str(total) + " sources. Failed/empty sources do NOT agree.\n\n"
                + block
                + "\n\n"
                "Count how many sources clearly support the condition.\n"
                "Return ONLY strict JSON:\n"
                '{ "agreeing": <int> }'
            )
            raw = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(raw)
            agreeing = int(data.get("agreeing", 0))
            agreeing = max(0, min(total, agreeing))
            ratio_milli = (agreeing * _MILLI) // total
            opened = ratio_milli >= threshold
            return canonical(
                {
                    "agreeing": agreeing,
                    "total": total,
                    "ratio_milli": ratio_milli,
                    "open": opened,
                }
            )

        principle = (
            "EQUIVALENT iff: (1) 'total' identical, (2) 'open' identical, "
            "(3) 'ratio_milli' within " + str(tol) + ", (4) 'agreeing' differs by at most 1. "
            "Otherwise NOT equivalent."
        )
        agreed = gl.eq_principle.prompt_comparative(judge, principle)
        parsed = json.loads(agreed)

        agreeing = int(parsed["agreeing"])
        total_out = int(parsed["total"])
        ratio_milli = int(parsed["ratio_milli"])
        opened = bool(parsed["open"])

        require(total_out == total, "total mismatch")
        # Deterministic threshold enforcement (fail-closed)
        opened = ratio_milli >= threshold

        manifest_hash = canonical({"question": q, "urls": url_list})
        self.history.append(
            GateEval(
                open=opened,
                ratio_milli=u256(ratio_milli),
                agreeing=u256(agreeing),
                total=u256(total_out),
                question=q,
                manifest_hash=manifest_hash,
            )
        )
        self.latest = u256(len(self.history) - 1)
        self.is_open_flag = opened
        return "OPEN" if opened else "CLOSED"

    @gl.public.write
    def force_close(self) -> None:
        require(gl.message.sender_address == self.owner, "only owner")
        self.is_open_flag = False

    @gl.public.view
    def is_open(self) -> bool:
        return self.is_open_flag is True

    @gl.public.view
    def gate_status(self) -> str:
        if len(self.history) == 0:
            return canonical({"open": False, "status": "CLOSED", "reason": "never_evaluated"})
        g = self.history[int(self.latest)]
        return canonical(
            {
                "open": bool(self.is_open_flag),
                "status": "OPEN" if self.is_open_flag else "CLOSED",
                "ratio_milli": int(g.ratio_milli),
                "agreeing": int(g.agreeing),
                "total": int(g.total),
                "question": g.question,
                "manifest_hash": g.manifest_hash,
            }
        )

    @gl.public.view
    def count(self) -> u256:
        return u256(len(self.history))

    @gl.public.view
    def is_host_allowed(self, host: str) -> bool:
        h = (host or "").strip().lower()
        return self.allowed_hosts.get(h, False) is True

    @gl.public.view
    def get_owner(self) -> Address:
        return self.owner

    @gl.public.view
    def get_threshold_milli(self) -> u256:
        return self.threshold_milli
