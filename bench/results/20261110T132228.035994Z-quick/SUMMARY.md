# HAETAE benchmark: QUICK

**QUICK: numbers validate output format only; do not use as performance or distribution estimates.**

- Tested commit: `34046d35956e55efd6079aea22ecab5de843400e` (driver hashes and working-tree status retained).
- CPU: AMD EPYC 9V74 80-Core Processor
- GCC: gcc (Debian 14.2.0-19) 14.2.0
- Flags: `-O3 -march=native -std=c99`.
- HAETAE v1.1.2 clean only, mode2/mode3/mode5; n=256, q=64513; no HAETAE AVX2 in this repository.
- Per mode: KAT 100 records; 100 valid signatures verified plus modified-message/signature rejection; 100 length samples; 11 timed calls per operation.
- Messages: 32 bytes, empty context, unchanged randomized public API and OS random source; fresh key every 100 correctness signatures.
- Sign/Verify timing starts with serialized sk/pk; includes unpacking. Fresh keypair per timed triple; 20 complete warmup triples discarded.

All timing values below are medians in kilocycles (cycles/ticks divided by 1000).

| Parameter | q | pk | sig (repository fixed) | paper mean sig | ref KeyGen | ref Sign | ref Verify | AVX2 KeyGen | AVX2 Sign | AVX2 Verify |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| haetae_mode2 | 64513 | 992 | 1474 | 1463 | 448.421 | 2693.781 | 135.459 | -- | -- | -- |
| haetae_mode3 | 64513 | 1472 | 2349 | 2337 | 1153.697 | 3306.315 | 230.697 | -- | -- | -- |
| haetae_mode5 | 64513 | 2080 | 2948 | 2908 | 720.433 | 3454.229 | 280.643 | -- | -- | -- |

| Parameter | length samples | encoded mean | encoded max | paper mean | mean minus paper |
|---|---:|---:|---:|---:|---:|
| haetae_mode2 | 100 | 1468.340000 | 1474 | 1463 | 5.340000 |
| haetae_mode3 | 100 | 2344.110000 | 2347 | 2337 | 7.110000 |
| haetae_mode5 | 100 | 2943.700000 | 2947 | 2908 | 35.700000 |

Length method (bench driver only): API siglen is fixed. At p=N/8+L*N, read the two serialized offsets. Actual encoded bytes = p+2+BASE_ENC_HB_Z1+sig[p]+BASE_ENC_H+sig[p+1], matching packing.c:pack_sig/unpack_sig. Require every subsequent byte to be zero. This preserves any zero bytes at the end of real encoded data; no heuristic trailing-zero stripping. Signatures remain fixed-length for verification.

Timer: the four unchanged pq-crystals/dilithium ref/test files from bba9534a3c5cbef66481cd6518d786e23ae601b5. Each call has start/end cpucycles reads; intervals are accumulated into N+1 synthetic timestamps so unchanged speed_print differences exactly N samples, subtracts its calibrated overhead, and computes the median. Default RDTSC ticks are used (not RDPMC, no system settings changed); TSC ticks are not necessarily actual core cycles. Only each byte API call is timed. Logical CPU is pinned to the first allowed CPU; no frequency changes.

KAT means the unchanged repository generator exited successfully, performed its sign/open checks, and emitted counts 0..99; no golden vectors are supplied. Paper means 1463/2337/2908 are the supplied comparison values; exact paper/version equivalence remains unconfirmed.

Reproduce full scale: `LANG=C bash bench/run.sh` (QUICK unset). Offline, no sudo; requires bash, Python >=3.8 standard library, GCC, Git, Linux /proc and x86-64 RDTSC. Generated KAT vectors include test secret keys and stay local.
