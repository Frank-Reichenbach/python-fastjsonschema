"""port.py TARGET C1[:nojoin] C2 ...  — master + code diffs of Ci (fuzzy patch), tests file of TARGET, run TARGET's new tests."""
import subprocess, sys, os, glob
S = os.path.dirname(os.path.abspath(__file__)) + '/..'
W = S + '/simp/wt'; G = '/Users/frankreichenbach/Development/private/python-fastjsonschema/.git'
PY = S + '/venv/bin/python'
def sh(*a, **k): return subprocess.run(a, cwd=W, capture_output=True, text=True, **k)
target, commits = sys.argv[1], sys.argv[2:]
sh('git', 'checkout', '-q', '-f', 'master', '--', 'fastjsonschema', 'tests')
for c in commits:
    c, _, mode = c.partition(':')
    diff = subprocess.run(['git', '--git-dir', G, 'show', c, '--format=', '--', 'fastjsonschema/'], capture_output=True, text=True).stdout
    if mode == 'nojoin': diff = diff.replace('join_uri(', 'urlparse.urljoin(')
    r = sh('patch', '-p1', '-F3', '--no-backup-if-mismatch', '-s', input=diff)
    for rej in glob.glob(W + '/fastjsonschema/*.rej'):
        print('  REJECT in', c, open(rej).read()[:300].replace('\n', '\n    ')); os.remove(rej)
open(W + '/tests/test_integration.py', 'w').write(subprocess.run(['git', '--git-dir', G, 'show', target + ':tests/test_integration.py'], capture_output=True, text=True).stdout)
names = open(S + '/simp/tests-%s.txt' % target).read().split()
try:
    r = sh('timeout', '60', PY, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--benchmark-skip', 'tests/test_integration.py', '-k', ' or '.join(names), env={**os.environ, 'PYTHONPATH': W}, timeout=90)
    lines = [l.split(' - ')[0] for l in r.stdout.splitlines() if l.startswith(('FAILED', 'ERROR')) or ' passed' in l or ' failed' in l]
    print('\n'.join('  ' + l for l in lines) or '  (timeout/hang) rc=%s' % r.returncode)
except subprocess.TimeoutExpired:
    print('  HANG')
