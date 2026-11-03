import copy
import re

import pytest

from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaException, compile, compile_to_code
from fastjsonschema.ref_resolver import join_uri


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
    # Copy, because the test cases share URN_NODE.
    validator = compile(copy.deepcopy(schema), handlers=handlers, fast_fail=fast_fail)

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


@pytest.mark.parametrize('base, ref, expected', [
    ('urn:example:node', '#/definitions/x', 'urn:example:node#/definitions/x'),
    ('urn:example:node#/a', '#foo', 'urn:example:node#foo'),
    ('urn:example:node#/a', '#', 'urn:example:node#'),
    ('tag:example.com,2026:node', '#foo', 'tag:example.com,2026:node#foo'),
    # Schemes that urljoin handles keep its result, which also lowercases the scheme.
    ('HTTP://example.com/item.json', '#/definitions/x', 'http://example.com/item.json#/definitions/x'),
    ('http://example.com/dir/a.json', 'b.json', 'http://example.com/dir/b.json'),
    # Only refs starting with # change: urljoin can't join other refs to such a base.
    ('urn:example:node', 'other.json', 'other.json'),
])
def test_join_uri(base, ref, expected):
    assert join_uri(base, ref) == expected


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


# urn:example:root#foo and urn:example:root:foo get the same function name until the names are unique per
# URI, as horejsek/python-fastjsonschema#224 makes them. Remove the mark once that is merged.
@pytest.mark.xfail(strict=True, reason='needs unique function names (horejsek/python-fastjsonschema#224)')
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
