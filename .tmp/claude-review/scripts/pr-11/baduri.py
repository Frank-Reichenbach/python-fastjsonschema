import fastjsonschema
try: print(' ', fastjsonschema.compile({'$id':'http://e/s.json','x-note':{'$ref':'http://[bad'}})({}))
except Exception as e: print(' ', type(e).__name__, e)
