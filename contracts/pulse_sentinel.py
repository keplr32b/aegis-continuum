# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
PulseSentinel — Aegis Continuum
================================

Continuity primitive: record whether allowlisted HTTPS endpoints still look
alive/OK under GenLayer consensus, with fail-closed reads for other contracts.

Not a one-shot Q&A oracle. Not an escrow.
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
class PulseRecord:
    status: str
    ratio_milli: u256
    ok_count: u256
    total: u256
    manifest_hash: str
    note: str


class PulseSentinel(gl.Contract):
    """
    Lifecycle:
      - owner allowlists hosts
      - anyone calls pulse(urls) with 1..4 allowlisted HTTPS URLs
      - validators fetch pages; comparative consensus on structured pulse JSON
      - deterministic map to ALIVE | DEGRADED | DEAD
      - downstream: is_alive(), latest_pulse(), count()
    """

    owner: Address
    allowed_hosts: TreeMap[str, bool]
    pulses: DynArray[PulseRecord]
    latest: u256
    alive_threshold_milli: u256
    degraded_threshold_milli: u256
    tolerance_milli: u256

    def __init__(
        self,
        alive_threshold_milli: int = 700,
        degraded_threshold_milli: int = 400,
        tolerance_milli: int = 150,
    ):
        require(0 < degraded_threshold_milli <= alive_threshold_milli <= 1000, "bad thresholds")
        require(0 < tolerance_milli <= 500, "tolerance out of range")
        self.owner = gl.message.sender_address
        self.alive_threshold_milli = u256(alive_threshold_milli)
        self.degraded_threshold_milli = u256(degraded_threshold_milli)
        self.tolerance_milli = u256(tolerance_milli)
        self.latest = u256(0)

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
    def pulse(self, urls: str) -> str:
        raw_urls = urls if isinstance(urls, str) else ""
        url_list = [u.strip() for u in raw_urls.split(",") if u.strip()]
        require(1 <= len(url_list) <= 4, "need 1 to 4 comma-separated urls")

        seen = {}
        for u in url_list:
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)
            require(u not in seen, "duplicate url")
            seen[u] = True

        tol = int(self.tolerance_milli)
        alive_th = int(self.alive_threshold_milli)
        deg_th = int(self.degraded_threshold_milli)
        total = len(url_list)
        urls_for_nondet = list(url_list)

        def sense() -> str:
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
                "You are checking service/page LIVENESS across independent HTTPS sources.\n\n"
                "There are " + str(total) + " sources. A source that failed to fetch, is empty, "
                "or clearly shows a major outage / total failure does NOT count as OK.\n"
                "A source that loads with normal operational content counts as OK "
                "(status pages that list incidents but are themselves up still count as OK).\n\n"
                + block
                + "\n\n"
                "Return ONLY strict JSON, no markdown, no prose:\n"
                '{ "ok_count": <int>, "note": "<short phrase>" }'
            )
            raw = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(raw)
            ok_count = int(data.get("ok_count", 0))
            ok_count = max(0, min(total, ok_count))
            note = str(data.get("note", "")).strip()[:120]
            ratio_milli = (ok_count * _MILLI) // total if total > 0 else 0
            if ratio_milli >= alive_th:
                status = "ALIVE"
            elif ratio_milli >= deg_th:
                status = "DEGRADED"
            else:
                status = "DEAD"
            return canonical(
                {
                    "status": status,
                    "ok_count": ok_count,
                    "total": total,
                    "ratio_milli": ratio_milli,
                    "note": note,
                }
            )

        principle = (
            "The two results are EQUIVALENT if and only if: (1) 'status' is identical, "
            "(2) 'total' is identical, (3) 'ok_count' differs by at most 1, "
            "(4) 'ratio_milli' differs by at most " + str(tol) + ". "
            "If status differs or ratios diverge beyond tolerance, they are NOT equivalent."
        )
        agreed = gl.eq_principle.prompt_comparative(sense, principle)
        parsed = json.loads(agreed)

        status = str(parsed["status"]).strip()
        ok_count = int(parsed["ok_count"])
        total_out = int(parsed["total"])
        ratio_milli = int(parsed["ratio_milli"])
        note = str(parsed.get("note", "")).strip()[:120]

        require(total_out == total, "total mismatch")
        require(status in ("ALIVE", "DEGRADED", "DEAD"), "bad status")
        require(0 <= ok_count <= total, "ok_count out of range")

        # Deterministic re-map from ratio (fail-closed consistency)
        if ratio_milli >= alive_th:
            status = "ALIVE"
        elif ratio_milli >= deg_th:
            status = "DEGRADED"
        else:
            status = "DEAD"

        manifest_hash = canonical({"urls": url_list})

        self.pulses.append(
            PulseRecord(
                status=status,
                ratio_milli=u256(ratio_milli),
                ok_count=u256(ok_count),
                total=u256(total_out),
                manifest_hash=manifest_hash,
                note=note,
            )
        )
        self.latest = u256(len(self.pulses) - 1)
        return status

    @gl.public.view
    def count(self) -> u256:
        return u256(len(self.pulses))

    @gl.public.view
    def latest_pulse(self) -> str:
        require(len(self.pulses) > 0, "no pulses yet")
        p = self.pulses[int(self.latest)]
        return canonical(
            {
                "status": p.status,
                "ratio_milli": int(p.ratio_milli),
                "ok_count": int(p.ok_count),
                "total": int(p.total),
                "manifest_hash": p.manifest_hash,
                "note": p.note,
            }
        )

    @gl.public.view
    def is_alive(self) -> bool:
        if len(self.pulses) == 0:
            return False
        return self.pulses[int(self.latest)].status == "ALIVE"

    @gl.public.view
    def is_host_allowed(self, host: str) -> bool:
        h = (host or "").strip().lower()
        return self.allowed_hosts.get(h, False) is True

    @gl.public.view
    def get_owner(self) -> Address:
        return self.owner

    @gl.public.view
    def get_alive_threshold_milli(self) -> u256:
        return self.alive_threshold_milli
