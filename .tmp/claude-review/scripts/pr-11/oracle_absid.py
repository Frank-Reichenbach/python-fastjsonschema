import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
loaded=[]
def retrieve(u):
    loaded.append(u)
    if u=='http://a/x.json': return Resource.from_contents({'$schema':'http://json-schema.org/draft-07/schema#','$id':'http://b/y.json','properties':{'c':{'$ref':'child.json'}}})
    return Resource.from_contents({'type':'integer'}, default_specification=DRAFT7)
v=jsonschema.Draft7Validator({'$ref':'http://a/x.json'}, registry=Registry(retrieve=retrieve))
print(v.is_valid({'c':1}), v.is_valid({'c':'x'}), loaded)
