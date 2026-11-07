import fastjsonschema, hashlib, re
keys = ['a', 'A', 'a-2', 'a_2', 'a.2', 'A-2', '-', '', 'ä', 'ö', 'x/y', 'x_y', 'X~y']
from urllib.parse import quote
ptr = lambda k: '#/definitions/' + quote(k.replace('~','~0').replace('/','~1'))
s = {'$id': 'http://example.com/root.json', 'definitions': {k: {'const': i, 'properties': {'n': {'$ref': ptr(keys[(i+1) % len(keys)])}}} for i, k in enumerate(keys)},
     'properties': {'p%d' % i: {'$ref': ptr(k)} for i, k in enumerate(keys)}}
code = fastjsonschema.compile_to_code(s, fast_fail=False)
print(hashlib.sha1(code.encode()).hexdigest(), sorted(re.findall(r'^def (\w+)', code, re.M)))
