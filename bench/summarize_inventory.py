"""Write the paper-size gate report; never imply timing has run."""
import csv
from pathlib import Path
import sys

out = Path(sys.argv[1])
with (out / 'inventory.csv').open(newline='') as handle:
    rows = list(csv.DictReader(handle))
assert len(rows) == 3
paper = [1463, 2337, 2908]
lines = [
    '# HAETAE inventory: PAUSED (paper signature-size mismatch)', '',
    'Cloud run validates the inventory workflow only. No performance measurements have been run.', '',
    '- Code commit: `' + (out / 'code-commit.txt').read_text().strip() + '`',
    '- CPU: ' + (out / 'cpu.txt').read_text().strip(),
    '- GCC: ' + (out / 'gcc.txt').read_text().splitlines()[0],
    '- Flags: `' + (out / 'flags.txt').read_text().strip() + '`',
    '- Version: README identifies HAETAE v1.1.2, upstream `743c31d` (2026-02-05).',
    '- Implementation: clean only; HAETAE AVX2 does not exist in this checkout.',
    '- Messages: 32 bytes; empty context; unchanged public randomized signer.', '',
    'Timing columns use kilocycles when measured. `not run` means the size gate stopped timing; `--` means no AVX2 implementation.', '',
    '| Parameter | q | pk | sig (mean) | ref KeyGen | ref Sign | ref Verify | AVX2 KeyGen | AVX2 Sign | AVX2 Verify |',
    '|---|---:|---:|---:|---|---|---|---|---|---|',
]
for row in rows:
    lines.append('| {parameter} | {q} | {pk_bytes} | {sig_average_bytes} | not run | not run | not run | -- | -- | -- |'.format(**row))
lines.extend(['', '| Parameter | n | sig buffer max | signatures | min | max | paper mean | measured minus paper |',
              '|---|---:|---:|---:|---:|---:|---:|---:|'])
for row, expected in zip(rows, paper):
    assert row['signatures'] == '10000'
    lines.append('| {parameter} | {n} | {sig_buffer_bytes} | {signatures} | {sig_min_bytes} | {sig_max_bytes} | '.format(**row) +
                 '%d | %+.6f |' % (expected, float(row['sig_average_bytes']) - expected))
lines.extend(['', 'The three q and pk values match the supplied table. Signature means do not: the repository API returns fixed-length padded signatures (1474/2349/2948 bytes), whereas the paper table lists 1463/2337/2908 bytes. The table does not identify a paper/version, so exact version equivalence is unconfirmed.', '',
              'Each mode completed the existing KAT generator (exit 0; 100 records), plus 10,000 public-API signatures verified and a modified message rejected. No upstream golden KAT reference is supplied. No source changes were needed.', '',
              'Stopped under the requested size-mismatch rule. Await confirmation before timer import, performance timing, and the complete run.sh/bench.csv delivery.'])
(out / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
