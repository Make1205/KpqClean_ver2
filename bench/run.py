#!/usr/bin/env python3
"""Offline benchmark orchestration; Python >=3.8 standard library only."""
import csv
import datetime
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
os.chdir(str(ROOT))
os.environ.update(LANG='C', LC_ALL='C')


def run(args, cwd=ROOT):
    return subprocess.run([str(a) for a in args], cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')


def main():
    if sys.version_info < (3, 8):
        raise RuntimeError('Python 3.8 or later required')
    quick = os.environ.get('QUICK', '0')
    if quick not in ('0', '1'):
        raise RuntimeError('QUICK must be 0 or 1')
    quick = quick == '1'
    nt, nc, nl = (11, 100, 100) if quick else (10001, 30000, 10000)
    kind = 'QUICK' if quick else 'FULL'
    out = ROOT / 'bench/results' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + '-' + kind.lower())
    out.mkdir(parents=True)
    print(str(out), flush=True)
    commit = run(['git', 'rev-parse', 'HEAD']).strip()
    # Refuse local algorithm modifications, including staged modifications.
    run(['git', 'diff', 'HEAD', '--exit-code', '--', 'crypto_sign/HAETAE2', 'crypto_sign/HAETAE3', 'crypto_sign/HAETAE5', 'common'])
    (out / 'code-commit.txt').write_text(commit + '\n')
    (out / 'git-status.txt').write_text(run(['git', 'status', '--short']))
    gcc = run(['gcc', '--version'])
    (out / 'gcc.txt').write_text(gcc)
    cpuinfo = Path('/proc/cpuinfo').read_text()
    cpu = next((s.split(':', 1)[1].strip() for s in cpuinfo.splitlines() if s.startswith('model name')), 'unknown')
    (out / 'cpu.txt').write_text(cpuinfo)
    flags = ['-O3', '-march=native', '-std=c99']
    (out / 'flags.txt').write_text(' '.join(flags) + '\n')
    sources = sorted((ROOT / 'bench').glob('*.c')) + sorted((ROOT / 'bench').glob('*.py')) + [ROOT / 'bench/run.sh'] + sorted((ROOT / 'bench/dilithium').glob('*'))
    (out / 'driver-sha256.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(ROOT)) + '\n' for p in sources if p.is_file()))
    core = 'decompose encoding fft fixpoint ntt packing poly polyfix polymat polyvec reduce sampler sign symmetric-shake'.split()
    rows = []
    for mode, paper in ((2, 1463), (3, 2337), (5, 2908)):
        print('mode%d: build, KAT, correctness, lengths, timing (%s)' % (mode, kind), flush=True)
        src = ROOT / ('crypto_sign/HAETAE%d/clean' % mode)
        base = ['gcc'] + flags + ['-I' + str(src), '-I' + str(ROOT / 'common'), '-I' + str(ROOT / 'bench')]
        files = [src / (s + '.c') for s in core]
        commands = [base + [ROOT / 'bench/benchmark.c'] + files + [ROOT / 'common/randombytes.c', ROOT / 'common/fips202.c', ROOT / 'bench/dilithium/cpucycles.c', ROOT / 'bench/dilithium/speed_print.c', '-o', out / ('benchmark-%d' % mode)],
                    base + [ROOT / 'crypto_sign/sign_bench/HAETAE_PQCgenKAT_sign.c', src / 'kat_sign.c'] + files + [ROOT / ('common/' + s + '.c') for s in ('aes', 'sha2', 'rng', 'fips202')] + ['-o', out / ('kat-%d' % mode)]]
        for label, command in zip(('benchmark', 'kat'), commands):
            (out / ('command-%s-%d.txt' % (label, mode))).write_text('\n'.join(str(a) for a in command) + '\n')
            try:
                log = run(command)
            except subprocess.CalledProcessError as exc:
                (out / ('build-%s-%d.txt' % (label, mode))).write_bytes(exc.stdout)
                raise
            (out / ('build-%s-%d.txt' % (label, mode))).write_text(log)
        katdir = out / ('kat-mode%d' % mode)
        katdir.mkdir()
        (katdir / 'run.txt').write_text(run([out / ('kat-%d' % mode)], cwd=katdir))
        rsp = list(katdir.glob('*.rsp'))
        if len(rsp) != 1 or re.findall(r'^count = (\d+)$', rsp[0].read_text(), re.M) != [str(i) for i in range(100)]:
            raise RuntimeError('KAT record validation failed: ' + str(katdir))
        log = run([out / ('benchmark-%d' % mode), nt, nc, nl])
        (out / ('benchmark-%d.txt' % mode)).write_text(log)
        data = next(csv.reader([next(s for s in log.splitlines() if s.startswith('data,'))]))
        medians = re.findall(r'^(KeyGen|Sign|Verify)\nmedian: (\d+) cycles/ticks$', log, re.M)
        if [m[0] for m in medians] != ['KeyGen', 'Sign', 'Verify']:
            raise RuntimeError('missing timing result')
        row = dict(zip(('parameter', 'n', 'q', 'pk_bytes', 'sig_fixed_bytes', 'correctness_signatures', 'length_samples', 'encoded_mean_bytes', 'encoded_max_bytes'), data[1:]))
        row.update(run=kind, paper_mean_bytes=paper, timing_samples=nt, kat_records=100, code_commit=commit,
                   encoded_minus_paper='%.6f' % (float(data[8]) - paper),
                   **{name.lower() + '_kcycles': '%.3f' % (int(value) / 1000) for name, value in medians},
                   avx2_keygen='--', avx2_sign='--', avx2_verify='--')
        rows.append(row)
    with (out / 'bench.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    text = ['# HAETAE benchmark: ' + kind, '',
            '**QUICK: numbers validate output format only; do not use as performance or distribution estimates.**' if quick else 'Full-scale measurement.', '',
            '- Tested commit: `' + commit + '` (driver hashes and working-tree status retained).',
            '- CPU: ' + cpu, '- GCC: ' + gcc.splitlines()[0], '- Flags: `' + ' '.join(flags) + '`.',
            '- HAETAE v1.1.2 clean only, mode2/mode3/mode5; n=256, q=64513; no HAETAE AVX2 in this repository.',
            '- Per mode: KAT 100 records; %d valid signatures verified plus modified-message/signature rejection; %d length samples; %d timed calls per operation.' % (nc, nl, nt),
            '- Messages: 32 bytes, empty context, unchanged randomized public API and OS random source; fresh key every 100 correctness signatures.',
            '- Sign/Verify timing starts with serialized sk/pk; includes unpacking. One warmup per API before each timing group.', '',
            'All timing values below are medians in kilocycles (cycles/ticks divided by 1000).', '',
            '| Parameter | q | pk | sig (repository fixed) | paper mean sig | ref KeyGen | ref Sign | ref Verify | AVX2 KeyGen | AVX2 Sign | AVX2 Verify |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|']
    for r in rows:
        text.append('| {parameter} | {q} | {pk_bytes} | {sig_fixed_bytes} | {paper_mean_bytes} | {keygen_kcycles} | {sign_kcycles} | {verify_kcycles} | -- | -- | -- |'.format(**r))
    text += ['', '| Parameter | length samples | encoded mean | encoded max | paper mean | mean minus paper |', '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        text.append('| {parameter} | {length_samples} | {encoded_mean_bytes} | {encoded_max_bytes} | {paper_mean_bytes} | {encoded_minus_paper} |'.format(**r))
    text += ['', 'Length method (bench driver only): API siglen is fixed. At p=N/8+L*N, read the two serialized offsets. Actual encoded bytes = p+2+BASE_ENC_HB_Z1+sig[p]+BASE_ENC_H+sig[p+1], matching packing.c:pack_sig/unpack_sig. Require every subsequent byte to be zero. This preserves any zero bytes at the end of real encoded data; no heuristic trailing-zero stripping. Signatures remain fixed-length for verification.', '',
             'Timer: the four unchanged pq-crystals/dilithium ref/test files from bba9534a3c5cbef66481cd6518d786e23ae601b5. Each call has start/end cpucycles reads; intervals are accumulated into N+1 synthetic timestamps so unchanged speed_print differences exactly N samples, subtracts its calibrated overhead, and computes the median. Default RDTSC ticks are used (not RDPMC, no system settings changed); TSC ticks are not necessarily actual core cycles. Branch dispatch is inside the timed interval. No CPU pinning or frequency changes.', '',
             'KAT means the unchanged repository generator exited successfully, performed its sign/open checks, and emitted counts 0..99; no golden vectors are supplied. Paper means 1463/2337/2908 are the supplied comparison values; exact paper/version equivalence remains unconfirmed.', '',
             'Reproduce full scale: `LANG=C bash bench/run.sh` (QUICK unset). Offline, no sudo; requires bash, Python >=3.8 standard library, GCC, Git, Linux /proc and x86-64 RDTSC. Generated KAT vectors include test secret keys and stay local.']
    (out / 'SUMMARY.md').write_text('\n'.join(text) + '\n')
    print('PASS: ' + str(out / 'SUMMARY.md'), flush=True)


if __name__ == '__main__':
    main()
