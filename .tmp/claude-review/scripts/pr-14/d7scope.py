import copy, warnings
warnings.simplefilter('ignore')
import fastjsonschema, jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7, DRAFT201909, DRAFT4
D = {'d7': ('http://json-schema.org/draft-07/schema#', jsonschema.Draft7Validator, DRAFT7),
     '2019': ('https://json-schema.org/draft/2019-09/schema', jsonschema.Draft201909Validator, DRAFT201909),
     'd4': ('http://json-schema.org/draft-04/schema#', jsonschema.Draft4Validator, DRAFT4)}
REMOTE = {'type': 'null'}
for dn, (sv, cls, spec) in D.items():
    idk = 'id' if dn == 'd4' else '$id'
    for target in ('http://example.com/child.json', 'http://example.com/sub/child.json'):
        schema = {'$schema': sv, idk: 'http://example.com/root.json',
                  'properties': {'foo': {idk: 'sub/x.json', '$ref': '#/properties/foo/definitions/a' if dn!='2019' else '#/definitions/a',
                                          'definitions': {'a': {idk: 'child.json', 'type': 'string'}}},
                                 'bar': {'$ref': target}}}
        loaded = []
        def h(u): loaded.append(u); return dict(REMOTE)
        try:
            v = fastjsonschema.compile(copy.deepcopy(schema), handlers={'http': h})
            r = []
            for d in ('x', None):
                try: v({'bar': d}); r.append('valid')
                except fastjsonschema.JsonSchemaException: r.append('invalid')
            f = '/'.join(r) + ' loaded=%s' % loaded
        except Exception as e:
            f = 'ERR ' + type(e).__name__ + ' ' + str(e)[:50]
        reg = Registry(retrieve=lambda u: Resource(contents=dict(REMOTE), specification=spec))
        try:
            val = cls(schema, registry=reg)
            o = '/'.join('valid' if val.is_valid({'bar': d}) else 'invalid' for d in ('x', None))
        except Exception as e:
            o = 'ERR ' + type(e).__name__
        print('%-5s bar->%-36s fjs=%-60s oracle=%s' % (dn, target, f, o))
