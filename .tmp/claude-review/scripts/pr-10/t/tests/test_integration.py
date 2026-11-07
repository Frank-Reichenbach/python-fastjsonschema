import copy
import re
from urllib.parse import quote

import pytest

from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaException, JsonSchemaValueException, compile, compile_to_code
from fastjsonschema.ref_resolver import RefResolver


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


@pytest.mark.parametrize('fast_fail', [True, False])
def test_refs_to_ids_with_same_function_name(fast_fail):
    validator = compile({
        'definitions': {
            'i': {'$id': 'http://example.com/user-id.json', 'type': 'integer'},
            's': {'$id': 'http://example.com/user_id.json', 'type': 'string'},
        },
        'properties': {
            'a': {'$ref': 'http://example.com/user-id.json'},
            'b': {'$ref': 'http://example.com/user_id.json'},
        },
    }, fast_fail=fast_fail)

    assert validator({'a': 1, 'b': 'x'}) == {'a': 1, 'b': 'x'}
    with pytest.raises(JsonSchemaException):
        validator({'b': 1})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_changed_by_normalization_and_its_normalized_form_use_one_function(fast_fail):
    validator = compile({
        'definitions': {'ab': {'type': 'integer'}},
        'properties': {'x': {'$ref': '?#/definitions/ab'}, 'y': {'$ref': '#/definitions/ab'}},
    }, fast_fail=fast_fail)

    assert validator({'x': 1, 'y': 1}) == {'x': 1, 'y': 1}
    with pytest.raises(JsonSchemaException):
        validator({'x': 'a'})


def string_handler(uri):
    return {'type': 'string'}


@pytest.mark.parametrize('schema', [
    # '#/-' and the root both get the name "validate"
    {'-': {'type': 'string'}, 'type': 'object', 'properties': {'a': {'$ref': '#/-'}}},
    # the root $id and the loaded schema both get the name "validate_http___example_com_a_b_json"
    {'$id': 'http://example.com/a-b.json', 'type': 'object', 'properties': {'a': {'$ref': 'http://example.com/a_b.json'}}},
], ids=['local', 'handler'])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_with_function_name_of_root_does_not_replace_root(schema, fast_fail):
    validator = compile(schema, handlers={'http': string_handler}, fast_fail=fast_fail)

    assert validator({'a': 'x'}) == {'a': 'x'}
    with pytest.raises(JsonSchemaException) as exc:
        validator({'a': 1})
    assert 'data.a must be string' in str(exc.value)
    with pytest.raises(JsonSchemaException):
        validator('x')


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


URN_NODE = {
    '$id': 'urn:example:node',
    'type': 'object',
    'properties': {
        'all': {'type': 'array', 'items': {'$ref': '#'}},
        'eq': {'type': 'array', 'maxItems': 2},
    },
    'additionalProperties': False,
}


@pytest.mark.parametrize('schema, handlers', [
    ({'properties': {'p': {'$ref': 'urn:example:node'}}, 'definitions': {'node': URN_NODE}}, {}),
    ({'properties': {'p': {'$ref': 'urn:example:node'}}}, {'urn': lambda uri: copy.deepcopy(URN_NODE)}),
    ({'properties': {'p': URN_NODE}}, {}),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_local_ref_in_subschema_with_urn_id(schema, handlers, fast_fail):
    # The test cases share URN_NODE, which compile() leaves unchanged.
    validator = compile(schema, handlers=handlers, fast_fail=fast_fail)

    assert validator({'p': {'all': [{'eq': [1, 2]}]}}) == {'p': {'all': [{'eq': [1, 2]}]}}
    with pytest.raises(JsonSchemaException) as exc:
        validator({'p': {'all': [{'eq': [1, 2, 3]}]}})
    errors = [exc.value] if fast_fail else exc.value.errors
    assert errors[0].name == 'data.p.all[0].eq'


@pytest.mark.parametrize('id_keyword, node_id, schema_uri', [
    ('$id', 'tag:example.com,2026:node', None),
    ('$id', 'URN:Example:Node', None),
    ('$id', 's3://bucket/node.json', None),
    ('$id', 'urn:example:node#', 'http://json-schema.org/draft-06/schema#'),
    ('id', 'urn:example:node', 'http://json-schema.org/draft-04/schema#'),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_local_ref_in_subschema_with_other_id_outside_uses_relative(id_keyword, node_id, schema_uri, fast_fail):
    node = {key: value for key, value in copy.deepcopy(URN_NODE).items() if key != '$id'}
    node[id_keyword] = node_id
    schema = {'properties': {'p': node}}
    if schema_uri:
        schema['$schema'] = schema_uri
    validator = compile(schema, fast_fail=fast_fail)

    assert validator({'p': {'all': [{'eq': [1, 2]}]}}) == {'p': {'all': [{'eq': [1, 2]}]}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'all': [{'eq': [1, 2, 3]}]}})


def test_ref_to_root_under_root_urn_id_uses_root_function():
    code = compile_to_code({'$id': 'urn:example:root', 'properties': {'a': {'$ref': '#'}}})

    assert re.findall(r'^def (\w+)', code, re.M) == ['validate_urn_example_root']


@pytest.mark.parametrize('fast_fail', [True, False])
def test_json_pointer_ref_in_subschema_with_urn_id(fast_fail):
    validator = compile({
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {
            '$id': 'urn:example:item',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {'v': {'$ref': '#/definitions/x'}},
        }},
    }, fast_fail=fast_fail)

    assert validator({'p': {'v': 1}}) == {'p': {'v': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'v': 'a'}})


def test_json_pointer_ref_in_subschema_with_urn_id_does_not_fall_back_to_root():
    with pytest.raises(JsonSchemaDefinitionException):
        compile({
            'definitions': {'x': {'type': 'string'}},
            'properties': {'p': {
                '$id': 'urn:example:item',
                'properties': {'v': {'$ref': '#/definitions/x'}},
            }},
        })


def test_local_ref_in_subschema_with_http_id_is_resolved_by_urljoin():
    schema = {
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {
            '$id': 'HTTP://example.com/item.json',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {'v': {'$ref': '#/definitions/x'}},
        }},
    }
    resolver = RefResolver.from_schema(schema, store={})

    # urljoin lowercases the scheme.
    assert resolver.get_ref(schema['properties']['p']['properties']['v']) == 'http://example.com/item.json#/definitions/x'


@pytest.mark.parametrize('fast_fail', [True, False])
def test_plain_name_id_in_subschema_with_urn_id(fast_fail):
    validator = compile({
        'definitions': {
            's': {'$id': '#foo', 'type': 'string'},
            'item': {
                '$id': 'urn:example:item',
                'definitions': {'i': {'$id': '#foo', 'type': 'integer'}},
                'properties': {'v': {'$ref': '#foo'}},
            },
        },
        'properties': {'r': {'$ref': '#foo'}, 'p': {'$ref': 'urn:example:item'}},
    }, fast_fail=fast_fail)

    assert validator({'r': 'a', 'p': {'v': 1}}) == {'r': 'a', 'p': {'v': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'r': 1})
    with pytest.raises(JsonSchemaException):
        validator({'p': {'v': 'a'}})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_object_in_data_keyword_under_urn_id_is_data(fast_fail):
    validator = compile({
        '$id': 'urn:example:root',
        'properties': {'c': {'const': {'$ref': '#'}}, 'd': {'default': {'$ref': '#'}}},
    }, fast_fail=fast_fail)

    assert validator({'c': {'$ref': '#'}}) == {'c': {'$ref': '#'}, 'd': {'$ref': '#'}}


@pytest.mark.parametrize('fast_fail', [True, False])
def test_plain_name_ref_under_urn_id_next_to_similar_urn(fast_fail):
    validator = compile({
        '$id': 'urn:example:root',
        'definitions': {
            'a': {'$id': '#foo', 'type': 'integer'},
            'b': {'$id': 'urn:example:root:foo', 'type': 'string'},
        },
        'properties': {'a': {'$ref': '#foo'}, 'b': {'$ref': 'urn:example:root:foo'}},
    }, fast_fail=fast_fail)

    assert validator({'a': 1, 'b': 'x'}) == {'a': 1, 'b': 'x'}
    with pytest.raises(JsonSchemaException):
        validator({'b': 1})


def refuse_handler(uri):
    raise RuntimeError('handler called for ' + uri)


def schema_with_refs(schema_id, defined_type):
    return {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$id': schema_id,
        'definitions': {
            'x': {'type': defined_type},
            'node': {'$id': 'node.json', 'definitions': {'y': {'type': 'integer'}}, 'properties': {'y': {'$ref': '#/definitions/y'}}},
        },
        'properties': {
            'p': {'$ref': '#/definitions/x'},
            'q': {'allOf': [{'$ref': '#/definitions/x'}], 'items': [{'$ref': '#/definitions/x'}]},
            'n': {'$ref': 'node.json'},
        },
    }


@pytest.mark.parametrize('to_code', [False, True])
def test_compile_leaves_schema_unchanged(to_code):
    schema = schema_with_refs('http://example.com/root.json', 'integer')
    original = copy.deepcopy(schema)

    if to_code:
        compile_to_code(schema, handlers={'http': refuse_handler})
    else:
        compile(schema, handlers={'http': refuse_handler})

    assert schema == original


@pytest.mark.parametrize('fast_fail', [True, False])
def test_object_shared_by_schemas_with_different_ids(fast_fail):
    shared = {'$ref': '#/definitions/x'}
    first = {'$id': 'http://example.com/one.json', 'definitions': {'x': {'type': 'integer'}}, 'properties': {'p': shared}}
    second = {'$id': 'http://example.com/two.json', 'definitions': {'x': {'type': 'string'}}, 'properties': {'p': shared}}

    validate_first = compile(first, handlers={'http': refuse_handler}, fast_fail=fast_fail)
    validate_second = compile(second, handlers={'http': refuse_handler}, fast_fail=fast_fail)

    assert validate_first({'p': 1}) == {'p': 1}
    assert validate_second({'p': 'a'}) == {'p': 'a'}
    with pytest.raises(JsonSchemaException):
        validate_second({'p': 1})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_schema_compiled_again_after_its_id_changed(fast_fail):
    schema = schema_with_refs('http://example.com/v1.json', 'integer')
    compile(schema, handlers={'http': refuse_handler}, fast_fail=fast_fail)
    schema['$id'] = 'http://example.com/v2.json'

    validator = compile(schema, handlers={'http': refuse_handler}, fast_fail=fast_fail)

    assert validator({'p': 1, 'n': {'y': 1}}) == {'p': 1, 'n': {'y': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'a'})


def node_with_local_x(v, id_key='$id'):
    return {
        id_key: 'http://example.com/node.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'v': v},
    }


@pytest.mark.parametrize('schema_version, id_key', [
    ('http://json-schema.org/draft-04/schema#', 'id'),
    ('http://json-schema.org/draft-07/schema#', '$id'),
])
@pytest.mark.parametrize('v, valid, invalid', [
    ({'allOf': [{'$ref': '#/definitions/x'}]}, 1, 'a'),
    ({'anyOf': [{'$ref': '#/definitions/x'}]}, 1, 'a'),
    ({'oneOf': [{'$ref': '#/definitions/x'}]}, 1, 'a'),
    ({'items': [{'$ref': '#/definitions/x'}]}, [1], ['a']),
    ({'allOf': [{'properties': {'w': {'$ref': '#/definitions/x'}}}]}, {'w': 1}, {'w': 'a'}),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_in_schema_array_uses_id_of_its_subschema(schema_version, id_key, v, valid, invalid, fast_fail):
    validator = compile({
        '$schema': schema_version,
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': node_with_local_x(v, id_key)},
    }, fast_fail=fast_fail)

    assert validator({'p': {'v': valid}}) == {'p': {'v': valid}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'v': invalid}})


def test_id_in_schema_array_is_registered():
    def handler(uri):
        raise AssertionError('handler called with ' + uri)

    validator = compile({
        '$id': 'http://example.com/root.json',
        'definitions': {'l': {'anyOf': [{'$id': 'item.json', 'type': 'integer'}, {'type': 'null'}]}},
        'properties': {'p': {'$ref': 'item.json'}},
    }, handlers={'http': handler})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'a'})


def test_plain_name_id_in_schema_array_is_registered():
    validator = compile({
        'definitions': {'l': {'allOf': [{'$id': '#int', 'type': 'integer'}]}},
        'properties': {'p': {'$ref': '#int'}},
    })

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'a'})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_boolean_schemas_next_to_ref_in_schema_array(fast_fail):
    validator = compile({
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': node_with_local_x({'allOf': [True, {'$ref': '#/definitions/x'}], 'anyOf': [False, True]})},
    }, fast_fail=fast_fail)

    assert validator({'p': {'v': 1}}) == {'p': {'v': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'v': 'a'}})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_schema_array_shared_by_schemas_with_different_ids(fast_fail):
    nullable = {'anyOf': [{'$ref': '#/definitions/x'}, {'type': 'null'}]}
    first = {'$id': 'http://example.com/one.json', 'definitions': {'x': {'type': 'integer'}}, 'properties': {'p': nullable}}
    second = {'$id': 'http://example.com/two.json', 'definitions': {'x': {'type': 'string'}}, 'properties': {'p': nullable}}

    validate_first = compile(first, handlers={'http': refuse_handler}, fast_fail=fast_fail)
    validate_second = compile(second, handlers={'http': refuse_handler}, fast_fail=fast_fail)

    assert validate_first({'p': 1}) == {'p': 1}
    assert validate_second({'p': 'a'}) == {'p': 'a'}
    with pytest.raises(JsonSchemaException):
        validate_second({'p': 1})


def test_array_in_unknown_keyword_is_not_walked():
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'integer'}

    validator = compile({
        '$id': 'http://example.com/root.json',
        'x-list': [{'$id': 'item.json', 'type': 'string'}],
        'properties': {'p': {'$ref': 'item.json'}},
    }, handlers={'http': handler})

    assert validator({'p': 1}) == {'p': 1}
    assert loaded == ['http://example.com/item.json']


def test_schema_array_inside_default_is_data():
    default = {'items': [{'$ref': '#/definitions/missing'}]}
    validator = compile({
        '$id': 'http://example.com/root.json',
        'properties': {'p': {'default': copy.deepcopy(default)}},
    }, use_default=True)

    assert validator({}) == {'p': default}


def test_schema_array_inside_data_keyword_is_data():
    value = {'allOf': [{'$ref': '#/definitions/x'}]}
    validator = compile({
        '$id': 'http://example.com/root.json',
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {'const': copy.deepcopy(value)}},
    })

    assert validator({'p': copy.deepcopy(value)}) == {'p': value}
