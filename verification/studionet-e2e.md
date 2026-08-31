# Studionet E2E - Aegis Continuum

Real public HTTPS only (docs.genlayer.com / genlayer.com). No example.com success paths.

## PulseSentinel

| Item | Value |
|------|--------|
| Contract | [`0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0`](https://explorer-studio.genlayer.com/address/0x8A1e9FfaC1F42985B19C8B7819ED62419A1e01F0) |
| Deploy tx | [`0x23f40cea94b04a2b808f1c1d097d04381ff443bc1a5fcdedc6f0cd1863ad958ba`](https://explorer-studio.genlayer.com/tx/0x23f40cea94b04a2b808f1c1d097d04381ff443bc1a5fcdedc6f0cd1863ad958ba) |
| pulse SUCCESS | `https://docs.genlayer.com` → status `ALIVE`, ratio_milli `1000`, `is_alive` true, count `1` |
| Fail-closed | `pulse(https://example.com)` → ERROR `[rollback] host not allowed: example.com` tx `0xed5cbe45d0bcffde7928912f60f555eab244af0754c0110b4531cd5ff5e8fa6f` |

## FreezeManifest (rejection fix)

| Item | Value |
|------|--------|
| Contract | [`0xC9a1324cAF21c51F2A498C34356919bEaC69Ff15`](https://explorer-studio.genlayer.com/address/0xC9a1324cAF21c51F2A498C34356919bEaC69Ff15) |
| Deploy | [`0xf2cd23f8861b413a8e46ca97369f92a283daf8c90064327328d7e5761e6f73aa`](https://explorer-studio.genlayer.com/tx/0xf2cd23f8861b413a8e46ca97369f92a283daf8c90064327328d7e5761e6f73aa) |
| Design | Deterministic URL-manifest seal; verify = comparative consensus on `matched` (not post-hoc digest equality); sealed URLs enforced |
| freeze | [`0xb33d016b…`](https://explorer-studio.genlayer.com/tx/0xb33d016b48cd65d1aa895925503130ee9a5861e40f9e1efcfc42f87cd58b1143) Accepted → `is_sealed` true |
| verify MATCH | [`0xe27e96dc…`](https://explorer-studio.genlayer.com/tx/0xe27e96dc31b97fcc4c1c9ae71880122ca2cce3430be85948e1cedd43efee645e) → `MATCH` |
| url manifest fail | [`0x042238b2…`](https://explorer-studio.genlayer.com/tx/0x042238b2d5c72a93bc4007341399bbd23201fc24c07d3781f7826d868ecb2aae) → `url manifest mismatch` |
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
