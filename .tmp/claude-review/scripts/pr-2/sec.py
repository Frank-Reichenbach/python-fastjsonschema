import fastjsonschema, copy
evil = 'urn:x:\'"\\\n{0}{__import__}"""; raise SystemExit(7) #'
s = {'properties': {'p': {'$id': evil, 'definitions': {'d': {'type': 'integer'}}, 'properties': {'v': {'$ref': '#/definitions/d'}, 's': {'$ref': '#'}}}}}
for ff in (True, False):
    code = fastjsonschema.compile_to_code(copy.deepcopy(s), fast_fail=ff)
    ns = {}; exec(code, ns)
    v = fastjsonschema.compile(copy.deepcopy(s), fast_fail=ff)
    for d in ({'p': {'v': 1, 's': {'v': 2}}}, {'p': {'s': {'v': 'x'}}}):
        try: v(d); print(ff, 'valid')
        except fastjsonschema.JsonSchemaException as e: print(ff, 'invalid', getattr(e, 'message', e))
