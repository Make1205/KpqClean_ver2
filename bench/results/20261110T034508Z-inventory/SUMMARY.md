# HAETAE inventory: PAUSED (paper signature-size mismatch)

Cloud run validates the inventory workflow only. No performance measurements have been run.

- Code commit: `c20b422b715c6e12edb04cfe0ceb659d8ac7b7a9`
- CPU: INTEL(R) XEON(R) PLATINUM 8573C
- GCC: gcc (Debian 14.2.0-19) 14.2.0
- Flags: `-O3 -march=native -std=c99 (system GCC)`
- Version: README identifies HAETAE v1.1.2, upstream `743c31d` (2026-02-05).
- Implementation: clean only; HAETAE AVX2 does not exist in this checkout.
- Messages: 32 bytes; empty context; unchanged public randomized signer.

Timing columns use kilocycles when measured. `not run` means the size gate stopped timing; `--` means no AVX2 implementation.

| Parameter | q | pk | sig (mean) | ref KeyGen | ref Sign | ref Verify | AVX2 KeyGen | AVX2 Sign | AVX2 Verify |
|---|---:|---:|---:|---|---|---|---|---|---|
| haetae_mode2 | 64513 | 992 | 1474.000000 | not run | not run | not run | -- | -- | -- |
| haetae_mode3 | 64513 | 1472 | 2349.000000 | not run | not run | not run | -- | -- | -- |
| haetae_mode5 | 64513 | 2080 | 2948.000000 | not run | not run | not run | -- | -- | -- |

| Parameter | n | sig buffer max | signatures | min | max | paper mean | measured minus paper |
|---|---:|---:|---:|---:|---:|---:|---:|
| haetae_mode2 | 256 | 1474 | 10000 | 1474 | 1474 | 1463 | +11.000000 |
| haetae_mode3 | 256 | 2349 | 10000 | 2349 | 2349 | 2337 | +12.000000 |
| haetae_mode5 | 256 | 2948 | 10000 | 2948 | 2948 | 2908 | +40.000000 |

The three q and pk values match the supplied table. Signature means do not: the repository API returns fixed-length padded signatures (1474/2349/2948 bytes), whereas the paper table lists 1463/2337/2908 bytes. The table does not identify a paper/version, so exact version equivalence is unconfirmed.

Each mode completed the existing KAT generator (exit 0; 100 records), plus 10,000 public-API signatures verified and a modified message rejected. No upstream golden KAT reference is supplied. No source changes were needed.

Stopped under the requested size-mismatch rule. Await confirmation before timer import, performance timing, and the complete run.sh/bench.csv delivery.
