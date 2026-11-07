"""What do fastjsonschema (PYTHONPATH) and jsonschema load for a $ref inside a handler-loaded document?"""
import sys, json
import fastjsonschema
import jsonschema, referencing
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7, DRAFT201909

CASES = [
    # (name, root $ref, fetch uri -> document, inner $ref)
    ('rel path, $id == path', 'dir/main.json', {'$id': 'dir/main.json'}),
    ('rel path, no $id', 'dir/main.json', {}),
    ('rel path, $id other dir', 'dir/main.json', {'$id': 'other/main.json'}),
    ('http, rel $id', 'http://example.com/a/main.json', {'$id': 'b/main.json'}),
    ('http, abs $id other host', 'http://example.com/a/main.json', {'$id': 'http://other.org/x/main.json'}),
    ('http, no $id', 'http://example.com/a/main.json', {}),
    ('http, nested rel $id', 'http://example.com/a/main.json', None),  # nested
]

def doc(case_doc):
    if case_doc is None:
        return {'properties': {'c': {'$id': 'sub/', 'properties': {'d': {'$ref': 'child.json'}}}}}
    return dict(case_doc, properties={'c': {'$ref': 'child.json'}})

def data(case_doc):
    return {'c': {'d': 1}} if case_doc is None else {'c': 1}

def run_fast(root_ref, d, draft):
    loaded = []
    def handler(uri):
        loaded.append(uri)
        return d if uri == root_ref else {'type': 'integer'}
    try:
        v = fastjsonschema.compile({'$schema': draft, '$ref': root_ref} if draft else {'$ref': root_ref}, handlers={'http': handler, '': handler})
        v(data(d if d.get('properties', {}).get('c', {}).get('$id') is None else None))
    except Exception as e:
        loaded.append('ERR %s: %s' % (type(e).__name__, str(e)[:60]))
    return loaded[1:]

def run_js(root_ref, d, spec):
    loaded = []
    def retrieve(uri):
        loaded.append(uri)
        return Resource.from_contents(d if uri == root_ref else {'type': 'integer'}, default_specification=spec)
    reg = Registry(retrieve=retrieve)
    cls = jsonschema.Draft7Validator if spec is DRAFT7 else jsonschema.Draft201909Validator
    try:
        cls({'$ref': root_ref}, registry=reg).validate({'c': 1} if 'sub/' not in json.dumps(d) else {'c': {'d': 1}})
    except Exception as e:
        loaded.append('ERR %s: %s' % (type(e).__name__, str(e)[:60]))
    return loaded[1:]

for name, root_ref, case_doc in CASES:
    import copy; d0 = doc(case_doc); d = copy.deepcopy(d0)
    f7 = run_fast(root_ref, copy.deepcopy(d0), 'http://json-schema.org/draft-07/schema#')
    j7 = run_js(root_ref, copy.deepcopy(d0), DRAFT7)
    j19 = run_js(root_ref, copy.deepcopy(d0), DRAFT201909)
    print('%-28s fast(d7)=%s | jsonschema d7=%s d2019=%s' % (name, f7, j7, j19))
