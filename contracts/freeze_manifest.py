# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
FreezeManifest — Aegis Continuum (storage-safe + consensus match)
================================================================

Seal HTTPS content fingerprint; verify judges MATCH under comparative
consensus against sealed digest + original URL manifest.
Primitive TreeMaps only (no nested dataclass storage).
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


def _normalize_url_list(urls: str) -> list:
    raw = urls if isinstance(urls, str) else ""
    url_list = [u.strip() for u in raw.split(",") if u.strip()]
    require(1 <= len(url_list) <= 4, "need 1 to 4 comma-separated urls")
    seen = {}
    out = []
    for u in url_list:
        require(u not in seen, "duplicate url")
        seen[u] = True
        out.append(u)
    return out


class FreezeManifest(gl.Contract):
    owner: Address
    allowed_hosts: TreeMap[str, bool]
    # primitive storage only
    digest_of: TreeMap[str, str]
    urls_csv_of: TreeMap[str, str]
    urls_hash_of: TreeMap[str, str]
    summary_of: TreeMap[str, str]
    sources_of: TreeMap[str, u256]
    labels: DynArray[str]
    # last verify
    verify_matched: TreeMap[str, bool]
    verify_new_digest: TreeMap[str, str]
    verify_note: TreeMap[str, str]

    def __init__(self):
        self.owner = gl.message.sender_address

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
        url_list = _normalize_url_list(urls)
        for u in url_list:
            host = _host_of(u)
            require(self.allowed_hosts.get(host, False) is True, "host not allowed: " + host)
        return url_list

    def _extract_seal(self, url_list: list) -> str:
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
                '{ "digest": "<short stable fingerprint phrase 8-48 chars>", '
                '"summary": "<one short line>" }'
            )
            raw = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(raw)
            digest = str(data.get("digest", "")).strip().lower()
            require(8 <= len(digest) <= 64, "bad digest length")
            summary = str(data.get("summary", "")).strip()[:160]
            return canonical({"digest": digest, "summary": summary, "sources_count": total})

        principle = (
            "EQUIVALENT if and only if: (1) 'digest' refers to the same content identity "
            "(minor wording differences allowed if clearly the same fingerprint intent), "
            "(2) 'sources_count' is identical. If digests clearly refer to different "
            "content identities, NOT equivalent."
        )
        return gl.eq_principle.prompt_comparative(extract, principle)

    def _judge_match(self, url_list: list, prior_digest: str) -> str:
        total = len(url_list)
        urls_for_nondet = list(url_list)
        sealed = (prior_digest or "").strip().lower()

        def judge() -> str:
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
                "You verify content integrity against a SEALED fingerprint.\n\n"
                "SEALED DIGEST: " + sealed + "\n\n"
                "Current sources (" + str(total) + "):\n"
                + block
                + "\n\n"
                "Decide if the current main content still matches the sealed content identity.\n"
                "Ignore volatile timestamps, ads, cookie banners.\n"
                "Return ONLY strict JSON:\n"
                '{ "matched": true or false, '
                '"new_digest": "<short fingerprint of current content 8-48 chars>", '
                '"note": "<short reason>" }'
            )
            raw = gl.nondet.exec_prompt(prompt)
            data = parse_json_response(raw)
            matched = bool(data.get("matched", False))
            new_digest = str(data.get("new_digest", "")).strip().lower()
            if len(new_digest) < 8:
                new_digest = "unspecified"
            note = str(data.get("note", "")).strip()[:120]
            return canonical(
                {
                    "matched": matched,
                    "new_digest": new_digest,
                    "note": note,
                    "sources_count": total,
                }
            )

        principle = (
            "EQUIVALENT if and only if: (1) 'matched' is identical, "
            "(2) 'sources_count' is identical. "
            "Wording of new_digest/note may differ. "
            "If matched differs, NOT equivalent."
        )
        return gl.eq_principle.prompt_comparative(judge, principle)

    @gl.public.write
    def freeze(self, label: str, urls: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        require(1 <= len(lab) <= 64, "bad label")
        require(len(self.digest_of.get(lab, "")) == 0, "label already frozen")

        url_list = self._prepare_urls(urls)
        agreed = self._extract_seal(url_list)
        parsed = json.loads(agreed)
        digest = str(parsed["digest"]).strip().lower()
        summary = str(parsed.get("summary", "")).strip()[:160]
        sources_count = int(parsed["sources_count"])
        require(sources_count == len(url_list), "sources_count mismatch")

        urls_csv = ",".join(url_list)
        urls_hash = canonical({"urls": url_list})

        self.digest_of[lab] = digest
        self.urls_csv_of[lab] = urls_csv
        self.urls_hash_of[lab] = urls_hash
        self.summary_of[lab] = summary
        self.sources_of[lab] = u256(sources_count)
        self.labels.append(lab)
        return digest

    @gl.public.write
    def verify(self, label: str, urls: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        prior = self.digest_of.get(lab, "")
        require(len(prior) > 0, "unknown label")

        url_list = self._prepare_urls(urls)
        sealed_csv = self.urls_csv_of.get(lab, "")
        sealed_hash = self.urls_hash_of.get(lab, "")
        require(",".join(url_list) == sealed_csv, "url manifest mismatch")
        require(canonical({"urls": url_list}) == sealed_hash, "url hash mismatch")

        agreed = self._judge_match(url_list, prior)
        parsed = json.loads(agreed)
        matched = bool(parsed["matched"])
        new_digest = str(parsed.get("new_digest", "")).strip().lower()
        note = str(parsed.get("note", "")).strip()[:120]
        sources_count = int(parsed["sources_count"])
        require(sources_count == len(url_list), "sources_count mismatch")

        self.verify_matched[lab] = matched
        self.verify_new_digest[lab] = new_digest
        self.verify_note[lab] = note
        return "MATCH" if matched else "MISMATCH"

    @gl.public.view
    def read_manifest(self, label: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        d = self.digest_of.get(lab, "")
        require(len(d) > 0, "unknown label")
        return canonical(
            {
                "label": lab,
                "digest": d,
                "sources_count": int(self.sources_of.get(lab, u256(0))),
                "urls_csv": self.urls_csv_of.get(lab, ""),
                "urls_hash": self.urls_hash_of.get(lab, ""),
                "summary": self.summary_of.get(lab, ""),
            }
        )

    @gl.public.view
    def read_last_verify(self, label: str) -> str:
        lab = (label if isinstance(label, str) else "").strip()
        require(lab in self.verify_matched, "no verify yet")
        matched = bool(self.verify_matched[lab])
        return canonical(
            {
                "label": lab,
                "matched": matched,
                "prior_digest": self.digest_of.get(lab, ""),
                "new_digest": self.verify_new_digest.get(lab, ""),
                "note": self.verify_note.get(lab, ""),
                "result": "MATCH" if matched else "MISMATCH",
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
