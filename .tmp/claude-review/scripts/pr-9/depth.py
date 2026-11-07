import fastjsonschema, time, copy
for kind in ('properties', 'not', 'x'):
    for n in (240, 260, 600):
        s = {'type': 'integer'}
        for _ in range(n):
            s = {'properties': {'a': s}} if kind == 'properties' else {kind: s}
        try:
            fastjsonschema.compile(s); r = 'ok'
        except Exception as e:
            r = type(e).__name__ + ': ' + str(e)[:60]
        print(kind, n, r)
# compile_to_code + const with $ref
code = None



# perf: many properties
big = {'definitions': {'d%d' % i: {'type': 'object', 'properties': {'p%d' % j: {'type': 'string', 'default': 'x', 'enum': ['x', 'y']} for j in range(30)}} for i in range(200)}, 'properties': {'a%d' % i: {'$ref': '#/definitions/d%d' % i} for i in range(200)}}
t = time.perf_counter()
for _ in range(3): fastjsonschema.compile(copy.deepcopy(big))
print('compile big x3: %.2fs' % (time.perf_counter() - t))
