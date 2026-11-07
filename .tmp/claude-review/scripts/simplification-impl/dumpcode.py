"""dumpcode.py OUT: compile_to_code for every schema of the official suite (with the suite's handlers)"""
import json, sys, glob, os, hashlib
sys.path.insert(0, os.getcwd())
from tests.json_schema.utils import SCHEMA_HANDLERS
import fastjsonschema
root = os.path.join(os.getcwd(), 'JSON-Schema-Test-Suite', 'tests')
drafts = {'draft4': 'http://json-schema.org/draft-04/schema', 'draft6': 'http://json-schema.org/draft-06/schema',
          'draft7': 'http://json-schema.org/draft-07/schema', 'draft2019-09': 'https://json-schema.org/draft/2019-09/schema'}
out = {}
for d, uri in drafts.items():
    for f in sorted(glob.glob(os.path.join(root, d, '**', '*.json'), recursive=True)):
        for i, case in enumerate(json.load(open(f))):
            schema = case['schema']
            if isinstance(schema, dict):
                schema.setdefault('$schema', uri)
            key = '%s/%s#%d %s' % (d, os.path.relpath(f, os.path.join(root, d)), i, case['description'])
            try:
                code = fastjsonschema.compile_to_code(schema, handlers=SCHEMA_HANDLERS)
                code = code.split('\n', 1)[1]  # drop VERSION line
                out[key] = hashlib.sha1(code.encode()).hexdigest()
            except Exception as e:
                out[key] = 'EXC ' + type(e).__name__
json.dump(out, open(sys.argv[1], 'w'), indent=0)
print(len(out))
