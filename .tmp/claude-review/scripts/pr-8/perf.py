import sys, time, itertools, fastjsonschema
mode, n = sys.argv[1], int(sys.argv[2])
if mode == 'distinct':
    keys = ['d%d' % i for i in range(n)]
else:  # all keys map to the same base name
    seps = ['-', '_', '.', ' ', '+', '*', ',', ';']
    keys = []
    for combo in itertools.product(seps, repeat=5):
        keys.append('a' + ''.join(c + 'b' for c in combo))
        if len(keys) == n: break
from urllib.parse import quote
s = {'definitions': {k: {'type': 'integer'} for k in keys},
     'properties': {'p%d' % i: {'$ref': '#/definitions/' + quote(k)} for i, k in enumerate(keys)}}
best = 1e9
for _ in range(3):
    t = time.perf_counter(); fastjsonschema.compile(s); best = min(best, time.perf_counter() - t)
print(mode, n, round(best, 3))
