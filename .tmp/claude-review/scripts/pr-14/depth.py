import fastjsonschema, sys
from fastjsonschema.ref_resolver import MAX_SCHEMA_WALK_DEPTH
def nested(n, key='definitions'):
    s = {'type': 'integer'}
    for _ in range(n):
        s = {key: {'d': s}}
    return s
def first_fail(with_ref, key='definitions', wrap='map'):
    for n in range(1, 400):
        inner = nested(n, key)
        if with_ref:
            schema = {'$ref': '#/x', 'x': {}, key: {'d': inner}}
        else:
            schema = {key: {'d': inner}}
        try:
            fastjsonschema.compile(schema)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            return n, str(e)
        except RecursionError as e:
            return n, 'RecursionError'
    return None
print('limit', MAX_SCHEMA_WALK_DEPTH, 'recursionlimit', sys.getrecursionlimit())
for key in ('definitions', '$defs'):
    print(key, 'with $ref:', first_fail(True, key), ' without:', first_fail(False, key))
# chain of $ref objects each with definitions
def chain(n):
    s = {'type': 'integer'}
    for _ in range(n):
        s = {'$ref': '#/x', 'definitions': {'d': s}}
    return dict(s, x={})
for n in range(1, 400):
    try:
        fastjsonschema.compile(chain(n))
    except fastjsonschema.JsonSchemaDefinitionException as e:
        print('chain of $ref objects fails at', n, e); break
    except RecursionError:
        print('chain RecursionError at', n); break
else:
    print('chain never fails')
