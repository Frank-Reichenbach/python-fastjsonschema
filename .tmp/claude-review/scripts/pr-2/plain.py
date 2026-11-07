import copy, fastjsonschema
D4='http://json-schema.org/draft-04/schema#'; D7='http://json-schema.org/draft-07/schema#'
def t(label, s, datas, **kw):
    try:
        v = fastjsonschema.compile(copy.deepcopy(s), **kw)
        out=[]
        for d in datas:
            try: v(d); out.append('valid')
            except fastjsonschema.JsonSchemaException: out.append('invalid')
        print('%-50s %s' % (label, out))
    except Exception as e:
        print('%-50s COMPILE %s: %s' % (label, type(e).__name__, e))
for rid in ('urn:ex:root', 'urn:ex:root#'):
    s = {'$schema': D7, '$id': rid, 'definitions': {'f': {'$id': '#foo', 'type': 'integer'}}, 'properties': {'a': {'$ref': '#foo'}}}
    t('root %s plain #foo  a=1/a=x' % rid, s, [{'a': 1}, {'a': 'x'}])
s = {'$schema': D4, 'id': 'urn:ex:root', 'definitions': {'f': {'id': '#foo', 'type': 'integer'}}, 'properties': {'a': {'$ref': '#foo'}}}
t('draft4 id urn root plain #foo a=1/a=x', s, [{'a': 1}, {'a': 'x'}])
remote = {'$id': 'urn:ex:r', 'definitions': {'f': {'$id': '#foo', 'type': 'integer'}}, 'properties': {'a': {'$ref': '#foo'}}}
s = {'$schema': D7, 'definitions': {'g': {'$id': '#foo', 'type': 'string'}}, 'properties': {'p': {'$ref': 'urn:ex:r'}, 'q': {'$ref': '#foo'}}}
t('handler urn doc plain #foo vs root #foo', s, [{'p': {'a': 1}, 'q': 'x'}, {'p': {'a': 'x'}}, {'q': 1}], handlers={'urn': lambda u: copy.deepcopy(remote)})
