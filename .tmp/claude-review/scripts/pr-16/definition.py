import sys
sys.path.insert(0, sys.argv[1])
import fastjsonschema
schema = {'$id': 'http://ex.com/r.json', 'definitions': {'x': {'type': 'object', 'properties': {'y': {'$ref': '#/definitions/y'}}}, 'y': {'type': 'integer'}},
          'type': 'object', 'properties': {'a': {'$ref': '#/definitions/x'}, 'b': {'type': 'string'}}}
try:
    fastjsonschema.compile(schema)(1)
except fastjsonschema.JsonSchemaValueException as e:
    print(e.definition)
