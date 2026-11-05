import copy

import pytest

from fastjsonschema import JsonSchemaException, compile


def no_handler(uri):
    raise AssertionError('handler called with ' + uri)


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
