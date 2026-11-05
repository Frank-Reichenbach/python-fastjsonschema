import pytest

from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaValueException, compile, compile_to_code
from fastjsonschema.ref_resolver import RefResolver, resolve_path


def from_code(schema, **options):
    namespace = {}
    exec(compile_to_code(schema, **options), namespace)
    return namespace['validate']


@pytest.mark.parametrize('pointer, expected', [
    ('', {'': {'': 'empty in empty', 'a/b': 'slash', 'm~n': 'tilde', 'é': 'encoded', 'x': 'plain'}, 'x': 'top'}),
    ('/', {'': 'empty in empty', 'a/b': 'slash', 'm~n': 'tilde', 'é': 'encoded', 'x': 'plain'}),
    ('//', 'empty in empty'),
    ('//x', 'plain'),
    ('//a~1b', 'slash'),
    ('//m~0n', 'tilde'),
    ('//%C3%A9', 'encoded'),
    ('/x', 'top'),
])
def test_resolve_path_keeps_empty_keys(pointer, expected):
    document = {'': {'': 'empty in empty', 'a/b': 'slash', 'm~n': 'tilde', 'é': 'encoded', 'x': 'plain'}, 'x': 'top'}

    assert resolve_path(document, pointer) == expected


def test_resolve_path_without_leading_slash_and_through_array():
    document = {'allOf': [{'type': 'null'}, {'type': 'string'}]}

    assert resolve_path(document, 'allOf/1') == {'type': 'string'}
    assert resolve_path(document, '/allOf/1') == {'type': 'string'}


def test_empty_key_that_does_not_exist_is_unresolvable():
    with pytest.raises(JsonSchemaDefinitionException, match='Unresolvable ref'):
        compile({'properties': {'p': {'$ref': '#/'}}})


@pytest.mark.parametrize('build', [compile, from_code])
@pytest.mark.parametrize('ref, target', [
    ('#/', {'type': 'integer'}),
    ('#//', {'': {'type': 'integer'}}),
    ('#//nested', {'nested': {'type': 'integer'}}),
])
def test_ref_through_empty_key(build, ref, target):
    validator = build({'': target, 'type': 'object', 'properties': {'p': {'$ref': ref}}})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaValueException):
        validator({'p': 'text'})
    with pytest.raises(JsonSchemaValueException):
        validator(1)


@pytest.mark.parametrize('build', [compile, from_code])
def test_ref_through_empty_key_in_loaded_schema(build):
    document = {'': {'type': 'integer'}, 'type': 'object', 'properties': {'p': {'$ref': '#/'}}}
    validator = build({'$ref': 'http://example.com/doc.json'}, handlers={'http': lambda uri: document})

    assert validator({'p': 1}) == {'p': 1}
    with pytest.raises(JsonSchemaValueException):
        validator({'p': 'text'})


def test_function_names_of_empty_keys_differ_from_the_root():
    resolver = RefResolver.from_schema({})
    root = resolver.get_scope_name()
    with resolver.in_scope('#/'):
        one_key = resolver.get_scope_name()
    with resolver.in_scope('#//'):
        two_keys = resolver.get_scope_name()
    with resolver.in_scope('#'):
        assert resolver.get_scope_name() == root
    with resolver.in_scope('#/'):
        assert resolver.get_scope_name() == one_key

    assert len({root, one_key, two_keys}) == 3
