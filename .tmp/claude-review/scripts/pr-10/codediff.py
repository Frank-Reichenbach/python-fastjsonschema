import json, sys, copy, hashlib
from pathlib import Path
sys.path.insert(0, '.')
from tests.json_schema.utils import SCHEMA_HANDLERS
import fastjsonschema
root = Path('JSON-Schema-Test-Suite/tests')
out = {}
for draft, ver in (('draft4', 'http://json-schema.org/draft-04/schema'), ('draft6', 'http://json-schema.org/draft-06/schema'), ('draft7', 'http://json-schema.org/draft-07/schema')):
    for p in sorted((root / draft).glob('**/*.json')):
        for i, case in enumerate(json.load(p.open())):
            s = copy.deepcopy(case['schema'])
            if isinstance(s, dict): s.setdefault('$schema', ver)
            try: code = fastjsonschema.compile_to_code(s, handlers=SCHEMA_HANDLERS)
            except Exception as e: code = 'ERR ' + type(e).__name__
            out[f"{draft}/{p.relative_to(root/draft)}#{i}"] = hashlib.sha1(code.encode()).hexdigest()
for name in sorted(Path('tests/json_schema/metaschemas').rglob('*.json')):
    s = json.load(name.open())
    try: code = fastjsonschema.compile_to_code(s, handlers=SCHEMA_HANDLERS)
    except Exception as e: code = 'ERR ' + type(e).__name__ + str(e)
    out[str(name)] = hashlib.sha1(code.encode()).hexdigest()
json.dump(out, sys.stdout, indent=0)
