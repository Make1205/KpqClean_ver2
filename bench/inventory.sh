#!/usr/bin/env bash
# Step 2 only. Performance measurements are paused pending size review.
set -euo pipefail
export LANG=C LC_ALL=C
cd "$(dirname "${BASH_SOURCE[0]}")/.."
root="$PWD"
out="$root/bench/results/$(date -u +%Y%m%dT%H%M%SZ)-inventory"
mkdir -p "$out"
printf '%s\n' "$out"
git rev-parse HEAD > "$out/code-commit.txt"
git diff --exit-code -- crypto_sign/HAETAE2 crypto_sign/HAETAE3 crypto_sign/HAETAE5 common
gcc --version > "$out/gcc.txt"
python3 - <<'PY' > "$out/cpu.txt"
from pathlib import Path
for line in Path('/proc/cpuinfo').read_text().splitlines():
    if line.startswith('model name'):
        print(line.split(':', 1)[1].strip())
        break
PY
printf '%s\n' '-O3 -march=native -std=c99 (system GCC)' > "$out/flags.txt"
printf '%s\n' 'parameter,n,q,pk_bytes,sig_buffer_bytes,signatures,sig_average_bytes,sig_min_bytes,sig_max_bytes' > "$out/inventory.csv"
core=(decompose.c encoding.c fft.c fixpoint.c ntt.c packing.c poly.c polyfix.c polymat.c polyvec.c reduce.c sampler.c sign.c symmetric-shake.c)
for mode in 2 3 5; do
  src="$root/crypto_sign/HAETAE$mode/clean"
  files=()
  for file in "${core[@]}"; do files+=("$src/$file"); done
  gcc -O3 -march=native -std=c99 -I"$src" -I"$root/common" \
    "$root/bench/inventory.c" "${files[@]}" "$root/common/randombytes.c" \
    "$root/common/fips202.c" -o "$out/inventory-$mode" 2> "$out/build-$mode.log"
  "$out/inventory-$mode" >> "$out/inventory.csv"
  gcc -O3 -march=native -std=c99 -I"$src" -I"$root/common" \
    "$root/crypto_sign/sign_bench/HAETAE_PQCgenKAT_sign.c" "$src/kat_sign.c" \
    "${files[@]}" "$root/common/aes.c" "$root/common/sha2.c" \
    "$root/common/rng.c" "$root/common/fips202.c" \
    -o "$out/kat-$mode" 2> "$out/build-kat-$mode.log"
  mkdir "$out/kat-mode$mode"
  (cd "$out/kat-mode$mode"; "../kat-$mode" > run.log 2>&1)
  python3 - "$out/kat-mode$mode" <<'PY'
from pathlib import Path
import sys
files = list(Path(sys.argv[1]).glob('*.rsp'))
assert len(files) == 1, files
counts = [line.strip() for line in files[0].read_text().splitlines() if line.startswith('count = ')]
assert counts == ['count = %d' % i for i in range(100)], counts
print('KAT passed:', sys.argv[1], '(100 records)')
PY
done
python3 "$root/bench/summarize_inventory.py" "$out"
