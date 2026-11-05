import copy

import pytest

from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaException, RefResolver, compile
from fastjsonschema.draft07 import CodeGeneratorDraft07


def refuse_handler(uri):
    raise RuntimeError('handler called for ' + uri)


HANDLER_DOC = {
    '$id': 'http://example.com/doc.json',
    'definitions': {'x': {'type': 'string'}},
    'properties': {'p': {
        '$id': 'http://example.com/node.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'v': {'$ref': '#/definitions/x'}},
    }},
}


@pytest.mark.parametrize('scheme, uri', [
    ('http', 'http://example.com/doc.json'),
    ('', 'schemas/main.json'),
    ('file', 'file:schemas/main.json'),
])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_ref_in_handler_loaded_schema_uses_id_of_its_subschema(scheme, uri, fast_fail):
    validator = compile(
        {'$ref': uri},
        handlers={scheme: lambda loaded_uri: copy.deepcopy(HANDLER_DOC)},
        fast_fail=fast_fail,
    )

    assert validator({'p': {'v': 1}}) == {'p': {'v': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'v': 'a'}})


@pytest.mark.parametrize('uri, schema_id', [
    ('http://example.com/a/main.json', 'b/main.json'),
    ('http://example.com/a/main.json', 'http://other.example.com/x/main.json'),
    ('dir/main.json', 'dir/main.json'),
    ('dir/main.json', 'other/main.json'),
])
def test_id_of_handler_loaded_schema_keeps_its_uri_as_base(uri, schema_id):
    # As in 2.22.3 and jsonschema: the $id of a loaded schema doesn't change its base URI.
    loaded = []

    def handler(loaded_uri):
        loaded.append(loaded_uri)
        if loaded_uri == uri:
            return {'$id': schema_id, 'properties': {'c': {'$ref': 'child.json'}}}
        return {'type': 'integer'}

    validator = compile({'$ref': uri}, handlers={'http': handler, '': handler})

    assert validator({'c': 1}) == {'c': 1}
    assert loaded == [uri, uri.rsplit('/', 1)[0] + '/child.json']


def test_ref_to_id_of_handler_loaded_schema_finds_it():
    def handler(uri):
        if uri == 'http://example.com/a/main.json':
            return {
                '$id': 'http://other.example.com/x/main.json',
                'definitions': {'i': {'type': 'integer'}},
                'properties': {'c': {'$ref': 'http://other.example.com/x/main.json#/definitions/i'}},
            }
        raise AssertionError('handler called with ' + uri)

    validator = compile({'$ref': 'http://example.com/a/main.json'}, handlers={'http': handler})

    assert validator({'c': 1}) == {'c': 1}
    with pytest.raises(JsonSchemaException):
        validator({'c': 'a'})


def test_relative_ref_in_handler_loaded_schema_is_resolved_once():
    loaded = []

    def handler(uri):
        loaded.append(uri)
        if uri == 'schemas/main.json':
            return {'properties': {'v': {'$ref': '../other.json'}}}
        return {'type': 'string'}

    validator = compile({'$ref': 'schemas/main.json'}, handlers={'': handler})

    assert validator({'v': 'a'}) == {'v': 'a'}
    assert loaded == ['schemas/main.json', 'other.json']


def test_ref_under_id_without_host_in_handler_loaded_schema_is_resolved_once():
    doc = {
        '$id': 'http://example.com/doc.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'p': {
            '$id': 'file:///node.json',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {'v': {'$ref': '#/definitions/x'}},
        }},
    }

    def handler(uri):
        if uri == 'file://server/schemas/main.json':
            return copy.deepcopy(doc)
        raise AssertionError('handler called with ' + uri)

    # walk() resolves the $ref to file:///node.json#/definitions/x. Resolved again against
    # file://server/schemas/main.json, it would turn into file://server/node.json#/definitions/x.
    validator = compile({'$ref': 'file://server/schemas/main.json'}, handlers={'file': handler})

    assert validator({'p': {'v': 1}}) == {'p': {'v': 1}}


def test_handler_loaded_schema_without_cache():
    doc = {
        'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {
            '$id': 'http://example.com/node.json',
            'definitions': {'x': {'type': 'integer'}},
            'properties': {'v': {'$ref': '#/definitions/x'}},
        }},
    }
    loaded = []

    def handler(uri):
        loaded.append(uri)
        return copy.deepcopy(doc)

    # Without cache, each ref into the document loads it again, as a new object that is walked too.
    schema = {'properties': {
        'a': {'$ref': 'http://example.com/doc.json#/properties/p'},
        'b': {'$ref': 'http://example.com/doc.json'},
    }}
    resolver = RefResolver.from_schema(schema, handlers={'http': handler}, store={}, cache=False)
    code_generator = CodeGeneratorDraft07(schema, resolver=resolver)
    global_state = code_generator.global_state
    exec(code_generator.func_code, global_state)  # pylint: disable=exec-used
    validator = global_state[resolver.get_scope_name()]

    data = {'a': {'v': 1}, 'b': {'p': {'v': 1}}}
    assert validator(data) == data
    for invalid in ({'a': {'v': 'x'}}, {'b': {'p': {'v': 'x'}}}):
        with pytest.raises(JsonSchemaException):
            validator(invalid)
    assert loaded == ['http://example.com/doc.json', 'http://example.com/doc.json']


def test_invalid_uri_in_unknown_keyword_of_handler_loaded_schema():
    validator = compile(
        {'$ref': 'http://example.com/doc.json'},
        handlers={'http': lambda uri: {'x-note': {'$ref': 'http://[bad'}}},
    )

    assert validator({}) == {}


def test_invalid_uri_in_unknown_keyword_of_schema_with_id():
    validator = compile({'$id': 'http://example.com/root.json', 'x-note': {'$ref': 'http://[bad'}, 'type': 'integer'})

    assert validator(1) == 1


def test_used_ref_that_is_not_a_valid_uri_fails():
    with pytest.raises(ValueError):
        compile({'properties': {'p': {'$ref': 'http://[bad'}}})


@pytest.mark.parametrize('fast_fail', [True, False])
def test_handler_returning_the_same_objects_compiled_twice(fast_fail):
    repo = {
        'schemas/main.json': {
            'definitions': {
                'object': {'type': 'object', 'properties': {'value': {'$ref': 'main.json#/definitions/string'}}},
                'string': {'type': 'string'},
            },
        },
    }

    for _ in range(2):
        validator = compile(
            {'$ref': 'schemas/main.json#/definitions/object'}, handlers={'': repo.__getitem__}, fast_fail=fast_fail,
        )
        assert validator({'value': 'ok'}) == {'value': 'ok'}
        with pytest.raises(JsonSchemaException):
            validator({'value': 1})


def test_handler_loaded_schema_compiled_directly_afterwards():
    loaded = {'definitions': {'s': {'type': 'string'}}, 'properties': {'v': {'$ref': '#/definitions/s'}}}
    compile({'properties': {'b': {'$ref': 'http://example.com/b.json'}}}, handlers={'http': lambda uri: loaded})

    validator = compile(loaded, handlers={'http': refuse_handler})

    assert validator({'v': 'a'}) == {'v': 'a'}
    with pytest.raises(JsonSchemaException):
        validator({'v': 1})


def documents_with_shared_ref(shared_document):
    ref = {'$ref': 'defs.json'}
    document = {'properties': {'c': ref}}
    return {
        'http://example.com/a/doc.json': document if shared_document else {'properties': {'c': ref}},
        'http://example.com/b/doc.json': document if shared_document else {'properties': {'c': ref}},
        'http://example.com/a/defs.json': {'type': 'string'},
        'http://example.com/b/defs.json': {'type': 'integer'},
    }


@pytest.mark.parametrize('shared_document', [True, False], ids=['same document', 'same subschema'])
@pytest.mark.parametrize('fast_fail', [True, False])
def test_objects_shared_by_handler_loaded_schemas(shared_document, fast_fail):
    documents = documents_with_shared_ref(shared_document)
    validator = compile({
        'properties': {
            'a': {'$ref': 'http://example.com/a/doc.json'},
            'b': {'$ref': 'http://example.com/b/doc.json'},
        },
    }, handlers={'http': documents.__getitem__}, fast_fail=fast_fail)

    assert validator({'a': {'c': 'x'}, 'b': {'c': 1}}) == {'a': {'c': 'x'}, 'b': {'c': 1}}
    with pytest.raises(JsonSchemaException):
        validator({'a': {'c': 1}})
    with pytest.raises(JsonSchemaException):
        validator({'b': {'c': 'x'}})


def test_handler_serving_an_object_that_was_compiled_before():
    doc = {
        '$id': 'http://example.com/doc.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'p': {
            '$id': 'http://example.com/sub/node.json',
            'definitions': {'x': {'type': 'string'}},
            'properties': {'q': {'$ref': '#/definitions/x'}},
        }},
    }
    compile(doc)
    validator = compile({'$ref': 'http://example.com/doc.json'}, handlers={'http': lambda uri: doc})

    assert validator({'p': {'q': 'text'}}) == {'p': {'q': 'text'}}
    with pytest.raises(JsonSchemaException):
        validator({'p': {'q': 1}})
