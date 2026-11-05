import pytest

from fastjsonschema import JsonSchemaException, compile
from fastjsonschema.ref_resolver import SCHEMA_VALUES

TARGET = 'http://example.com/target.json'
NOT_A_SCHEMA = {'$id': TARGET, 'type': 'string'}
REAL_SCHEMA = {'$id': TARGET, 'type': 'integer'}


def refuse_handler(uri):
    raise RuntimeError('handler called for ' + uri)


def assert_ref_uses_real_schema(schema):
    validator = compile(schema, handlers={'http': refuse_handler})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'text'})


@pytest.mark.parametrize('unknown_first', [True, False])
@pytest.mark.parametrize('unknown', [
    {'x-note': NOT_A_SCHEMA},
    {'x-note': {'nested': NOT_A_SCHEMA}},
    {'x-note': {'properties': {'nested': NOT_A_SCHEMA}}},
    {'x-note': {'allOf': [NOT_A_SCHEMA]}},
    {'not': {'x-note': NOT_A_SCHEMA}},
], ids=['value', 'nested', 'properties', 'array', 'in-not'])
def test_id_in_unknown_keyword_does_not_replace_a_real_one(unknown, unknown_first):
    keywords = [('x-container', unknown), ('$defs', {'real': REAL_SCHEMA})]
    schema = dict(keywords if unknown_first else reversed(keywords))
    schema['properties'] = {'p': {'$ref': TARGET}}

    assert_ref_uses_real_schema(schema)


@pytest.mark.parametrize('keyword', SCHEMA_VALUES)
def test_id_in_keyword_with_one_schema_is_a_real_one(keyword):
    assert_ref_uses_real_schema({
        '$defs': {'wrapper': {keyword: REAL_SCHEMA}, 'unknown': {'x-note': NOT_A_SCHEMA}},
        'properties': {'p': {'$ref': TARGET}},
    })


def test_id_in_unknown_keyword_stays_available_without_a_real_one():
    assert_ref_uses_real_schema({
        'x-definitions': {'number': REAL_SCHEMA},
        'properties': {'p': {'$ref': TARGET}},
    })


def test_ref_in_unknown_keyword_resolves_against_its_id():
    validator = compile({
        '$id': 'http://example.com/root.json',
        'x-definitions': {
            'a': {'$id': 'http://example.com/dir/a.json', 'properties': {'p': {'$ref': 'b.json'}}},
            'b': {'$id': 'http://example.com/dir/b.json', 'type': 'integer'},
        },
        '$ref': 'dir/a.json',
    }, handlers={'http': refuse_handler})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'text'})
