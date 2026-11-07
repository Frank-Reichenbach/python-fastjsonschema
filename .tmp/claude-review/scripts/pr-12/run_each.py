import subprocess, sys, os
wt, testdir, kexpr = sys.argv[1], sys.argv[2], sys.argv[3]
py = sys.executable
env = dict(os.environ, PYTHONPATH=wt)
out = subprocess.run([py, '-m', 'pytest', '--collect-only', '-q', '-p', 'no:cacheprovider', 'tests/test_integration.py', '-k', kexpr], cwd=testdir, env=env, capture_output=True, text=True).stdout.split('\n')
ids = [i for i in out if '::' in i]
for i in ids:
    try:
        r = subprocess.run([py, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--benchmark-skip', i], cwd=testdir, env=env, capture_output=True, text=True, timeout=15)
        res = 'PASS' if r.returncode == 0 else 'FAIL'
        if res == 'FAIL':
            lines = [l for l in r.stdout.split('\n') if l.startswith('E ')]
            res += ' ' + (lines[0][:160] if lines else r.stdout[-300:])
    except subprocess.TimeoutExpired:
        res = 'TIMEOUT(15s)'
    print(i.split('::')[-1], res)
