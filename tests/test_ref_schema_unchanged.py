import copy

import pytest

from fastjsonschema import JsonSchemaException, compile, compile_to_code


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

