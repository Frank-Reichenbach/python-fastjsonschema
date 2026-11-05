import pytest

from fastjsonschema import JsonSchemaException, RefResolver, compile


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

    assert resolver.get_ref(resolver.schema['properties']['count']) == expected


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
