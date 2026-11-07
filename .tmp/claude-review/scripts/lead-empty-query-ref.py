import fastjsonschema as f
for s in [{'definitions':{'ab':{'type':'integer'}},'properties':{'x':{'$ref':'?#/definitions/ab'},'y':{'$ref':'#/definitions/ab'}}},
          {'type':'object','definitions':{'ab':{'type':'integer'}},'properties':{'x':{'$ref':'?#/definitions/ab'}}}]:
    try: v=f.compile(s); print(v({'x':1}))
    except Exception as e: print(type(e).__name__, e)
