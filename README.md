# Aegis Continuum

On-chain rails that track whether an off-chain condition is **still holding** — under fetch failure, host abuse, and fail-closed gates other contracts can read.

Not a one-shot Q&A oracle. Not escrow. Not a Penumbra clone.

## Modules

| Contract | Job | Key reads |
|----------|-----|-----------|
| `PulseSentinel` | Liveness pulse from allowlisted HTTPS endpoints | `is_alive()`, `latest_pulse()` |
| `FreezeManifest` | Seal + later verify content fingerprint | `read_manifest`, `read_last_verify` |
| `ThresholdGate` | OPEN only if condition clears threshold | `is_open()`, `gate_status()` |

## Shared safety

- Owner host allowlist  
- HTTPS only (no IP / localhost / userinfo)  
- Comparative consensus + deterministic threshold checks  
- Fail-closed: errors never open gates or invent ALIVE  

## Live deployment

Deploy each file under `contracts/` on GenLayer Studionet from [studio.genlayer.com](https://studio.genlayer.com).

1. `allow_host` for each real public host you will use  
2. Call `pulse` / `freeze` / `evaluate` with real HTTPS URLs  
3. Read views; confirm fail-closed on unauthorized hosts  
4. Record receipts in `verification/studionet-e2e.md`

**Demo sources:** real status/docs pages only (e.g. GitHub/Cloudflare status). No `example.com`.

## Tests

```bash
python tests/test_aegis_continuum.py

## Docs

- Design thesis
- Architecture + binding
- E2E matrix

## Limits

- Not a legal uptime SLA or price feed
- Point-in-time validator fetches
- Owner controls allowlists (governance role)
- Studionet is a development network
