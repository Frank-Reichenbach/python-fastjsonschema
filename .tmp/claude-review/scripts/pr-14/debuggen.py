import json, sys, copy
sys.path.insert(0, '.')
from tests.json_schema.utils import SCHEMA_HANDLERS
from fastjsonschema import RefResolver, _get_code_generator_class, compile_to_code
cases = json.load(open('JSON-Schema-Test-Suite/tests/draft7/ref.json'))
c = [c for c in cases if c['description'].startswith('$ref prevents a sibling $id')][0]
schema = c['schema']
r = RefResolver.from_schema(schema, handlers=SCHEMA_HANDLERS)
dbg = _get_code_generator_class('http://json-schema.org/draft-07/schema#')(schema, resolver=r).func_code
s2 = dict(copy.deepcopy(schema), **{'$schema': 'http://json-schema.org/draft-07/schema#'})
real = compile_to_code(s2, handlers=SCHEMA_HANDLERS)
import re
print('debug funcs:', re.findall(r'def (\w+)', dbg))
print('real  funcs:', re.findall(r'def (\w+)', real))
