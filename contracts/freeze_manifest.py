# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
FreezeManifest — Aegis Continuum
================================
Deterministic seal of URL manifest.
Verify: comparative consensus on matched bool vs live fetch + sealed URLs.
"""

from genlayer import *
import json


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


class FreezeManifest(gl.Contract):
    owner: Address
    allowed_hosts: TreeMap[str, bool]
    sealed: bool
    urls_csv: str
    urls_hash: str
    sources_count: u256
    verified: bool
    last_matched: bool
    last_note: str

    def __init__(self):
        self.owner = gl.message.sender_address
        self.sealed = False
        self.urls_csv = ""
        self.urls_hash = ""
        self.sources_count = u256(0)
        self.verified = False
        self.last_matched = False
        self.last_note = ""

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
    def freeze(self, urls: str) -> str:
        """Deterministic seal — no LLM. Avoids Undetermined on free-form digests."""
        require(not self.sealed, "already sealed")
        raw = urls if isinstance(urls, str) else ""
        url_list = [u.strip() for u in raw.split(",") if u.strip()]
        require(1 <= len(url_list) <= 4, "need 1 to 4 comma-separated urls")
        seen = {}
        for u in url_list:
            require(u not in seen, "duplicate url")
            seen[u] = True
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)

        self.urls_csv = ",".join(url_list)
        self.urls_hash = canonical({"urls": url_list})
        self.sources_count = u256(len(url_list))
        self.sealed = True
        return self.urls_hash

    @gl.public.write
    def verify(self, urls: str) -> str:
        """Consensus on matched bool; enforce sealed URL manifest."""
        require(self.sealed, "not sealed")
        raw = urls if isinstance(urls, str) else ""
        url_list = [u.strip() for u in raw.split(",") if u.strip()]
        require(1 <= len(url_list) <= 4, "need 1 to 4 urls")
        for u in url_list:
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)
        require(",".join(url_list) == self.urls_csv, "url manifest mismatch")
        require(canonical({"urls": url_list}) == self.urls_hash, "url hash mismatch")

        total = len(url_list)
        urls_for_nondet = list(url_list)
        sealed_csv = self.urls_csv

        def judge() -> str:
            parts = []
            ok = 0
            for i, u in enumerate(urls_for_nondet):
                try:
                    content = gl.nondet.web.render(u, mode="text")
                    snippet = (content[:3000] if content else "")
                    if snippet.strip():
                        ok += 1
                    else:
                        snippet = "[EMPTY PAGE]"
                except Exception as e:
                    snippet = ("[FETCH FAILED: " + str(e) + "]")[:240]
                parts.append("SOURCE " + str(i + 1) + " (" + u + "):\n---\n" + snippet + "\n---")
            block = "\n\n".join(parts)
            prompt = (
                "Integrity check against a SEALED URL manifest.\n"
                "SEALED URLS: " + sealed_csv + "\n\n"
                + block
                + "\n\n"
                "matched=true only if every sealed source fetches non-empty main content "
                "and still looks like the same site/docs identity (ignore ads/timestamps).\n"
                "matched=false if fetch fails, empty, or clearly different/broken content.\n"
                "Return ONLY strict JSON:\n"
                '{ "matched": true or false, "note": "<short reason>" }'
            )
            rawp = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(rawp)
            matched = bool(data.get("matched", False))
            if ok == 0:
                matched = False
            note = str(data.get("note", "")).strip()[:120]
            return canonical({"matched": matched, "note": note, "sources_count": total})

        principle = (
            "EQUIVALENT iff: (1) matched is identical, (2) sources_count is identical. "
            "note may differ. If matched differs => NOT equivalent."
        )
        agreed = gl.eq_principle.prompt_comparative(judge, principle)
        parsed = json.loads(agreed)
        matched = bool(parsed["matched"])
        note = str(parsed.get("note", "")).strip()[:120]
        require(int(parsed["sources_count"]) == total, "sources_count mismatch")

        self.last_matched = matched
        self.last_note = note
        self.verified = True
        return "MATCH" if matched else "MISMATCH"

    @gl.public.view
    def is_sealed(self) -> bool:
        return self.sealed is True

    @gl.public.view
    def read_manifest(self) -> str:
        require(self.sealed, "not sealed")
        return canonical(
            {
                "urls_csv": self.urls_csv,
                "urls_hash": self.urls_hash,
                "sources_count": int(self.sources_count),
            }
        )

    @gl.public.view
    def read_last_verify(self) -> str:
        require(self.verified, "no verify yet")
        return canonical(
            {
                "matched": bool(self.last_matched),
                "note": self.last_note,
                "result": "MATCH" if self.last_matched else "MISMATCH",
            }
        )

    @gl.public.view
    def is_host_allowed(self, host: str) -> bool:
        h = (host or "").strip().lower()
        return self.allowed_hosts.get(h, False) is True

    @gl.public.view
    def get_owner(self) -> Address:
        return self.owner
