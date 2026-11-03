import copy
import re
from urllib.parse import quote

import pytest

from fastjsonschema import (
    JsonSchemaDefinitionException,
    JsonSchemaException,
    JsonSchemaValueException,
    RefResolver,
    compile,
    compile_to_code,
)
from fastjsonschema import _get_code_generator_class
from fastjsonschema.draft2019 import CodeGeneratorDraft2019
from fastjsonschema.ref_resolver import id_next_to_ref_applies
from fastjsonschema.draft07 import CodeGeneratorDraft07


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


def no_handler(uri):
    raise AssertionError('handler called with ' + uri)


@pytest.mark.parametrize('schema_id', ['schemas/item.json', 'file:schemas/item.json'])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_local_ref_under_relative_root_id_with_directory(schema_id, fast_fail):
    validator = compile({
        '$id': schema_id,
        'definitions': {'count': {'type': 'integer'}},
        'properties': {'count': {'$ref': '#/definitions/count'}},
    }, handlers={'': no_handler, 'file': no_handler}, fast_fail=fast_fail)

    assert validator({'count': 1}) == {'count': 1}
    with pytest.raises(JsonSchemaException):
        validator({'count': 'a'})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_error_definition_under_relative_root_id_with_directory(fast_fail):
    validator = compile({
        '$id': 'schemas/item.json',
        'type': 'object',
        'definitions': {'count': {'type': 'integer'}},
        'properties': {'count': {'$ref': '#/definitions/count'}},
    }, handlers={'': no_handler}, fast_fail=fast_fail)

    with pytest.raises(JsonSchemaException) as exc:
        validator('x')
    errors = [exc.value] if fast_fail else exc.value.errors
    assert errors[0].definition['properties'] == {'count': {'type': 'integer'}}


@pytest.mark.parametrize('base_uri, schema_id, expected', [
    ('http://example.com/dir/', 'item.json', 'http://example.com/dir/item.json#/definitions/count'),
    # Constructed directly, the resolver applies the root $id to the base URI even if they are equal.
    ('schemas/item.json', 'schemas/item.json', 'schemas/schemas/item.json#/definitions/count'),
])
def test_resolver_applies_root_id_to_base_uri(base_uri, schema_id, expected):
    schema = {
        '$id': schema_id,
        'definitions': {'count': {'type': 'integer'}},
        'properties': {'count': {'$ref': '#/definitions/count'}},
    }
    resolver = RefResolver(base_uri, schema, store={})

    assert resolver.get_ref(schema['properties']['count']) == expected


def test_relative_ref_under_relative_root_id_with_directory():
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'integer'}

    validator = compile({'$id': 'a/b/item.json', 'properties': {'x': {'$ref': 'other.json'}}}, handlers={'': handler})

    assert validator({'x': 1}) == {'x': 1}
    assert loaded == ['a/b/other.json']


@pytest.mark.parametrize('ref', ['#', 'node.json'])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_to_subschema_with_relative_id_with_directory(ref, fast_fail):
    validator = compile({
        'properties': {'p': {
            '$id': 'schemas/node.json',
            'properties': {'q': {'$ref': ref}, 'n': {'type': 'integer'}},
        }},
    }, handlers={'': no_handler}, fast_fail=fast_fail)

    assert validator({'p': {'q': {'n': 1}}}) == {'p': {'q': {'n': 1}}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'q': {'n': 'a'}}})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_schema_with_relative_root_id_with_directory_compiled_twice(fast_fail):
    schema = {
        '$id': 'schemas/item.json',
        'definitions': {'count': {'type': 'integer'}},
        'properties': {'count': {'$ref': '#/definitions/count'}},
    }

    for _ in range(2):
        validator = compile(schema, handlers={'': no_handler}, fast_fail=fast_fail)
        assert validator({'count': 1}) == {'count': 1}
        with pytest.raises(JsonSchemaException):
            validator({'count': 'a'})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_local_ref_in_loaded_schema_under_relative_root_id_with_directory(fast_fail):
    loaded = []

    def handler(uri):
        loaded.append(uri)
        if uri != 'a/b/other.json':
            raise AssertionError('handler called with ' + uri)
        return {'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}}}

    validator = compile(
        {'$id': 'a/b/root.json', 'properties': {'o': {'$ref': 'other.json'}}},
        handlers={'': handler},
        fast_fail=fast_fail,
    )

    assert validator({'o': {'c': 1}}) == {'o': {'c': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'o': {'c': 'a'}})
    assert loaded == ['a/b/other.json']


def test_nested_relative_id_is_registered_once():
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'string'}

    validator = compile({
        '$id': 'http://example.com/root/base.json',
        'definitions': {'node': {'$id': 'child/node.json', 'type': 'integer'}},
        # The generator works through the refs last in, first out: p's function is generated first.
        'properties': {'q': {'$ref': 'child/child/node.json'}, 'p': {'$ref': 'child/node.json'}},
    }, handlers={'http': handler})

    assert validator({'p': 1, 'q': 'a'}) == {'p': 1, 'q': 'a'}
    assert loaded == ['http://example.com/root/child/child/node.json']


HANDLER_DOC = {
    '$id': 'http://example.com/doc.json',
    'definitions': {'x': {'type': 'string'}},
    'properties': {'p': {
        '$id': 'http://example.com/node.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'v': {'$ref': '#/definitions/x'}},
    }},
}


@pytest.mark.parametrize('scheme, uri', [
    ('http', 'http://example.com/doc.json'),
    ('', 'schemas/main.json'),
    ('file', 'file:schemas/main.json'),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_in_handler_loaded_schema_uses_id_of_its_subschema(scheme, uri, fast_fail):
    validator = compile(
        {'$ref': uri},
        handlers={scheme: lambda loaded_uri: copy.deepcopy(HANDLER_DOC)},
        fast_fail=fast_fail,
    )

    assert validator({'p': {'v': 1}}) == {'p': {'v': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'v': 'a'}})


@pytest.mark.parametrize('uri, schema_id, expected', [
    ('http://example.com/a/main.json', 'b/main.json', 'http://example.com/a/b/child.json'),
    # The same rule applies if the retrieval URI is relative and equal to the $id.
    ('dir/main.json', 'dir/main.json', 'dir/dir/child.json'),
])
def test_root_id_of_handler_loaded_schema_is_resolved_against_its_uri(uri, schema_id, expected):
    loaded = []

    def handler(loaded_uri):
        loaded.append(loaded_uri)
        if loaded_uri == uri:
            return {'$id': schema_id, 'properties': {'c': {'$ref': 'child.json'}}}
        return {'type': 'integer'}

    validator = compile({'$ref': uri}, handlers={'http': handler, '': handler})

    assert validator({'c': 1}) == {'c': 1}
    assert loaded == [uri, expected]


def test_relative_ref_in_handler_loaded_schema_is_resolved_once():
    loaded = []

    def handler(uri):
        loaded.append(uri)
        if uri == 'schemas/main.json':
            return {'properties': {'v': {'$ref': '../other.json'}}}
        return {'type': 'string'}

    validator = compile({'$ref': 'schemas/main.json'}, handlers={'': handler})

    assert validator({'v': 'a'}) == {'v': 'a'}
    assert loaded == ['schemas/main.json', 'other.json']


def test_ref_under_id_without_host_in_handler_loaded_schema_is_resolved_once():
    doc = {
        '$id': 'http://example.com/doc.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'p': {
            '$id': 'file:///node.json',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {'v': {'$ref': '#/definitions/x'}},
        }},
    }

    def handler(uri):
        if uri == 'file://server/schemas/main.json':
            return copy.deepcopy(doc)
        raise AssertionError('handler called with ' + uri)

    # walk() rewrites the $ref to file:///node.json#/definitions/x. Resolved again against
    # file://server/schemas/main.json, it would turn into file://server/node.json#/definitions/x.
    validator = compile({'$ref': 'file://server/schemas/main.json'}, handlers={'file': handler})

    assert validator({'p': {'v': 1}}) == {'p': {'v': 1}}


def test_handler_loaded_schema_without_cache():
    doc = {
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {
            '$id': 'http://example.com/node.json',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {'v': {'$ref': '#/definitions/x'}},
        }},
    }
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return copy.deepcopy(doc)

    # Without cache, each ref into the document loads it again, as a new object that is walked too.
    schema = {'properties': {
        'a': {'$ref': 'http://example.com/doc.json#/properties/p'},
        'b': {'$ref': 'http://example.com/doc.json'},
    }}
    resolver = RefResolver.from_schema(schema, handlers={'http': handler}, store={}, cache=False)
    code_generator = CodeGeneratorDraft07(schema, resolver=resolver)
    global_state = code_generator.global_state
    exec(code_generator.func_code, global_state)  # pylint: disable=exec-used
    validator = global_state[resolver.get_scope_name()]

    data = {'a': {'v': 1}, 'b': {'p': {'v': 1}}}
    assert validator(data) == data
    for invalid in ({'a': {'v': 'x'}}, {'b': {'p': {'v': 'x'}}}):
        with pytest.raises(JsonSchemaException):
            validator(invalid)
    assert loaded == ['http://example.com/doc.json', 'http://example.com/doc.json']


def test_invalid_uri_in_unknown_keyword_of_handler_loaded_schema():
    validator = compile(
        {'$ref': 'http://example.com/doc.json'},
        handlers={'http': lambda uri: {'x-note': {'$ref': 'http://[bad'}}},
    )

    assert validator({}) == {}


def test_used_ref_that_is_not_a_valid_uri_fails():
    with pytest.raises(ValueError):
        compile({'properties': {'p': {'$ref': 'http://[bad'}}})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_handler_returning_the_same_objects_compiled_twice(fast_fail):
    repo = {
        'schemas/main.json': {
            'definitions': {
                'object': {'type': 'object', 'properties': {'value': {'$ref': 'main.json#/definitions/string'}}},
                'string': {'type': 'string'},
            },
        },
    }

    for _ in range(2):
        validator = compile(
            {'$ref': 'schemas/main.json#/definitions/object'}, handlers={'': repo.__getitem__}, fast_fail=fast_fail,
        )
        assert validator({'value': 'ok'}) == {'value': 'ok'}
        with pytest.raises(JsonSchemaException):
            validator({'value': 1})


def test_handler_loaded_schema_compiled_directly_afterwards():
    loaded = {'definitions': {'s': {'type': 'string'}}, 'properties': {'v': {'$ref': '#/definitions/s'}}}
    compile({'properties': {'b': {'$ref': 'http://example.com/b.json'}}}, handlers={'http': lambda uri: loaded})

    validator = compile(loaded, handlers={'http': refuse_handler})

    assert validator({'v': 'a'}) == {'v': 'a'}
    with pytest.raises(JsonSchemaException):
        validator({'v': 1})


def documents_with_shared_ref(shared_document):
    ref = {'$ref': 'defs.json'}
    document = {'properties': {'c': ref}}
    return {
        'http://example.com/a/doc.json': document if shared_document else {'properties': {'c': ref}},
        'http://example.com/b/doc.json': document if shared_document else {'properties': {'c': ref}},
        'http://example.com/a/defs.json': {'type': 'string'},
        'http://example.com/b/defs.json': {'type': 'integer'},
    }


@pytest.mark.parametrize('shared_document', [True, False], ids=['same document', 'same subschema'])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_objects_shared_by_handler_loaded_schemas(shared_document, fast_fail):
    documents = documents_with_shared_ref(shared_document)
    validator = compile({
        'properties': {
            'a': {'$ref': 'http://example.com/a/doc.json'},
            'b': {'$ref': 'http://example.com/b/doc.json'},
        },
    }, handlers={'http': documents.__getitem__}, fast_fail=fast_fail)

    assert validator({'a': {'c': 'x'}, 'b': {'c': 1}}) == {'a': {'c': 'x'}, 'b': {'c': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'a': {'c': 1}})
    with pytest.raises(JsonSchemaException):
        validator({'b': {'c': 'x'}})



def node_with_own_y(id_key='$id', in_array=False):
    ref = {'$ref': '#/definitions/y'}
    return {
        id_key: 'http://example.com/node.json',
        'definitions': {'y': {'type': 'integer'}},
        'properties': {'b': {'allOf': [ref]} if in_array else ref},
    }


@pytest.mark.parametrize('schema_version, id_key', [
    ('http://json-schema.org/draft-04/schema#', 'id'),
    ('http://json-schema.org/draft-07/schema#', '$id'),
    (None, '$id'),
])
@pytest.mark.parametrize('definitions_key', ['definitions', '$defs'])
@pytest.mark.parametrize('in_array', [False, True])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_into_definitions_next_to_ref_uses_id_of_target(schema_version, id_key, definitions_key, in_array, fast_fail):
    schema = {'$ref': '#/{}/a'.format(definitions_key), 'definitions': {'y': {'type': 'string'}}}
    schema.setdefault(definitions_key, {})['a'] = node_with_own_y(id_key, in_array)
    if schema_version:
        schema['$schema'] = schema_version
    validator = compile(schema, fast_fail=fast_fail)

    assert validator({'b': 1}) == {'b': 1}
    with pytest.raises(JsonSchemaException):
        validator({'b': 'x'})


@pytest.mark.parametrize('root_id, node_id', [
    (None, 'node.json'),
    ('schemas/root.json', 'node.json'),
    ('http://example.com/root.json', 'sub/node.json'),
    (None, 'urn:example:node'),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_into_definitions_next_to_ref_with_other_ids(root_id, node_id, fast_fail):
    node = node_with_own_y()
    node['$id'] = node_id
    schema = {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$ref': '#/definitions/a',
        'definitions': {'a': node, 'y': {'type': 'string'}},
    }
    if root_id:
        schema['$id'] = root_id
    validator = compile(schema, handlers={'': no_handler, 'http': no_handler, 'urn': no_handler}, fast_fail=fast_fail)

    assert validator({'b': 1}) == {'b': 1}
    with pytest.raises(JsonSchemaException):
        validator({'b': 'x'})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_to_id_in_defs_next_to_ref_under_root_id(fast_fail):
    # The form of "order of evaluation: $id and $ref" in the 2019-09 suite.
    validator = compile({
        '$schema': 'https://json-schema.org/draft/2019-09/schema',
        '$id': 'http://example.com/a/base.json',
        '$ref': 'int.json',
        '$defs': {
            'bigint': {'$id': 'int.json', 'maximum': 10},
            'smallint': {'$id': '/a-int.json', 'maximum': 2},
        },
    }, handlers={'http': no_handler}, fast_fail=fast_fail)

    assert validator(5) == 5
    with pytest.raises(JsonSchemaException):
        validator(50)


@pytest.mark.parametrize('schema_version, foo_type, bar_type, expected_loaded', [
    # In 2019-09, the $id next to the $ref is the base URI of the $ref and of the $defs next to it:
    # foo is the local sub/item.json, bar the remote item.json.
    ('https://json-schema.org/draft/2019-09/schema', 'integer', 'string', ['http://example.com/item.json']),
    (None, 'integer', 'string', ['http://example.com/item.json']),
    # draft-07 ignores the $id next to the $ref: the $defs register item.json, which both refs use.
    ('http://json-schema.org/draft-07/schema#', 'integer', 'integer', []),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_id_next_to_ref_with_definitions(schema_version, foo_type, bar_type, expected_loaded, fast_fail):
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'string'}

    schema = {
        '$id': 'http://example.com/root.json',
        'properties': {
            'foo': {'$id': 'sub/foo.json', '$ref': 'item.json', '$defs': {'item': {'$id': 'item.json', 'type': 'integer'}}},
            'bar': {'$ref': 'item.json'},
        },
    }
    if schema_version:
        schema['$schema'] = schema_version
    validator = compile(schema, handlers={'http': handler}, fast_fail=fast_fail)

    values = {'integer': 1, 'string': 'x'}
    for key, valid_type in (('foo', foo_type), ('bar', bar_type)):
        invalid_type = 'string' if valid_type == 'integer' else 'integer'
        assert validator({key: values[valid_type]}) == {key: values[valid_type]}
        with pytest.raises(JsonSchemaException):
            validator({key: values[invalid_type]})
    assert loaded == expected_loaded


@pytest.mark.parametrize('fast_fail', [True, False])
def test_pointer_into_definitions_next_to_ref_with_id_in_draft_07(fast_fail):
    validator = compile({
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$id': 'http://example.com/root.json',
        'definitions': {'int': {'type': 'integer'}},
        'properties': {
            'foo': {
                '$id': 'ignored.json',
                '$ref': '#/definitions/int',
                'definitions': {'a': {
                    '$id': 'child.json',
                    'definitions': {'x': {'type': 'string'}},
                    'properties': {'v': {'$ref': '#/definitions/x'}},
                }},
            },
            'bar': {'$ref': '#/properties/foo/definitions/a'},
        },
    }, handlers={'http': no_handler}, fast_fail=fast_fail)

    assert validator({'foo': 1, 'bar': {'v': 'x'}}) == {'foo': 1, 'bar': {'v': 'x'}}
    with pytest.raises(JsonSchemaException):
        validator({'bar': {'v': 1}})
    with pytest.raises(JsonSchemaException):
        validator({'foo': 'x'})


def test_id_in_definitions_next_to_ref_is_registered():
    validator = compile({
        '$ref': 'http://example.com/node.json',
        'definitions': {'a': node_with_own_y(), 'y': {'type': 'string'}},
    }, handlers={'http': no_handler})

    assert validator({'b': 1}) == {'b': 1}
    with pytest.raises(JsonSchemaException):
        validator({'b': 'x'})


def test_ref_into_definitions_next_to_ref_in_handler_loaded_schema():
    doc = {'$ref': '#/definitions/a', 'definitions': {'a': node_with_own_y(), 'y': {'type': 'string'}}}
    validator = compile({'$ref': 'http://example.com/doc.json'}, handlers={'http': lambda uri: copy.deepcopy(doc)})

    assert validator({'b': 1}) == {'b': 1}
    with pytest.raises(JsonSchemaException):
        validator({'b': 'x'})


@pytest.mark.parametrize('keyword', ['x-example', 'not'])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_id_in_other_keyword_next_to_ref_is_ignored(keyword, fast_fail):
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'integer'}

    validator = compile({
        # In 2019-09, `not` next to a $ref is an applicator, and its $id identifies a schema in the document.
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$ref': 'http://example.com/target',
        keyword: {'$id': 'http://example.com/target', 'type': 'string'},
    }, handlers={'http': handler}, fast_fail=fast_fail)

    assert validator(1) == 1
    with pytest.raises(JsonSchemaException):
        validator('x')
    assert loaded == ['http://example.com/target']


UNKNOWN_KEYWORD_DEFINITIONS = {'a': {'x-example': {'$id': 'http://example.com/target', 'type': 'string'}}}


@pytest.mark.parametrize('schema, valid, invalid', [
    ({'definitions': UNKNOWN_KEYWORD_DEFINITIONS, 'properties': {'p': {'$ref': 'http://example.com/target'}}},
     {'p': 'x'}, {'p': 1}),
    ({'$ref': 'http://example.com/target', 'definitions': UNKNOWN_KEYWORD_DEFINITIONS}, 'x', 1),
])
def test_id_in_unknown_keyword_inside_definitions_is_registered(schema, valid, invalid):
    # walk() treats the values of unknown keywords as schemas, so this $id replaces the schema
    # a handler would load. Definitions next to a $ref are no exception.
    validator = compile(copy.deepcopy(schema), handlers={'http': no_handler})

    assert validator(valid) == valid
    with pytest.raises(JsonSchemaException):
        validator(invalid)


def test_data_keyword_next_to_ref_is_data():
    schema = {
        '$id': 'http://example.com/root',
        '$ref': '#/definitions/a',
        'definitions': {'a': {'type': 'object'}},
        'default': {'$ref': 'child'},
    }
    compile(schema)

    assert schema['default'] == {'$ref': 'child'}


def test_id_next_to_ref_is_ignored():
    validator = compile({
        '$schema': 'http://json-schema.org/draft-07/schema#',
        '$id': 'http://example.com/root.json',
        'definitions': {'y': {'type': 'string'}},
        'properties': {'b': {'$id': 'http://example.com/other.json', '$ref': '#/definitions/y'}},
    })

    assert validator({'b': 'x'}) == {'b': 'x'}
    with pytest.raises(JsonSchemaException):
        validator({'b': 1})


@pytest.mark.parametrize('schema_version, expected_loaded', [
    # 2019-09: id is an unknown keyword and doesn't change the base URI of the $ref next to it.
    (None, ['http://example.com/thing.json']),
    # draft-04: id next to a $ref is ignored, as every keyword next to a $ref.
    ('http://json-schema.org/draft-04/schema#', ['http://example.com/thing.json']),
])
def test_draft_04_id_next_to_ref(schema_version, expected_loaded):
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {}

    schema = {'id': 'http://example.com/root.json', 'properties': {'a': {'id': 'sub/a.json', '$ref': 'thing.json'}}}
    if schema_version:
        schema['$schema'] = schema_version
    compile(schema, handlers={'http': handler})

    assert loaded == expected_loaded


@pytest.mark.parametrize('schema', [
    {},
    True,
    {'$schema': 'http://json-schema.org/draft-04/schema#'},
    {'$schema': 'http://json-schema.org/draft-06/schema#'},
    {'$schema': 'http://json-schema.org/draft-07/schema#'},
    {'$schema': 'https://json-schema.org/draft/2019-09/schema'},
    {'$schema': 'http://example.com/custom-meta-schema'},
])
def test_resolver_reads_the_draft_like_the_compiler(schema):
    applies = id_next_to_ref_applies(schema)

    assert applies == (_get_code_generator_class(schema) is CodeGeneratorDraft2019)

