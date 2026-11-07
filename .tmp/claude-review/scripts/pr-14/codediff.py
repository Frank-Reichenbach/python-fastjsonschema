import json, sys, copy, hashlib, glob, os
wt = sys.argv[1]
sys.path.insert(0, wt)
os.chdir(wt)
from tests.json_schema.utils import SCHEMA_HANDLERS
from fastjsonschema import compile_to_code
SV = {'draft4': 'http://json-schema.org/draft-04/schema#', 'draft6': 'http://json-schema.org/draft-06/schema#',
      'draft7': 'http://json-schema.org/draft-07/schema#', 'draft2019-09': 'http://json-schema.org/draft-2019-09/schema'}
out = {}
for d, sv in SV.items():
    for f in sorted(glob.glob('JSON-Schema-Test-Suite/tests/%s/**/*.json' % d, recursive=True)):
        for i, c in enumerate(json.load(open(f))):
            s = copy.deepcopy(c['schema'])
            if isinstance(s, dict): s.setdefault('$schema', sv)
            try: code = compile_to_code(s, handlers=SCHEMA_HANDLERS)
            except Exception as e: code = 'EXC ' + type(e).__name__ + str(e)
            out['%s:%s:%s' % (d, os.path.basename(f), c['description'])] = hashlib.md5(code.encode()).hexdigest()
json.dump(out, open(sys.argv[2], 'w'))
