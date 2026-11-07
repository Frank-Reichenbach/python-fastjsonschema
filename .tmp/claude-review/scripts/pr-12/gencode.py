import sys, json, copy, glob, os, hashlib, threading
wt, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, wt)
sys.path.insert(0, os.path.join(wt, 'tests'))
import fastjsonschema
from json_schema.utils import SCHEMA_HANDLERS
root = '/Users/frankreichenbach/Development/private/python-fastjsonschema/JSON-Schema-Test-Suite/tests'
res = {}
schemas = []
for d, ver in [('draft4', 'http://json-schema.org/draft-04/schema#'), ('draft6', 'http://json-schema.org/draft-06/schema#'), ('draft7', 'http://json-schema.org/draft-07/schema#'), ('draft2019-09', 'https://json-schema.org/draft/2019-09/schema')]:
    for f in sorted(glob.glob(f'{root}/{d}/**/*.json', recursive=True)):
        for i, case in enumerate(json.load(open(f))):
            s = case['schema']
            if isinstance(s, dict) and '$schema' not in s:
                s = dict(s, **{'$schema': ver})
            schemas.append((f'{os.path.relpath(f, root)}#{i}', s))
# repo examples
for f in sorted(glob.glob(os.path.join(wt, 'tests/examples/**/*.json'), recursive=True)):
    schemas.append((os.path.relpath(f, wt), json.load(open(f))))
for key, s in schemas:
    for ff in (True, False):
        r = []
        def go():
            try:
                r.append(fastjsonschema.compile_to_code(copy.deepcopy(s), handlers=SCHEMA_HANDLERS, fast_fail=ff))
            except Exception as e:
                r.append('EXC ' + type(e).__name__ + ': ' + str(e)[:100])
        t = threading.Thread(target=go, daemon=True); t.start(); t.join(10)
        res[f'{key}|{ff}'] = r[0] if r else 'HANG'
json.dump(res, open(out, 'w'))
print(len(res))
