# Architecture — Aegis Continuum

## Family

Three fail-closed primitives that answer *is the off-chain condition still holding?* rather than one-shot Q&A.

| Module | Write path | Downstream reads |
|--------|------------|------------------|
| PulseSentinel | `pulse(urls)` | `is_alive()`, `latest_pulse()` |
| FreezeManifest | `freeze` / `verify` | `read_manifest`, `read_last_verify` |
| ThresholdGate | `evaluate(question, urls)` | `is_open()`, `gate_status()` |

## Shared rules

- Owner-managed host allowlist before any fetch
- HTTPS only; reject IP literals, localhost, userinfo
- Comparative consensus where extraction is non-deterministic
- Deterministic post-checks for thresholds and status mapping
- Errors do not open gates or invent ALIVE

## Consensus binding

### PulseSentinel

| Field | Binding |
|-------|---------|
| status | comparative + deterministic remap from ratio |
| ok_count / ratio_milli | comparative within tolerance |
| total | exact |

### FreezeManifest

| Field | Binding |
|-------|---------|
| digest | comparative meaning (content identity) |
| sources_count | exact |

### ThresholdGate

| Field | Binding |
|-------|---------|
| open | comparative then deterministic threshold |
| ratio_milli / agreeing | comparative within tolerance |
| total | exact |

## Fail-closed matrix

| Condition | Pulse | Freeze | Gate |
|-----------|-------|--------|------|
| Host not allowed | revert | revert | revert |
| Non-HTTPS / IP / localhost | revert | revert | revert |
| Low ratio | DEAD/DEGRADED (not ALIVE) | — | stays CLOSED |
| Never called | `is_alive=false` | no manifest | CLOSED |
| Owner force_close | — | — | CLOSED |

## Demo sources (real only)

Use public status/docs endpoints, e.g.:

- `https://www.githubstatus.com`
- `https://www.cloudflarestatus.com`
- Official project docs HTTPS pages

Always `allow_host` the exact host (`www.` vs apex).

## Limits

- Not a legal SLA or uptime guarantee
- Not a price feed
- Point-in-time under validator fetch
- Owner is a governance role for allowlists
