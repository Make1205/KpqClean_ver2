# Timing protocol

GCC -O3 -march=native -std=c99; native integer/fixed-point algorithms unchanged.
Each timing round uses a fresh encoded keypair, signs from byte sk and verifies
from byte pk, including all native decoding/expansion/hash/RNG work. Message:
32 zero bytes. Discard 20 complete warmup triples. Use unchanged Dilithium
bba9534 timing files and median ticks/1000. Pin first allowed logical CPU.
QUICK=1: timing 11, correctness/length 100. FULL: 10001/10000. Native KAT
counts remain 100. Actual encoded length still uses the two native offsets,
not backward zero stripping. No sudo/network. FULL measurements run locally.
