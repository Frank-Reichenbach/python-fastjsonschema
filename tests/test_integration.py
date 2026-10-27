import copy
from urllib.parse import quote

import pytest

from fastjsonschema import JsonSchemaException, JsonSchemaValueException, compile


definition = {
    'type': 'array',
    'items': [
        {
            'type': 'number',
            'maximum': 10,
            'exclusiveMaximum': True,
        },
        {
            'type': 'string',
            'enum': ['hello', 'world'],
        },
        {
            'type': 'array',
            'minItems': 1,
            'maxItems': 3,
            'items': [
                {'type': 'number'},
                {'type': 'string'},
                {'type': 'boolean'},
            ],
        },
        {
            'type': 'object',
            'required': ['a', 'b'],
            'minProperties': 3,
            'properties': {
                'a': {'type': ['null', 'string']},
                'b': {'type': ['null', 'string']},
                'c': {'type': ['null', 'string'], 'default': 'abc'}
            },
            'additionalProperties': {'type': 'string'},
        },
        {'not': {'type': ['null']}},
        {'oneOf': [
            {'type': 'number', 'multipleOf': 3},
            {'type': 'number', 'multipleOf': 5},
        ]},
    ],
}
@pytest.mark.parametrize('value, expected', [
    (
        [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3],
        [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'c': 'abc', 'd': 'd'}, 42, 3],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'abc', 'd': 'd'}, 42, 3],
    ),
    (
        (9, 'world', (1,), {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3),
        (9, 'world', (1,), {'a': 'a', 'b': 'b', 'c': 'abc', 'd': 'd'}, 42, 3),
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 42, 3],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 42, 3],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5, 'any'],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5, 'any'],
    ),
    (
        [10, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaValueException('data[0] must be smaller than 10', value=10, name='data[0]', definition=definition['items'][0], rule='maximum'),
    ),
    (
        [9, 'xxx', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaValueException('data[1] must be one of [\'hello\', \'world\']', value='xxx', name='data[1]', definition=definition['items'][1], rule='enum'),
    ),
    (
        [9, 'hello', [], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaValueException('data[2] must contain at least 1 items', value=[], name='data[2]', definition=definition['items'][2], rule='minItems'),
    ),
    (
        [9, 'hello', [1, 2, 3], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaValueException('data[2][1] must be string', value=2, name='data[2][1]', definition={'type': 'string'}, rule='type'),
    ),
    (
        [9, 'hello', [1], {'q': 'q', 'x': 'x', 'y': 'y'}, 'str', 5],
        JsonSchemaValueException('data[3] must contain [\'a\', \'b\'] properties', value={'q': 'q', 'x': 'x', 'y': 'y'}, name='data[3]', definition=definition['items'][3], rule='required'),
    ),
    (
        [9, 'hello', [1], {'a': 'a', 'x': 'x', 'y': 'y'}, 'str', 5],
        JsonSchemaValueException('data[3] must contain [\'b\'] properties', value={'a': 'a', 'x': 'x', 'y': 'y'}, name='data[3]', definition=definition['items'][3], rule='required'),
    ),
    (
        [9, 'hello', [1], {}, 'str', 5],
        JsonSchemaValueException('data[3] must contain at least 3 properties', value={}, name='data[3]', definition=definition['items'][3], rule='minProperties'),
    ),
    (
        [9, 'hello', [1], {'a': 'a', 'b': 'b', 'x': 'x'}, None, 5],
        JsonSchemaValueException('data[4] must NOT match a disallowed definition', value=None, name='data[4]', definition=definition['items'][4], rule='not'),
    ),
    (
        [9, 'hello', [1], {'a': 'a', 'b': 'b', 'x': 'x'}, 42, 15],
        JsonSchemaValueException('data[5] must be valid exactly by one definition (2 matches found)', value=15, name='data[5]', definition=definition['items'][5], rule='oneOf'),
    ),
])
def test_integration(asserter, value, expected):
    asserter(definition, value, expected)


def test_any_of_with_patterns(asserter):
    asserter({
        'type': 'object',
        'properties': {
            'hash': {
                'anyOf': [
                    {
                        'type': 'string',
                        'pattern': '^AAA'
                    },
                    {
                        'type': 'string',
                        'pattern': '^BBB'
                    }
                ]
            }
        }
    }, {
        'hash': 'AAAXXX',
    }, {
        'hash': 'AAAXXX',
    })


def test_swap_handlers():
    # Make sure that by swapping resolvers, the schemas do not get cached
    repo1 = {
        "sch://schema": {"type": "array"}
    }
    validator1 = compile({"$ref": "sch://schema"}, handlers={"sch": repo1.__getitem__})
    assert validator1([1, 2, 3]) is not None

    repo2 = {
        "sch://schema": {"type": "string"}
    }
    validator2 = compile({"$ref": "sch://schema"}, handlers={"sch": repo2.__getitem__})
    assert validator2("hello world") is not None


def test_relative_ref_in_remote_schema_is_resolved_once():
    repo = {
        'schemas/main.json': {
            'definitions': {
                'object': {
                    'type': 'object',
                    'properties': {'value': {'$ref': 'main.json#/definitions/string'}},
                },
                'string': {'type': 'string'},
            },
        },
    }

    validator = compile(
        {'$ref': 'schemas/main.json#/definitions/object'},
        handlers={'': repo.__getitem__},
    )

    assert validator({'value': 'ok'}) == {'value': 'ok'}


def definition_pointer(key):
    return '#/definitions/' + quote(key.replace('~', '~0').replace('/', '~1'))


@pytest.mark.parametrize('integer_key, string_key', [
    ('Address', 'address'),
    ('user-id', 'user_id'),
    ('a/b', 'a_b'),
    ('größe', 'grüße'),
    ('id', 'id_'),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_refs_to_definitions_with_same_function_name(integer_key, string_key, fast_fail):
    validator = compile({
        'definitions': {integer_key: {'type': 'integer'}, string_key: {'type': 'string'}},
        'properties': {
            'a': {'$ref': definition_pointer(integer_key)},
            'b': {'$ref': definition_pointer(string_key)},
        },
    }, fast_fail=fast_fail)

    assert validator({'a': 1, 'b': 'x'}) == {'a': 1, 'b': 'x'}
    with pytest.raises(JsonSchemaException):
        validator({'a': 'x'})
    with pytest.raises(JsonSchemaException):
        validator({'b': 1})


def test_refs_to_ids_with_same_function_name():
    validator = compile({
        'definitions': {
            'i': {'$id': 'http://example.com/user-id.json', 'type': 'integer'},
            's': {'$id': 'http://example.com/user_id.json', 'type': 'string'},
        },
        'properties': {
            'a': {'$ref': 'http://example.com/user-id.json'},
            'b': {'$ref': 'http://example.com/user_id.json'},
        },
    })

    assert validator({'a': 1, 'b': 'x'}) == {'a': 1, 'b': 'x'}
    with pytest.raises(JsonSchemaException):
        validator({'b': 1})


def test_ref_changed_by_normalization_and_its_normalized_form_use_one_function():
    validator = compile({
        'definitions': {'ab': {'type': 'integer'}},
        'properties': {'x': {'$ref': '?#/definitions/ab'}, 'y': {'$ref': '#/definitions/ab'}},
    })

    assert validator({'x': 1, 'y': 1}) == {'x': 1, 'y': 1}
    with pytest.raises(JsonSchemaException):
        validator({'x': 'a'})


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
