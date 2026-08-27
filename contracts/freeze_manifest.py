# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
FreezeManifest — Aegis Continuum
================================

Integrity primitive: seal a consensus fingerprint of allowlisted HTTPS
content so later changes are detectable via verify().

Not a price feed. Not escrow. Not one-shot Q&A.
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


@allow_storage
@dataclass
class Manifest:
    label: str
    digest: str
    sources_count: u256
    urls_hash: str
    summary: str


@allow_storage
@dataclass
class VerifyResult:
    label: str
    matched: bool
    prior_digest: str
    new_digest: str


class FreezeManifest(gl.Contract):
    owner: Address
    allowed_hosts: TreeMap[str, bool]
    manifests: TreeMap[str, Manifest]
    last_verify: TreeMap[str, VerifyResult]
    labels: DynArray[str]
    tolerance_note: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.tolerance_note = u256(0)

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

    def _prepare_urls(self, urls: str) -> list:
        raw_urls = urls if isinstance(urls, str) else ""
        url_list = [u.strip() for u in raw_urls.split(",") if u.strip()]
        require(1 <= len(url_list) <= 4, "need 1 to 4 comma-separated urls")
        seen = {}
        for u in url_list:
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)
            require(u not in seen, "duplicate url")
            seen[u] = True
        return url_list

    def _extract_digest(self, url_list: list) -> str:
        total = len(url_list)
        urls_for_nondet = list(url_list)

        def extract() -> str:
            parts = []
            for i, u in enumerate(urls_for_nondet):
                try:
                    content = gl.nondet.web.render(u, mode="text")
                    snippet = (content[:3000] if content else "[EMPTY PAGE]")
                except Exception as e:
                    snippet = ("[FETCH FAILED: " + str(e) + "]")[:240]
                parts.append("SOURCE " + str(i + 1) + " (" + u + "):\n---\n" + snippet + "\n---")
            block = "\n\n".join(parts)
            prompt = (
                "You fingerprint the COMBINED content of these sources for integrity checking.\n"
                "Ignore volatile timestamps, ads, and cookie banners when possible.\n"
                "Focus on stable main content identity.\n\n"
                + block
                + "\n\n"
                "Return ONLY strict JSON:\n"
                '{ "digest": "<short stable fingerprint phrase 8-24 chars>", '
                '"summary": "<one short line>" }'
            )
            raw = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(raw)
            digest = str(data.get("digest", "")).strip().lower()
            require(8 <= len(digest) <= 64, "bad digest length")
            summary = str(data.get("summary", "")).strip()[:160]
            return canonical({"digest": digest, "summary": summary, "sources_count": total})

        principle = (
            "EQUIVALENT if and only if: (1) 'digest' means the same content identity "
            "(minor wording differences allowed if clearly same fingerprint intent), "
            "(2) 'sources_count' is identical. If digests clearly refer to different "
            "content identities, NOT equivalent."
        )
        agreed = gl.eq_principle.prompt_comparative(extract, principle)
        return agreed

    @gl.public.write
    def freeze(self, label: str, urls: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        require(1 <= len(lab) <= 64, "bad label")
        require(lab not in self.manifests, "label already frozen")

        url_list = self._prepare_urls(urls)
        agreed = self._extract_digest(url_list)
        parsed = json.loads(agreed)
        digest = str(parsed["digest"]).strip().lower()
        summary = str(parsed.get("summary", "")).strip()[:160]
        sources_count = int(parsed["sources_count"])
        require(sources_count == len(url_list), "sources_count mismatch")

        urls_hash = canonical({"urls": url_list})
        self.manifests[lab] = Manifest(
            label=lab,
            digest=digest,
            sources_count=u256(sources_count),
            urls_hash=urls_hash,
            summary=summary,
        )
        self.labels.append(lab)
        return digest

    @gl.public.write
    def verify(self, label: str, urls: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        require(lab in self.manifests, "unknown label")
        prior = self.manifests[lab]

        url_list = self._prepare_urls(urls)
        agreed = self._extract_digest(url_list)
        parsed = json.loads(agreed)
        new_digest = str(parsed["digest"]).strip().lower()
        sources_count = int(parsed["sources_count"])
        require(sources_count == len(url_list), "sources_count mismatch")

        matched = new_digest == prior.digest or (
            len(new_digest) > 0 and prior.digest in new_digest
        ) or (
            len(prior.digest) > 0 and new_digest in prior.digest
        )
        # Prefer exact match; soft containment only if exact fails but strings overlap strongly
        matched = new_digest == prior.digest

        self.last_verify[lab] = VerifyResult(
            label=lab,
            matched=matched,
            prior_digest=prior.digest,
            new_digest=new_digest,
        )
        return "MATCH" if matched else "MISMATCH"

    @gl.public.view
    def read_manifest(self, label: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        require(lab in self.manifests, "unknown label")
        m = self.manifests[lab]
        return canonical(
            {
                "label": m.label,
                "digest": m.digest,
                "sources_count": int(m.sources_count),
                "urls_hash": m.urls_hash,
                "summary": m.summary,
            }
        )

    @gl.public.view
    def read_last_verify(self, label: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        require(lab in self.last_verify, "no verify yet")
        v = self.last_verify[lab]
        return canonical(
            {
                "label": v.label,
                "matched": bool(v.matched),
                "prior_digest": v.prior_digest,
                "new_digest": v.new_digest,
                "result": "MATCH" if v.matched else "MISMATCH",
            }
        )

    @gl.public.view
    def label_count(self) -> u256:
        return u256(len(self.labels))

    @gl.public.view
    def is_host_allowed(self, host: str) -> bool:
        h = (host or "").strip().lower()
        return self.allowed_hosts.get(h, False) is True

    @gl.public.view
    def get_owner(self) -> Address:
        return self.owner
