import pytest

from fastjsonschema import JsonSchemaDefinitionException, compile


@pytest.mark.parametrize('schema', [
    {'$id': 'http://example.com/a.json', 'x-note': {'$ref': 'http://[bad'}},
    {'$id': 'http://example.com/a.json', 'type': 'object', 'x-note': {'$ref': 'http://[bad'}},
    {'type': 'object', 'x-note': {'$ref': 'http://[bad'}},
])
def test_invalid_uri_in_unknown_keyword_is_ignored(schema):
    assert compile(schema)({}) == {}


def test_invalid_uri_in_a_used_ref_still_fails():
    with pytest.raises(ValueError):
        compile({'$id': 'http://example.com/a.json', 'properties': {'a': {'$ref': 'http://[bad'}}})


def test_unresolvable_ref_in_unknown_keyword_still_fails():
    with pytest.raises(JsonSchemaDefinitionException):
        compile({'type': 'object', 'x-note': {'$ref': '#/nope'}})
