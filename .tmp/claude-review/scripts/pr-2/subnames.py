import re, fastjsonschema
s = {'properties': {'p': {'$id': 'urn:example:item', 'definitions': {'x': {'type': 'integer'}}, 'properties': {'v': {'$ref': '#/definitions/x'}, 's': {'$ref': '#'}}}}}
print(re.findall(r'^def (\w+)', fastjsonschema.compile_to_code(s), re.M))
