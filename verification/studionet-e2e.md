# Studionet E2E — Aegis Continuum

Real public HTTPS only (docs.genlayer.com / genlayer.com). No example.com success paths.

## PulseSentinel

| Item | Value |
|------|--------|
| Contract | [`0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0`](https://explorer-studio.genlayer.com/address/0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0) |
| Deploy tx | [`0x23f40cea94b04a2b808f1c1d097d04381ff443bc1a5fcdedc6f0cd1863ad958ba`](https://explorer-studio.genlayer.com/tx/0x23f40cea94b04a2b808f1c1d097d04381ff443bc1a5fcdedc6f0cd1863ad958ba) |
| pulse SUCCESS | `https://docs.genlayer.com` → status `ALIVE`, ratio_milli `1000`, `is_alive` true, count `1` |
| Fail-closed | `pulse(https://example.com)` → ERROR `[rollback] host not allowed: example.com` tx `0xed5cbe45d0bcffde7928912f60f555eab244af0754c0110b4531cd5ff5e8fa6f` |

## FreezeManifest

| Item | Value |
|------|--------|
| Contract | [`0x6fF53b22a419d3b8FDC0CBbCb5883Aa17bBCd033`](https://explorer-studio.genlayer.com/address/0x6fF53b22a419d3b8FDC0CBbCb5883Aa17bBCd033) |
| Deploy tx | [`0x7e75b387cd56695a85f31df2871bc965cbcf68e9b90210cbc135a12be6581aaa`](https://explorer-studio.genlayer.com/tx/0x7e75b387cd56695a85f31df2871bc965cbcf68e9b90210cbc135a12be6581aaa) |
| freeze SUCCESS | label `genlayer-docs`, url `https://docs.genlayer.com`, digest sealed |
| verify | same URL → `MISMATCH` (LLM digest variance; strict exact match — documented limit) |
| Fail-closed | `freeze(should-fail, https://example.com)` → ERROR `host not allowed` tx `0xc12d22caf8907aea5387445f5866cffcb33bd389f9333c5322d6a9abf32f23cc` |

## ThresholdGate

| Item | Value |
|------|--------|
| Contract | [`0xC292EE9448DabF9841CE0B52Dd394C6b4f8B18EB`](https://explorer-studio.genlayer.com/address/0xC292EE9448DabF9841CE0B52Dd394C6b4f8B18EB) |
| Deploy tx | [`0x8edb3196e86bae2b024f860fa23f7fa4dd32632f23ec92839f7b97ff8e001c64`](https://explorer-studio.genlayer.com/tx/0x8edb3196e86bae2b024f860fa23f7fa4dd32632f23ec92839f7b97ff8e001c64) |
| evaluate SUCCESS | question on GenLayer docs; urls docs+genlayer → `OPEN`, ratio_milli `1000`, agreeing `2`, `is_open` true, count `1` |
| Fail-closed | `evaluate` with example.com/org → ERROR `host not allowed` tx `0xb36800dcb495afd65992089570b6d36aae04e3b5274a2c62b7fb411df266ddfb` |

## Notes

- All three modules share allowlist + HTTPS hygiene + fail-closed host rejection.
- Freeze verify MISMATCH is honest strict fingerprinting under non-deterministic LLM digests; freeze seal and host rejection still hold.
- Studionet development network; not a production SLA.
