import fastjsonschema, traceback
for s in [{'properties': {'root': {'$ref': '?#'}}},
          {'type':'object','properties': {'root': {'$ref': '?#'}}},
          {'definitions':{'ab':{'type':'integer'}},'type':'object','properties': {'x': {'$ref': '?#/definitions/ab'}}},
          {'definitions':{'ab':{'type':'integer'}},'required':['x'],'properties': {'x': {'$ref': '?#/definitions/ab'}}}]:
    try:
        v = fastjsonschema.compile(s); print('ok', v({'x':1}) if 'definitions' in s else v({}))
    except Exception as e:
        print(type(e).__name__, e)
