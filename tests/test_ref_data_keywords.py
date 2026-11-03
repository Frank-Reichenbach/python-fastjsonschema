import copy

import pytest

from fastjsonschema import JsonSchemaException, compile


POINTER = {'$ref': '#/definitions/x'}


@pytest.mark.parametrize('schema', [
    {'properties': {'p': {'const': POINTER}}},
    {'$id': 'http://example.com/root.json', 'definitions': {'x': {'type': 'string'}}, 'properties': {'p': {'const': POINTER}}},
    {'properties': {'p': {'enum': [POINTER]}}},
    {'properties': {'p': {'type': 'object', 'examples': [POINTER]}}},
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_object_in_data_keyword_is_data(schema, fast_fail):
    validator = compile(copy.deepcopy(schema), fast_fail=fast_fail)

    assert validator({'p': copy.deepcopy(POINTER)}) == {'p': POINTER}


def test_ref_object_as_default_is_inserted_unchanged():
    validator = compile({
        '$id': 'http://example.com/root.json',
        'properties': {'p': {'default': copy.deepcopy(POINTER)}},
    })

    assert validator({}) == {'p': POINTER}


def test_invalid_uri_in_default_ref_object_is_data():
    validator = compile({
        '$id': 'http://example.com/root.json',
        'properties': {'p': {'default': {'$ref': 'http://[bad'}}},
    }, use_default=False)

    assert validator({}) == {}


@pytest.mark.parametrize('keyword', ['const', 'default'])
def test_id_in_data_keyword_is_data(keyword):
    validator = compile({
        'definitions': {'s': {'$id': 'http://example.com/string.json', 'type': 'string'}},
        'properties': {
            'q': {keyword: {'$id': 'http://example.com/string.json', 'type': 'integer'}},
            'v': {'$ref': 'http://example.com/string.json'},
        },
    })

    assert validator({'v': 'a'})['v'] == 'a'
    with pytest.raises(JsonSchemaException):
        validator({'v': 1})


@pytest.mark.parametrize('name', ['const', 'default', 'enum', 'examples'])
def test_property_named_like_data_keyword_is_schema(name):
    validator = compile({
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {
            '$id': 'http://example.com/node.json',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {name: {'$ref': '#/definitions/x'}},
        }},
    })

    assert validator({'p': {name: 1}}) == {'p': {name: 1}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {name: 'a'}})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_error_definition_expands_refs_of_properties_named_like_data_keywords(fast_fail):
    validator = compile({
        'definitions': {'x': {'type': 'string'}},
        'properties': {'const': {'$ref': '#/definitions/x'}, 'v': {'enum': [POINTER]}},
        'required': ['z'],
    }, fast_fail=fast_fail)

    with pytest.raises(JsonSchemaException) as exc:
        validator({})
    error = exc.value if fast_fail else exc.value.errors[0]
    assert error.definition['properties'] == {'const': {'type': 'string'}, 'v': {'enum': [POINTER]}}

