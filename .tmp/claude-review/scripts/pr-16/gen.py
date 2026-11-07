"""Usage: PYTHONPATH=<wt> python gen.py <wt> <out.json>
For every schema of the official suite (4 drafts used by the tests, plus 2020-12 without $schema),
record compile_to_code output for fast_fail True/False, whether the input was mutated,
whether remotes were mutated, and whether a second compilation gives the same code."""
import copy, json, sys
from pathlib import Path
wt = Path(sys.argv[1])
sys.path.insert(0, str(wt))
import fastjsonschema
from tests.json_schema import utils
remotes_before = copy.deepcopy(utils.REMOTES), copy.deepcopy(utils.METASCHEMAS)
DIRS = [('draft4', 'http://json-schema.org/draft-04/schema'), ('draft6', 'http://json-schema.org/draft-06/schema'),
        ('draft7', 'http://json-schema.org/draft-07/schema'), ('draft2019-09', 'http://json-schema.org/draft-2019-09/schema'),
        ('draft2020-12', None)]
out = {}
for d, version in DIRS:
    for path in sorted((wt / 'JSON-Schema-Test-Suite/tests' / d).glob('**/*.json')):
        for idx, case in enumerate(json.loads(path.read_text(encoding='utf-8'))):
            schema = case['schema']
            if isinstance(schema, dict) and version:
                schema.setdefault('$schema', version)
            key = '{}/{}#{}'.format(d, path.relative_to(wt / 'JSON-Schema-Test-Suite/tests' / d), idx)
            orig = copy.deepcopy(schema)
            res = {}
            for ff in (True, False):
                try:
                    res[str(ff)] = fastjsonschema.compile_to_code(schema, handlers=utils.SCHEMA_HANDLERS, fast_fail=ff)
                except Exception as e:
                    res[str(ff)] = 'EXC {}: {}'.format(type(e).__name__, e)
            try:
                again = fastjsonschema.compile_to_code(schema, handlers=utils.SCHEMA_HANDLERS)
            except Exception as e:
                again = 'EXC {}: {}'.format(type(e).__name__, e)
            # compile() too, so that both entry points are checked for mutation
            try:
                fastjsonschema.compile(schema, handlers=utils.SCHEMA_HANDLERS)
            except Exception:
                pass
            res['mutated'] = schema != orig
            res['stable'] = again == res['True']
            out[key] = res
out['__remotes_mutated__'] = (utils.REMOTES, utils.METASCHEMAS) != remotes_before
json.dump(out, open(sys.argv[2], 'w'))
print(len(out) - 1, 'schemas; mutated:', sum(1 for k, v in out.items() if isinstance(v, dict) and v['mutated']),
      'unstable:', sum(1 for k, v in out.items() if isinstance(v, dict) and not v['stable']),
      'remotes mutated:', out['__remotes_mutated__'])
