import copy

import pytest

from fastjsonschema import JsonSchemaException, compile


def refuse_handler(uri):
    raise RuntimeError('handler called for ' + uri)


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


@pytest.mark.parametrize('fast_fail', [True, False])
def test_error_definition_expands_refs_only_in_schema_arrays(fast_fail):
    def handler(uri):
        raise AssertionError('handler called with ' + uri)

    validator = compile({
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': node_with_local_x({
            'type': 'object',
            'allOf': [{'$ref': '#/definitions/x'}],
            'x-list': [{'$ref': 'http://example.com/unknown.json'}],
        })},
    }, handlers={'http': handler}, fast_fail=fast_fail)

    with pytest.raises(JsonSchemaException) as exc:
        validator({'p': {'v': 1}})
    error = exc.value if fast_fail else exc.value.errors[0]
    assert error.definition['allOf'] == [{'type': 'integer'}]
    assert error.definition['x-list'] == [{'$ref': 'http://example.com/unknown.json'}]
