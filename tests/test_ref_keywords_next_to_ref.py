import pytest

from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaException, JsonSchemaValuesException, compile

DRAFT_2019 = 'https://json-schema.org/draft/2019-09/schema'
EARLIER_DRAFTS = [
    'http://json-schema.org/draft-04/schema#',
    'http://json-schema.org/draft-06/schema#',
    'http://json-schema.org/draft-07/schema#',
]


def refuse_handler(uri):
    raise RuntimeError('handler called for ' + uri)


@pytest.mark.parametrize('fast_fail', [True, False])
@pytest.mark.parametrize('schema_version', [DRAFT_2019, None])
def test_keyword_next_to_ref_validates_in_2019_09(schema_version, fast_fail):
    schema = {
        'definitions': {'list': {'type': 'array'}},
        'properties': {'p': {'$ref': '#/definitions/list', 'maxItems': 1}},
    }
    if schema_version:
        schema['$schema'] = schema_version
    validator = compile(schema, fast_fail=fast_fail)

    assert validator({'p': [1]}) == {'p': [1]}
    with pytest.raises(JsonSchemaException):
        validator({'p': [1, 2]})
    with pytest.raises(JsonSchemaException):
        validator({'p': 'text'})


@pytest.mark.parametrize('schema_version', EARLIER_DRAFTS)
def test_keyword_next_to_ref_is_ignored_before_2019_09(schema_version):
    validator = compile({
        '$schema': schema_version,
        'definitions': {'list': {'type': 'array'}},
        'properties': {'p': {'$ref': '#/definitions/list', 'maxItems': 1}},
    })

    assert validator({'p': [1, 2]}) == {'p': [1, 2]}


def test_errors_of_ref_and_keyword_next_to_it_are_collected():
    validator = compile({
        '$schema': DRAFT_2019,
        '$defs': {'short': {'maxLength': 2}},
        'properties': {'p': {'$ref': '#/$defs/short', 'pattern': '^a'}},
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc:
        validator({'p': 'bbb'})

    assert sorted(error.rule for error in exc.value.errors) == ['maxLength', 'pattern']


@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_in_keyword_next_to_ref(fast_fail):
    validator = compile({
        '$schema': DRAFT_2019,
        '$id': 'http://example.com/root.json',
        '$defs': {'object': {'type': 'object'}, 'number': {'type': 'integer'}},
        '$ref': '#/$defs/object',
        'properties': {'p': {'$ref': '#/$defs/number'}},
    }, fast_fail=fast_fail, handlers={'http': refuse_handler})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'text'})
    with pytest.raises(JsonSchemaException):
        validator(1)


@pytest.mark.parametrize('keyword', ['if', 'then', 'else', 'not'])
def test_ref_to_id_in_keyword_next_to_it(keyword):
    target = {'$id': 'http://example.com/target.json', 'type': 'integer'}
    validator = compile({
        '$schema': DRAFT_2019,
        '$defs': {'wrapper': {'$ref': 'http://example.com/target.json', keyword: target}},
        'properties': {'p': {'$ref': 'http://example.com/target.json'}},
    }, handlers={'http': refuse_handler})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaException):
        validator({'p': 'text'})


def test_id_in_keyword_next_to_ref_is_not_registered_before_2019_09():
    with pytest.raises(RuntimeError, match='handler called'):
        compile({
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'if': {'$id': 'http://example.com/target.json', 'type': 'integer'},
            '$ref': 'http://example.com/target.json',
        }, handlers={'http': refuse_handler})


@pytest.mark.parametrize('nested_id', ['nested.json', 'http://example.com/nested.json'])
def test_properties_next_to_ref_under_id_next_to_ref(nested_id):
    validator = compile({
        '$schema': DRAFT_2019,
        '$id': 'http://example.com/root.json',
        'properties': {
            'foo': {
                '$id': nested_id,
                '$defs': {'inner': {'properties': {'bar': {'type': 'string'}}}},
                '$ref': '#/$defs/inner',
            },
        },
        '$ref': 'nested.json',
    }, handlers={'http': refuse_handler})

    valid = {'foo': {'bar': 'a'}, 'bar': 'a'}
    assert validator(valid) == valid
    with pytest.raises(JsonSchemaException):
        validator({'foo': {'bar': 1}, 'bar': 'a'})
    with pytest.raises(JsonSchemaException):
        validator({'foo': {'bar': 'a'}, 'bar': 1})


def test_invalid_keyword_next_to_ref_is_reported_in_2019_09():
    with pytest.raises(JsonSchemaDefinitionException, match='maxItems must be a number'):
        compile({
            '$schema': DRAFT_2019,
            '$defs': {'list': {'type': 'array'}},
            'properties': {'p': {'$ref': '#/$defs/list', 'maxItems': 'one'}},
        })
