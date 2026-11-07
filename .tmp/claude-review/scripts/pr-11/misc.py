import fastjsonschema, types, collections, copy
def run(label, f):
    try: print(' ', label, '->', f())
    except Exception as e: print(' ', label, '->', type(e).__name__, str(e)[:80])
# handler returning booleans
run('bool True', lambda: fastjsonschema.compile({'properties':{'a':{'$ref':'http://e/t.json'},'b':{'$ref':'http://e/f.json'}}}, handlers={'http': lambda u: u.endswith('t.json')})({'a':1}))
run('bool False', lambda: fastjsonschema.compile({'properties':{'a':{'$ref':'http://e/t.json'},'b':{'$ref':'http://e/f.json'}}}, handlers={'http': lambda u: u.endswith('t.json')})({'b':1}))
# mappingproxy
run('mappingproxy', lambda: fastjsonschema.compile({'$ref':'http://e/m.json'}, handlers={'http': lambda u: types.MappingProxyType({'type':'integer'})})(1))
# OrderedDict
run('OrderedDict', lambda: fastjsonschema.compile({'$ref':'http://e/m.json'}, handlers={'http': lambda u: collections.OrderedDict(type='integer')})(1))
# handler returns list / None
run('list', lambda: fastjsonschema.compile({'$ref':'http://e/m.json'}, handlers={'http': lambda u: [1]})(1))
run('None', lambda: fastjsonschema.compile({'$ref':'http://e/m.json'}, handlers={'http': lambda u: None})(1))
# invalid uri in unknown keyword, main schema with $id
run('bad uri x-note main $id', lambda: fastjsonschema.compile({'$id':'http://e/s.json','x-note':{'$ref':'http://[bad'}})({}))
run('bad uri x-note main no id', lambda: fastjsonschema.compile({'x-note':{'$ref':'http://[bad'}})({}))
run('used bad uri main $id', lambda: fastjsonschema.compile({'$id':'http://e/s.json','properties':{'p':{'$ref':'http://[bad'}}}))
run('used bad uri main $id ff=False', lambda: fastjsonschema.compile({'$id':'http://e/s.json','properties':{'p':{'$ref':'http://[bad'}}}, fast_fail=False))
run('used bad uri in handler doc', lambda: fastjsonschema.compile({'$ref':'http://e/d.json'}, handlers={'http': lambda u: {'properties':{'p':{'$ref':'http://[bad'}}}}))
# compile_to_code with handler doc nested id
DOC = {"$id": "http://example.com/doc.json","definitions": {"x": {"type": "string"}},
 "properties": {"p": {"$id": "http://example.com/node.json","definitions": {"x": {"type": "integer"}},"properties": {"v": {"$ref": "#/definitions/x"}}}}}
def ctc():
    code = fastjsonschema.compile_to_code({'$ref':'http://example.com/doc.json'}, handlers={'http': lambda u: DOC})
    g={}; exec(code, g); fn=[v for k,v in g.items() if k.startswith('validate')][-1]
    return [k for k in g if k.startswith('validate')], g['validate']({'p':{'v':1}}) if 'validate' in g else None
run('compile_to_code', ctc)
# handler result unchanged
d0 = copy.deepcopy(DOC); fastjsonschema.compile({'$ref':'http://example.com/doc.json'}, handlers={'http': lambda u: DOC}); print('  DOC unchanged', d0 == DOC)
# error definition for $ref in loaded doc
def errdef():
    v = fastjsonschema.compile({'$ref':'http://example.com/doc.json'}, handlers={'http': lambda u: DOC})
    try: v({'p': {'v':'a'}})
    except fastjsonschema.JsonSchemaValueException as e: return e.name, e.rule, e.definition
run('err', errdef)
