from urllib.parse import quote

import pytest

from fastjsonschema import JsonSchemaException, JsonSchemaValueException, compile, compile_to_code
from fastjsonschema.ref_resolver import RefResolver


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


def test_ref_with_empty_query_in_schema_with_a_keyword():
    validator = compile({
        'type': 'object',
        'definitions': {'ab': {'type': 'integer'}},
        'properties': {'a': {'$ref': '?#/definitions/ab'}, 'b': {'$ref': '#/definitions/ab'}},
    })

    assert validator({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    with pytest.raises(JsonSchemaValueException):
        validator({'a': 'x'})


def test_names_of_uris_that_do_not_collide_stay_as_they_are():
    resolver = RefResolver.from_schema({})
    with resolver.in_scope('#/definitions/a-b'):
        first = resolver.get_scope_name()
    with resolver.in_scope('#/definitions/a_b'):
        second = resolver.get_scope_name()
    with resolver.in_scope('#/definitions/a_b_2'):
        third = resolver.get_scope_name()
    with resolver.in_scope('#/definitions/a-b'):
        again = resolver.get_scope_name()

    assert first == again == 'validate___definitions_a_b'
    assert second == 'validate___definitions_a_b_2_'
    assert third == 'validate___definitions_a_b_2'


def test_compile_to_code_uses_the_unique_names():
    code = compile_to_code({
        'definitions': {'user-id': {'type': 'integer'}, 'user_id': {'type': 'string'}},
        'properties': {'a': {'$ref': '#/definitions/user-id'}, 'b': {'$ref': '#/definitions/user_id'}},
    })
    namespace = {}
    exec(code, namespace)

    assert namespace['validate']({'a': 1, 'b': 'x'}) == {'a': 1, 'b': 'x'}
