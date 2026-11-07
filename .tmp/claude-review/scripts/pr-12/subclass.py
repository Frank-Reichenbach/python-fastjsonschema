import contextlib
from fastjsonschema import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
class MyResolver(RefResolver):
    @contextlib.contextmanager
    def resolving(self, ref):
        with super().resolving(ref) as s:
            yield s
schema = {'definitions': {'a': {'type': 'integer'}}, 'properties': {'p': {'$ref': '#/definitions/a'}}}
try:
    print(CodeGeneratorDraft07(schema, resolver=MyResolver.from_schema(schema, store={})).func_code.count('def '), 'functions')
except Exception as e: print(type(e).__name__, e)
