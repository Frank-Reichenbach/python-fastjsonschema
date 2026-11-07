import re, fastjsonschema
def h(uri): return {'type': 'integer'}
cases = [
 {'$id': 'schemas/item.json', 'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}, 'me': {'$ref': '#'}, 'me2': {'$ref': 'item.json'}, 'o': {'$ref': 'other.json'}}},
 {'$id': 'schemas/item.json#', 'properties': {'me': {'$ref': '#'}}},
 {'properties': {'p': {'$id': 'schemas/node.json', 'properties': {'q': {'$ref': '#'}, 'r': {'$ref': 'node.json'}}}}},
 {'$id': 'a/b/root.json', 'definitions': {'n': {'$id': 'c/node.json', 'properties': {'s': {'$ref': '#'}}}}, 'properties': {'n': {'$ref': 'c/node.json'}, 'n2': {'$ref': '#/definitions/n'}}},
]
for s in cases:
    code = fastjsonschema.compile_to_code(s, handlers={'': h})
    print(sorted(set(re.findall(r'^def (\w+)', code, re.M))))
    ns = {}; exec(code, ns)
