# Studionet E2E - Aegis Continuum

Real public HTTPS only (docs.genlayer.com / genlayer.com). No example.com success paths.

## PulseSentinel

| Item | Value |
|------|--------|
| Contract | [`0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0`](https://explorer-studio.genlayer.com/address/0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0) |
| Deploy tx | [`0x23f40cea94b04a2b808f1c1d097d04381ff443bc1a5fcdedc6f0cd1863ad958ba`](https://explorer-studio.genlayer.com/tx/0x23f40cea94b04a2b808f1c1d097d04381ff443bc1a5fcdedc6f0cd1863ad958ba) |
| pulse SUCCESS | `https://docs.genlayer.com` → status `ALIVE`, ratio_milli `1000`, `is_alive` true, count `1` |
| Fail-closed | `pulse(https://example.com)` → ERROR `[rollback] host not allowed: example.com` tx `0xed5cbe45d0bcffde7928912f60f555eab244af0754c0110b4531cd5ff5e8fa6f` |

## FreezeManifest (resubmit build)

| Item | Value |
|------|--------|
| Contract | [`0x85C307f9959a8725756580DC62E0649Cc4c24588`](https://explorer-studio.genlayer.com/address/0x85C307f9959a8725756580DC62E0649Cc4c24588) |
| Deploy | [`0x881bb7da002ba12928e2fa4f8b6c0b7b0af8c74cc946ebc665fda277ab1febcf`](https://explorer-studio.genlayer.com/tx/0x881bb7da002ba12928e2fa4f8b6c0b7b0af8c74cc946ebc665fda277ab1febcf) |
| freeze | [`0x5f8d80de6c22e1822ef3ee8aed3024c532b1344170ce0c8247bfbc58e06d6285`](https://explorer-studio.genlayer.com/tx/0x5f8d80de6c22e1822ef3ee8aed3024c532b1344170ce0c8247bfbc58e06d6285) |
| verify MATCH | [`0x8ccd4331e62ec358a1fa63ccf2e4d803a2ba743c099e858bdf9ee9f05fcab7b1`](https://explorer-studio.genlayer.com/tx/0x8ccd4331e62ec358a1fa63ccf2e4d803a2ba743c099e858bdf9ee9f05fcab7b1) |
| wrong host | [`0xa719b304942de789711f14068bb0dd91cc497189de25d328efecb920e5f8f2dc`](https://explorer-studio.genlayer.com/tx/0xa719b304942de789711f14068bb0dd91cc497189de25d328efecb920e5f8f2dc) — host not allowed |

Mechanism: deterministic `freeze` seal; `verify` consensus on `matched` bool (not phrase equality).


## ThresholdGate

| Item | Value |
|------|--------|
| Contract | [`0xC292EE9448DabF9841CE0B52Dd394C6b4f8B18EB`](https://explorer-studio.genlayer.com/address/0xC292EE9448DabF9841CE0B52Dd394C6b4f8B18EB) |
| Deploy tx | [`0x8edb3196e86bae2b024f860fa23f7fa4dd32632f23ec92839f7b97ff8e001c64`](https://explorer-studio.genlayer.com/tx/0x8edb3196e86bae2b024f860fa23f7fa4dd32632f23ec92839f7b97ff8e001c64) |
| evaluate SUCCESS | question on GenLayer docs; urls docs+genlayer → `OPEN`, ratio_milli `1000`, agreeing `2`, `is_open` true, count `1` |
| Fail-closed | `evaluate` with example.com/org → ERROR `host not allowed` tx `0xb36800dcb495afd65992089570b6d36aae04e3b5274a2c62b7fb411df266ddfb` |

## Notes

- All three modules share allowlist + HTTPS hygiene + fail-closed host rejection.
- FreezeManifest: `freeze` is deterministic URL seal only; `verify` uses comparative consensus on `matched` bool (note non-binding); MATCH/MISMATCH follows agreed `matched`, not post-hoc phrase equality.
- Studionet development network; not a production SLA.
