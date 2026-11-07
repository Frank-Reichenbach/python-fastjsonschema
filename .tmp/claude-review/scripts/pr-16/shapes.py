"""Adversarial shapes: is the schema unchanged after compile()/compile_to_code(), and what code is generated."""
import copy, json, sys
sys.path.insert(0, sys.argv[1])
import fastjsonschema
D7 = 'http://json-schema.org/draft-07/schema#'
def remote(uri):
    return {'$id': uri, 'definitions': {'r': {'type': 'integer'}}, 'properties': {'a': {'$ref': '#/definitions/r'}, 'n': {'$ref': '#'}}}
H = {'http': remote, 'https': remote, 'urn': remote}
shared = {'$ref': '#/definitions/x'}
twice = {'$ref': '#/definitions/x'}
SHAPES = {
 'bool_root': True,
 'bool_nested': {'$schema': D7, 'properties': {'a': False, 'b': {'$ref': '#/properties/a'}}},
 'ref_siblings': {'$schema': D7, 'definitions': {'x': {'type': 'integer'}}, 'properties': {'a': {'$ref': '#/definitions/x', 'type': 'string', 'definitions': {'y': {'$ref': '#'}}}}},
 'recursive': {'$schema': D7, 'type': 'object', 'properties': {'child': {'$ref': '#'}, 'list': {'type': 'array', 'items': {'$ref': '#'}}}},
 'urn_root': {'$schema': D7, '$id': 'urn:example:root', 'definitions': {'x': {'type': 'integer'}}, 'properties': {'a': {'$ref': '#/definitions/x'}, 'b': {'$ref': '#'}}},
 'urn_nested': {'$schema': D7, 'properties': {'p': {'$id': 'urn:ex:n', 'definitions': {'x': {'type': 'string'}}, 'properties': {'v': {'$ref': '#/definitions/x'}, 'w': {'$ref': '#'}}}}},
 'draft04_id': {'$schema': 'http://json-schema.org/draft-04/schema#', 'id': 'http://ex.com/r.json', 'definitions': {'x': {'id': 'x.json', 'type': 'integer'}}, 'properties': {'a': {'$ref': 'x.json'}, 'b': {'$ref': '#/definitions/x'}}},
 'nested_http_ids': {'$schema': D7, '$id': 'http://ex.com/root/', 'definitions': {'f': {'$id': 'folder/', 'definitions': {'i': {'$id': 'int.json', 'type': 'integer'}}, 'items': {'$ref': 'int.json'}}}, 'properties': {'l': {'$ref': 'folder/'}, 'm': {'$ref': 'folder/int.json'}}},
 'braces_quotes': {'$schema': D7, 'definitions': {'{x}': {'type': 'integer'}, "q'\"": {'type': 'string'}, 'a/b~c': {'type': 'null'}}, 'properties': {'{a}': {'$ref': '#/definitions/{x}'}, "'b\"": {'$ref': "#/definitions/q'\""}, 'c': {'$ref': '#/definitions/a~1b~0c'}}},
 'refs_in_data': {'$schema': D7, 'definitions': {'x': {'type': 'integer'}}, 'const': {'$ref': '#/definitions/x'}, 'properties': {'e': {'enum': [{'$ref': 'x'}], 'default': {'$ref': 'y'}}}},
 'all_keywords': {'$schema': D7, '$id': 'http://ex.com/all.json', 'definitions': {'x': {'type': 'integer'}, 's': {'type': 'string'}},
     'properties': {'a': {'$ref': '#/definitions/x'}}, 'patternProperties': {'^p': {'$ref': '#/definitions/x'}},
     'additionalProperties': {'$ref': '#/definitions/x'}, 'dependencies': {'d': {'$ref': '#/definitions/x'}},
     'propertyNames': {'$ref': '#/definitions/s'}, 'not': {'$ref': '#/definitions/s'}, 'if': {'$ref': '#/definitions/x'}, 'then': {'$ref': '#/definitions/x'}, 'else': {'$ref': '#/definitions/x'},
     'contains': {'$ref': '#/definitions/x'}, 'items': [{'$ref': '#/definitions/x'}], 'additionalItems': {'$ref': '#/definitions/x'},
     'anyOf': [{'$ref': '#/definitions/x'}, True], 'oneOf': [{'$ref': '#/definitions/x'}, {'type': 'object'}], 'allOf': [{'$ref': '#/definitions/x'}]},
 'draft2019': {'$schema': 'https://json-schema.org/draft/2019-09/schema', '$id': 'http://ex.com/d19.json', '$defs': {'x': {'type': 'integer'}}, 'dependentSchemas': {'d': {'$ref': '#/$defs/x'}}, 'properties': {'a': {'$ref': '#/$defs/x'}}, 'unevaluatedProperties': {'$ref': '#/$defs/x'}},
 'remote': {'$schema': D7, 'properties': {'a': {'$ref': 'http://ex.com/remote.json'}, 'b': {'$ref': 'urn:ex:remote'}}},
 'shared_twice_in_one': {'$schema': D7, 'definitions': {'x': {'type': 'integer'}}, 'properties': {'a': {'$id': 'http://ex.com/a.json', 'definitions': {'x': {'type': 'string'}}, 'properties': {'v': twice}}, 'b': {'$id': 'http://ex.com/b.json', 'definitions': {'x': {'type': 'null'}}, 'properties': {'v': twice}}}},
 'shared_walked_and_array': {'$schema': D7, '$id': 'http://ex.com/s.json', 'definitions': {'x': {'type': 'integer'}, 'n': {'$id': 'n.json', 'definitions': {'x': {'type': 'string'}}, 'properties': {'v': shared}}}, 'allOf': [shared], 'properties': {'n': {'$ref': 'n.json'}}},
 'nonstring_ref': {'$schema': D7, 'properties': {'a': {'$ref': {'not': 'a string'}}}},
 'empty_ref': {'$schema': D7, 'type': 'object', 'properties': {'a': {'$ref': ''}}},
}
out = {}
for name, schema in SHAPES.items():
    orig = copy.deepcopy(schema)
    res = {}
    for ff in (True, False):
        try:
            res[str(ff)] = fastjsonschema.compile_to_code(schema, handlers=H, fast_fail=ff)
            fastjsonschema.compile(schema, handlers=H, fast_fail=ff)
        except Exception as e:
            res[str(ff)] = 'EXC {}: {}'.format(type(e).__name__, e)
    res['mutated'] = schema != orig
    out[name] = res
    print('{:26} mutated={!s:5} {}'.format(name, res['mutated'], res['True'][:70].replace('\n', ' ') if res['True'].startswith('EXC') else 'ok'))
json.dump(out, open(sys.argv[2], 'w'))
