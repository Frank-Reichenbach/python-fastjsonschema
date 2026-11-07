import fastjsonschema
loaded=[]
DOC={'$id':'http://e/doc.json','properties':{'n':{'$id':'sub/n.json','properties':{'v':{'$ref':'other.json'}}}}}
def h(u):
    loaded.append(u); return DOC if u=='http://e/doc.json' else {'type':'integer'}
v=fastjsonschema.compile({'$ref':'http://e/doc.json#/properties/n'}, handlers={'http':h})
print(' ', v({'v':1}), loaded)
