# Aegis Continuum — Design

## Thesis

Most GenLayer demos answer a one-shot question: *what does the web say right now?*

**Aegis Continuum** answers a different family of questions:

> Is an off-chain condition **still holding** — under fetch failure, host abuse, and explicit fail-closed rules that other contracts can read?

Three primitives share one safety model (allowlist, HTTPS hygiene, fail-closed writes, closed read surface) but solve three distinct jobs: **continuity**, **integrity**, and **gating**.

This is not a dispute/settlement product and not a generic corroboration oracle.

## Modules

### 1. PulseSentinel

**Job:** Record whether allowlisted HTTPS endpoints still look “alive / OK” inside a time window.

- Owner allowlists hosts.
- Anyone can call `pulse(urls)` with 1–4 allowlisted HTTPS URLs.
- Validators fetch pages; comparative consensus on a structured pulse result (`status`, `ok_count`, `total`, `ratio_milli`).
- Deterministic rules map ratio + window into `ALIVE` | `STALE` | `DEAD`.
- Downstream: `is_alive()`, `latest_pulse()`.

**Fail-closed:** unauthorized host, non-HTTPS, empty set → revert. Low ratio → not ALIVE.

### 2. FreezeManifest

**Job:** Seal a consensus fingerprint of content from allowlisted URLs so later changes are detectable.

- `freeze(label, urls)` fetches sources under consensus and stores a canonical manifest + content digest material.
- Later `verify(label, urls)` re-fetches and compares; returns match / mismatch under the same safety rules.
- Downstream: `read_manifest(label)`, `last_verify(label)`.

**Fail-closed:** host violations revert; insufficient fetch agreement does not silently seal garbage.

### 3. ThresholdGate

**Job:** Expose a boolean integration gate that opens only when an external condition clears a threshold.

- Owner configures `threshold_milli`.
- `evaluate(urls)` or bound pulse/freeze signals update gate state.
- Downstream: `is_open()`, `gate_status()`.

**Fail-closed:** gate stays `CLOSED` unless threshold is met under consensus; errors do not open the gate.

## Shared safety model

| Rule | Behavior |
|------|----------|
| Host allowlist | Required before any fetch URL is used |
| HTTPS only | `http://`, IP literals, localhost, `.local` rejected |
| Fail-closed writes | Revert or keep prior safe state; never “open on error” |
| Closed reads | Stable JSON/status views for other contracts |
| No free-form prose storage | Structured fields only |

## Consensus binding (per module)

Documented in each contract header and in `docs/architecture.md` after implementation:

- Comparative where LLM extraction is involved (pulse status phrase / ok counts within tolerance).
- Deterministic post-checks for thresholds, window expiry, and gate open/close.
- Exact equality where digests / counts must match.

## What this is not

- Not a price feed or SLA legal guarantee.
- Not an escrow or fund-routing product.
- Not a one-shot Q&A oracle (see Source Corroboration Covenant for that pattern).
- Not dependent on `example.com` or throwaway pages — demos use real public status/docs endpoints.

## Live evidence plan

Studionet deployments for all three modules with:

1. Happy path (real status/docs URLs)
2. Host-not-allowed revert
3. Insufficient / stale / mismatch path

Receipts recorded in `verification/`.

## Repo layout (target)
