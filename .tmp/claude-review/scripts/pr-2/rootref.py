import copy, socket, fastjsonschema, jsonschema
# block network so http fetches fail fast and visibly
def nonet(*a, **k): raise OSError('network blocked by test')
socket.create_connection = nonet
for sch in ('http://json-schema.org/draft-07/schema#', 'http://json-schema.org/draft-06/schema#', 'http://json-schema.org/draft-04/schema#'):
    idk = 'id' if 'draft-04' in sch else '$id'
    for rid in ('urn:ex:root', 'urn:ex:root#', 'tag:ex.com,2026:root#', 'http://ex.com/root', 'http://ex.com/root#'):
        s = {'$schema': sch, idk: rid, '$ref': '#/definitions/x', 'definitions': {'x': {'type': 'integer'}}}
        try:
            v = fastjsonschema.compile(copy.deepcopy(s))
            r = []
            for d in (1, 'a'):
                try: v(d); r.append('valid')
                except fastjsonschema.JsonSchemaException: r.append('invalid')
            r = str(r)
        except Exception as e:
            r = 'COMPILE %s: %s' % (type(e).__name__, str(e)[:70])
        js = []
        for d in (1, 'a'):
            try: js.append('valid' if jsonschema.validators.validator_for(s)(s).is_valid(d) else 'invalid')
            except Exception as e: js.append(type(e).__name__)
        print('%-8s %-24s fjs=%-60s js=%s' % (sch.split('/')[-2], rid, r, js))
