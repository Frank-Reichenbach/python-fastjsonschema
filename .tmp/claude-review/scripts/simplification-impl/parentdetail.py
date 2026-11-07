"""parentdetail.py BRANCH PARENT MODULE [drop_import drop_test ...]: per-test results of BRANCH's MODULE on PARENT's code"""
import subprocess, sys, os, re, collections
S = '/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad'
V = S + '/impl/verify'; G = '/Users/frankreichenbach/Development/private/python-fastjsonschema'
b, p, m, *drops = sys.argv[1:]
subprocess.run(['git', 'checkout', '-q', '-f', '--detach', p], cwd=V, check=True)
src = subprocess.run(['git', '-C', G, 'show', b + ':tests/' + m], capture_output=True, text=True, check=True).stdout
for d in drops:
    if d.startswith('import:'):
        src = '\n'.join(l for l in src.splitlines() if d[7:] not in l or not l.startswith('from')) + '\n'
    elif d.startswith('test:'):
        name = d[5:]
        i = src.index('def ' + name + '(')
        start = src.rfind('\n\n\n', 0, i) + 3; end = src.find('\n\n\n', i)
        src = src[:start] + src[end + 3 if end >= 0 else len(src):]
open(V + '/tests/' + m, 'w').write(src)
r = subprocess.run([S + '/impl/rt.sh', V, '--timeout', '20', '-rA', 'tests/' + m], capture_output=True, text=True)
res = collections.defaultdict(collections.Counter)
for l in r.stdout.splitlines():
    mm = re.match(r'^(PASSED|FAILED|ERROR) tests/\S+::(\w+)', l)
    if mm: res[mm.group(2)][mm.group(1)] += 1
os.remove(V + '/tests/' + m)
print('== %s (%s) on %s' % (m, b, p), r.stdout.strip().splitlines()[-1])
for t, c in res.items():
    print('   %-75s %s' % (t, ' '.join('%s=%d' % kv for kv in sorted(c.items()))))
