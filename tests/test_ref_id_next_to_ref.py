import pytest

from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaException, RefResolver, compile
from fastjsonschema.draft07 import CodeGeneratorDraft07
from fastjsonschema.draft2019 import CodeGeneratorDraft2019


@pytest.mark.parametrize('schema_version, expected_loaded', [
    ('https://json-schema.org/draft/2019-09/schema', 'http://example.com/sub/item.json'),
    (None, 'http://example.com/sub/item.json'),
    ('http://json-schema.org/draft-07/schema#', 'http://example.com/item.json'),
    ('http://json-schema.org/draft-06/schema#', 'http://example.com/item.json'),
])
def test_id_next_to_ref_is_the_base_uri_of_the_ref_in_2019_09(schema_version, expected_loaded):
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'integer'}

    schema = {
        '$id': 'http://example.com/root.json',
        'properties': {'p': {'$id': 'http://example.com/sub/', '$ref': 'item.json'}},
    }
    if schema_version:
        schema['$schema'] = schema_version
    validator = compile(schema, handlers={'http': handler})

    assert validator({'p': 1}) == {'p': 1}
    assert loaded == [expected_loaded]


def test_ref_next_to_id_cannot_point_into_the_outer_schema_in_2019_09():
    with pytest.raises(JsonSchemaDefinitionException):
        compile({
            '$id': 'http://example.com/root.json',
            'definitions': {'y': {'type': 'string'}},
            'properties': {'p': {'$id': 'http://example.com/other.json', '$ref': '#/definitions/y'}},
        }, handlers={'http': lambda uri: {}})


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


@pytest.mark.parametrize('code_generator_class, expected_loaded', [
    (CodeGeneratorDraft07, 'http://example.com/foo.json'),
    (CodeGeneratorDraft2019, 'http://example.com/sub/foo.json'),
])
def test_code_generator_tells_resolver_its_draft(code_generator_class, expected_loaded):
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return {'type': 'integer'}

    # No $schema: the draft of the code generator decides, not the default of RefResolver.
    schema = {'$id': 'http://example.com/root.json', 'properties': {'a': {'$id': 'sub/a.json', '$ref': 'foo.json'}}}
    resolver = RefResolver.from_schema(schema, handlers={'http': handler}, store={},
                                       keywords_next_to_ref=code_generator_class.KEYWORDS_NEXT_TO_REF)
    code_generator = code_generator_class(schema, resolver=resolver)
    code_generator.func_code  # pylint: disable=pointless-statement

    assert loaded == [expected_loaded]
