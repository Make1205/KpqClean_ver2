# HAETAE inventory and paper-size gate

## Starting state and scope

- Initial command: `git status`; branch `work`, clean working tree.
- Full starting commit: `c20b422b715c6e12edb04cfe0ceb659d8ac7b7a9`.
- Created branch `bench` directly from that commit, without a worktree.
- Repository: Make1205/KpqClean_ver2. No Copa code is involved.
- Only new files under `bench/` are added. No HAETAE algorithm, parameter,
  sampler, encoding, randomness, common code, or other scheme is modified.

## Version and implementations

README.md identifies HAETAE v1.1.2, upstream CryptoLabInc/HAETAE commit
`743c31d` (2026-02-05). This is the repository's stated provenance, not an
independently verified correspondence to a particular paper or KpqC round.
The supplied table has no paper citation/version identifier, so an exact
paper-version match cannot be established from that table alone.

Three parameter sets are present: `crypto_sign/HAETAE2/clean`,
`crypto_sign/HAETAE3/clean`, `crypto_sign/HAETAE5/clean`. Each directory's
`config.h` selects its default `HAETAE_CONFIG_MODE`: `HAETAE_MODE2`,
`HAETAE_MODE3`, or `HAETAE_MODE5`. These constants are internally 0, 1, 2;
passing numeric 2/3/5 as an override would be incorrect. No override is used.

Only the portable clean implementation is present. No HAETAE AVX2 directory,
SIMD intrinsic implementation, or AVX2 build selector is present. Shared
`common/keccak4x` and `common/Keccak_avx2` do not constitute an HAETAE AVX2
implementation and are not linked. The selected common SHAKE is `fips202.c`.
The compiler may auto-vectorize with `-march=native`; that is not an AVX2
algorithm implementation.

| Repository parameter set | n | q | pk bytes | Signature buffer / API bytes | Paper row (by order only) | Paper mean bytes |
|---|---:|---:|---:|---:|---|---:|
| HAETAE mode2 | 256 | 64513 | 992 | 1474 | HAETAE-120 | 1463 |
| HAETAE mode3 | 256 | 64513 | 1472 | 2349 | HAETAE-180 | 2337 |
| HAETAE mode5 | 256 | 64513 | 2080 | 2948 | HAETAE-260 | 2908 |

The paper labels are not repository parameter-set names. Their pairing above
is for the requested three-row size comparison, not a proven security claim.

## Signature length discrepancy

The public detached signature API returns fixed-length, zero-padded signatures.
In all three copies of `sign.c`, successful signing sets
`*siglen = HAETAE_CRYPTO_BYTES`; verification rejects any other length.
`packing.c:pack_sig` zero-fills the entire buffer and rejects/retries encodings
that would exceed it. Internal compressed components vary in size, but their
unpadded payload sizes are not the public API's signature lengths. We neither
strip padding nor change the algorithm to match the table.

`inventory.c` measures **10,000 detached signatures per parameter set**, using
100 fresh public-API keypairs and 100 messages per key. Messages are 32 bytes,
with an empty context. It uses the repository's unchanged OS random source
and randomized public signer. Every signature is verified; a modified final
message must be rejected. The average is calculated from returned `siglen`,
not inferred from the maximum or from KAT files. Results appear in
`results/<UTC timestamp>-inventory/inventory.csv` and `SUMMARY.md`.

## Build and correctness choices

System GCC, `-O3 -march=native -std=c99`; include only the selected HAETAE
clean directory and `common`. The exact core source list follows the existing
HAETAE Makefile. No source patches, pointer-warning suppression, or repository
benchmark driver are needed: the external inventory driver uses correct
`size_t` lengths and the public detached APIs. No timing code is used here.

The repository includes `crypto_sign/sign_bench/HAETAE_PQCgenKAT_sign.c`
and each mode's `kat_sign.c`. Build those unchanged with the core and the
repository AES-CTR DRBG (`common/rng.c`), then run each in its own fresh output
directory. Require exit status zero and exactly counts 0..99 in its response.
This exercises the existing sign/verify self-checks; the repository supplies
no golden vectors to compare against. AVX2/ref KAT comparison and cross-
verification are inapplicable because HAETAE AVX2 is absent.

KAT vectors contain test secret keys and are generated locally, not committed;
small logs and reports are retained. `inventory.sh` requires bash, Python >=3.8
standard library, GCC, Git, and normal base-system tools; no sudo or network.
All commands inherit `LANG=C` and `LC_ALL=C`. Output directory names use UTC.

## Benchmark continuation (authorized after the inventory gate)

The user authorized continuing from 326c4a930332aed09485ecb95c150927dee78bea
while retaining the fixed API serialization. The earlier size-mismatch pause
is superseded. Algorithm sources and other schemes remain unchanged.

Run `LANG=C bash bench/run.sh` with QUICK unset for full scale. This uses
10001 timed calls per operation, 30000 correctness signatures per mode, and
10000 length samples per mode. `QUICK=1 LANG=C bash bench/run.sh` uses 11,
100, and 100 respectively, and is the only scale executed in the cloud.
The unchanged KAT generator always emits 100 records per mode.

The new driver reads exact compressed lengths from the two serialized length
offsets at N/8+L*N, adds both encoding baselines and the fixed prefix, and
checks that all bytes after the computed boundary are zero. This is more
precise than scanning backwards through zeros, which could discard valid
encoded zeros. The API still signs and verifies the full padded buffer.

The four Dilithium bba9534 timer files are vendored unchanged under
bench/dilithium with provenance and SHA-256 hashes. Independent start/end
intervals are accumulated into N+1 timestamps for unchanged speed_print,
which differences exactly N samples, subtracts its overhead, and reports the
median. RDTSC ticks are reported as kilocycles with the TSC caveat in SUMMARY.
Sign/Verify call the public API on byte-form sk/pk, including unpacking.

Only bash, Python >=3.8 standard library, installed GCC and Git are needed;
Linux /proc supplies CPU metadata and the unchanged timer requires x86-64.
No network, sudo, CPU configuration, dependency installation, or environment
configuration changes occur in the run script. LANG=C and LC_ALL=C are
inherited by all child commands. Exact compiler arguments, GCC version, CPU
information, HEAD, working-tree status and driver hashes are retained.

Outputs: bench/results/<UTC timestamp>-quick or -full/SUMMARY.md and bench.csv,
plus build/run logs and metadata. KAT vectors include generated test keys and
stay local, as do binaries; small cloud smoke-test reports are committed.
QUICK summaries explicitly mark all numbers as format checks only.

Cloud smoke validation: `QUICK=1 bash bench/run.sh` passed all three modes
on tested driver commit dd621dfdc1f85f99918eeafb10c9c1c33aff7e70. Reports:
`results/20261110T041647.856370Z-quick/`. No full-scale run was executed.
