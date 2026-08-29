# Aegis Continuum

On-chain rails that track whether an off-chain condition is **still holding** — under fetch failure, host abuse, and fail-closed gates other contracts can read.

Not a one-shot Q&A oracle. Not escrow. Not a Penumbra clone.

## Live Studionet deployments

| Module | Contract |
|--------|----------|
| PulseSentinel | [`0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0`](https://explorer-studio.genlayer.com/address/0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0) |
| FreezeManifest | [`0x6fF53b22a419d3b8FDC0CBbCb5883Aa17bBCd033`](https://explorer-studio.genlayer.com/address/0x6fF53b22a419d3b8FDC0CBbCb5883Aa17bBCd033) |
| ThresholdGate | [`0xC292EE9448DabF9841CE0B52Dd394C6b4f8B18EB`](https://explorer-studio.genlayer.com/address/0xC292EE9448DabF9841CE0B52Dd394C6b4f8B18EB) |

Full receipts: [`verification/studionet-e2e.md`](verification/studionet-e2e.md)

## Modules

| Contract | Job | Key reads |
|----------|-----|-----------|
| `PulseSentinel` | Liveness pulse from allowlisted HTTPS endpoints | `is_alive()`, `latest_pulse()` |
| `FreezeManifest` | Seal + later verify content fingerprint | `read_manifest`, `read_last_verify` |
| `ThresholdGate` | OPEN only if condition clears threshold | `is_open()`, `gate_status()` |

## Proven on-chain

- **Pulse:** `ALIVE` ratio 1000 on `docs.genlayer.com`; unauthorized host reverts  
- **Freeze:** manifest sealed for `genlayer-docs`; unauthorized host reverts  
- **Gate:** `OPEN` ratio 1000 on docs+genlayer; unauthorized host reverts  

## Shared safety

- Owner host allowlist  
- HTTPS only (no IP / localhost / userinfo)  
- Comparative consensus + deterministic threshold checks  
- Fail-closed: errors never open gates or invent ALIVE  

## How to reproduce

1. Deploy each file under `contracts/` on [Studionet](https://studio.genlayer.com)  
2. `allow_host` for real public hosts only  
3. Call `pulse` / `freeze` / `evaluate`  
4. Confirm fail-closed with a non-allowlisted host  

## Tests

python tests/test_aegis_continuum.py

## Docs
- Design thesis
- Architecture + binding
- E2E matrix

## Limits
- Not a legal uptime SLA or price feed
- LLM content digests are point-in-time and non-cryptographic (verify may MISMATCH on phrase variance)
- Owner controls allowlists (governance role)
- Studionet is a development network
