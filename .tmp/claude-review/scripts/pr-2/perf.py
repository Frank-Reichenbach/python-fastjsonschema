import timeit, copy, fastjsonschema
def mk(i):
    s = {'definitions': {'d%d' % k: {'type': 'integer'} for k in range(200)},
         'properties': {'p%d' % k: {'$ref': '#/definitions/d%d' % k} for k in range(200)}}
    if i: s['$id'] = i
    return s
for i in ('', 'http://e.com/r', 'urn:ex:r'):
    s = mk(i)
    t = min(timeit.repeat(lambda: fastjsonschema.compile(copy.deepcopy(s)), number=5, repeat=5)) / 5
    print('%-16r compile %.1f ms' % (i, t * 1000))
