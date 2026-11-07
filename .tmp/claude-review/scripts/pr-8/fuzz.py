import random, re, sys
from urllib.parse import quote
import fastjsonschema
from fastjsonschema import JsonSchemaException
ALPH = ['a', 'A', '-', '_', '2', '3', '~', '/', ' ', 'ä', '.', '"']
def ptr(key, base='#/definitions/'):
    return base + quote(key.replace('~', '~0').replace('/', '~1'))
rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
bad = 0
for it in range(3000):
    n = rng.randint(2, 7)
    keys = set()
    while len(keys) < n:
        keys.add(''.join(rng.choice(ALPH) for _ in range(rng.randint(0, 4))))
    keys = sorted(keys, key=lambda _: rng.random())
    defs = {}
    for i, k in enumerate(keys):
        d = {'const': i}
        # chain: some definitions reference another one through allOf
        if rng.random() < 0.3 and i > 0:
            j = rng.randrange(i)
            d = {'allOf': [{'$ref': ptr(keys[j])}], 'const': i} if False else {'properties': {'r': {'$ref': ptr(keys[j])}}, 'const': i} if False else d
        defs[k] = d
    props = {'p%d' % i: {'$ref': ptr(k)} for i, k in enumerate(keys)}
    # add a ref equal to root sometimes, under weird spellings
    if rng.random() < 0.3:
        props['root'] = {'$ref': rng.choice(['#', '?#', '#/', ''])}
    schema = {'definitions': defs, 'properties': props, 'type': 'object'}
    if rng.random() < 0.3:
        schema['$id'] = 'http://example.com/' + rng.choice(['a-b.json', 'a_b.json', 'A.json', 'x'])
    ff = rng.random() < 0.5
    try:
        code = fastjsonschema.compile_to_code(schema, fast_fail=ff)
        v = fastjsonschema.compile(schema, fast_fail=ff)
    except Exception as e:
        print('compile error', type(e).__name__, e, schema); bad += 1; continue
    names = re.findall(r'^def (\w+)\(', code, re.M)
    if len(names) != len(set(names)):
        print('DUP', names, schema); bad += 1
    for i, k in enumerate(keys):
        try:
            v({'p%d' % i: i})
        except Exception as e:
            print('FALSE REJECT', repr(k), type(e).__name__, e, schema); bad += 1; break
        j = (i + 1) % n
        try:
            v({'p%d' % i: j}); print('FALSE ACCEPT', repr(k), schema); bad += 1; break
        except JsonSchemaException:
            pass
    try:
        v('notobject'); print('ROOT REPLACED', schema); bad += 1
    except JsonSchemaException:
        pass
print('bad', bad)
