# pylint: disable=import-outside-toplevel

"""
JSON Schema URI resolution scopes and dereferencing

https://tools.ietf.org/id/draft-zyp-json-schema-04.html#rfc.section.7

Code adapted from https://github.com/Julian/jsonschema
"""

import contextlib
import json
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from typing import Any
from urllib import parse as urlparse
from urllib.parse import unquote

from .exceptions import JsonSchemaDefinitionException

# keywords whose values are data, not schemas
DATA_KEYWORDS = ('const', 'default', 'enum', 'examples')
# keywords whose values can be arrays of schemas (`items` can also be one schema)
SCHEMA_ARRAYS = ('allOf', 'anyOf', 'oneOf', 'items')
# keywords whose values map names to schemas
SCHEMA_MAPS = ('$defs', 'definitions', 'dependencies', 'dependentSchemas', 'patternProperties', 'properties')
MAX_SCHEMA_WALK_DEPTH = min(500, sys.getrecursionlimit() // 2)


def get_id(schema: dict[str, Any]) -> str:
    """
    Originally ID was `id` and since v7 it's `$id`.
    """
    return schema.get('$id', schema.get('id', ''))


def resolve_path(schema: Any, fragment: str) -> Any:
    """
    Return definition from path.

    Path is unescaped according https://tools.ietf.org/html/rfc6901
    """
    fragment = fragment.lstrip('/')
    parts = unquote(fragment).split('/') if fragment else []
    for part in parts:
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(schema, list):
            schema = schema[int(part)]
        elif part in schema:
            schema = schema[part]
        else:
            raise JsonSchemaDefinitionException('Unresolvable ref: {}'.format(part))
    return schema


def normalize(uri: str) -> str:
    return urlparse.urlsplit(uri).geturl()


def subschemas(node: dict[str, Any]) -> Iterator[tuple[dict[str, Any], int]]:
    """
    Yield the subschemas of ``node`` that are objects, with how many levels below ``node`` they are.
    """
    for key, item in node.items():
        if key in DATA_KEYWORDS:
            continue
        if key in SCHEMA_ARRAYS and isinstance(item, list):
            for sub in item:
                if isinstance(sub, dict):
                    yield sub, 2
        elif key in SCHEMA_MAPS and isinstance(item, dict):
            for sub in item.values():
                if isinstance(sub, dict):
                    yield sub, 2
        elif isinstance(item, dict):
            yield item, 1


def resolve_remote(uri: str, handlers: Mapping[str, Callable[[str], Any]]) -> Any:
    """
    Resolve a remote ``uri``.

    .. note::

        urllib library is used to fetch requests from the remote ``uri``
        if handlers does notdefine otherwise.
    """
    scheme = urlparse.urlsplit(uri).scheme
    if scheme in handlers:
        result = handlers[scheme](uri)
    else:
        from urllib.request import urlopen

        with urlopen(uri) as response:
            encoding = response.info().get_content_charset() or 'utf-8'
            try:
                result = json.loads(response.read().decode(encoding),)
            except ValueError as exc:
                raise JsonSchemaDefinitionException('{} failed to decode'.format(uri)) from exc
    return result


# pylint: disable=too-many-instance-attributes
class RefResolver:
    """
    Resolve JSON References.
    """

    # pylint: disable=dangerous-default-value,too-many-arguments
    def __init__(
        self,
        base_uri: str,
        schema: dict[str, Any] | bool,
        store: dict[str, Any] = {},
        cache: bool = True,
        handlers: Mapping[str, Callable[[str], Any]] = {},
    ) -> None:
        """
        `base_uri` is URI of the referring document from the `schema`.
        `store` is an dictionary that will be used to cache the fetched schemas
        (if `cache=True`).

        Please notice that you can have caching problems when compiling schemas
        with colliding `$ref`. To force overwriting use `cache=False` or
        explicitly pass the `store` argument (with a brand new dictionary)
        """
        self.base_uri = base_uri
        self.resolution_scope = base_uri
        self.schema = schema
        self.store = store
        self.cache = cache
        self.handlers = handlers
        self._walked_uris: set[str] = set()
        # The $refs that walk() resolved, by id() of the object with the $ref. The schema itself
        # stays unchanged: its objects can be part of other schemas with other base URIs.
        # Holding the object keeps its id from being reused while the resolver exists.
        self._resolved_refs: dict[int, tuple[dict[str, Any], str]] = {}
        self.walk(schema)
        self._walked_uris.add(normalize(base_uri) if base_uri else '')

    @classmethod
    def from_schema(
        cls,
        schema: dict[str, Any] | bool,
        handlers: Mapping[str, Callable[[str], Any]] = {},
        **kwargs: Any,
    ) -> 'RefResolver':
        """
        Construct a resolver from a JSON schema object.
        """
        return cls(
            get_id(schema) if isinstance(schema, dict) else '',
            schema,
            handlers=handlers,
            **kwargs
        )

    @contextlib.contextmanager
    def in_scope(self, scope: str) -> Iterator[None]:
        """
        Context manager to handle current scope.
        """
        old_scope = self.resolution_scope
        self.resolution_scope = urlparse.urljoin(old_scope, scope)
        try:
            yield
        finally:
            self.resolution_scope = old_scope

    @contextlib.contextmanager
    def resolving(self, ref: str) -> Iterator[Any]:
        """
        Context manager which resolves a JSON ``ref`` and enters the
        resolution scope of this ref.
        """
        new_uri = urlparse.urljoin(self.resolution_scope, ref)
        uri, fragment = urlparse.urldefrag(new_uri)

        document_uri = uri or self.base_uri

        if uri and normalize(uri) in self.store:
            schema = self.store[normalize(uri)]
        elif not uri or uri == self.base_uri:
            schema = self.schema
        else:
            schema = resolve_remote(uri, self.handlers)
            if self.cache:
                self.store[normalize(uri)] = schema

        old_base_uri, old_schema = self.base_uri, self.schema
        self.base_uri, self.schema = document_uri, schema
        try:
            with self.in_scope(document_uri):
                self._ensure_walked(document_uri, schema)
                if fragment and not fragment.startswith('/'):
                    plain_name = normalize(urlparse.urljoin(document_uri, '#' + fragment))
                    if plain_name in self.store:
                        yield self.store[plain_name]
                        return
                    raise JsonSchemaDefinitionException('Unresolvable ref: {}'.format(fragment))
                yield resolve_path(schema, fragment)
        finally:
            self.base_uri, self.schema = old_base_uri, old_schema

    def _ensure_walked(self, uri: str, schema: Any) -> None:
        normalized = normalize(uri) if uri else ''
        if normalized in self._walked_uris:
            return
        self.walk(schema, rewrite_refs=False)
        self._walked_uris.add(normalized)

    def get_ref(self, node: dict[str, Any]) -> str:
        """
        The ``$ref`` of ``node``, resolved against its base URI if ``walk`` reached it.
        """
        resolved = self._resolved_refs.get(id(node))
        return node['$ref'] if resolved is None else resolved[1]

    def get_uri(self) -> str:
        return normalize(self.resolution_scope)

    def get_scope_name(self) -> str:
        """
        Get current scope and return it as a valid function name.
        """
        name = 'validate_' + unquote(self.resolution_scope).replace('~1', '_').replace('~0', '_').replace('"', '')
        name = re.sub(r'($[^a-zA-Z]|[^a-zA-Z0-9])', '_', name)
        name = name.lower().rstrip('_')
        return name

    def walk(self, node: dict[str, Any] | bool, depth: int = 0, rewrite_refs: bool = True) -> None:
        """
        Walk thru schema, register ``id`` and resolve ``$ref`` instances. The schema
        stays unchanged; the resolved ``$ref`` values are available through ``get_ref``.
        """
        if depth >= MAX_SCHEMA_WALK_DEPTH:
            raise JsonSchemaDefinitionException(
                'Schema is too deeply nested (maximum depth is {})'.format(MAX_SCHEMA_WALK_DEPTH)
            )

        if isinstance(node, bool):
            pass
        elif '$ref' in node and isinstance(node['$ref'], str):
            # The first base URI wins if the same object is reached again under another one.
            if rewrite_refs and id(node) not in self._resolved_refs:
                self._resolved_refs[id(node)] = (node, urlparse.urljoin(self.resolution_scope, node['$ref']))
        elif ('$id' in node or 'id' in node) and isinstance(get_id(node), str):
            with self.in_scope(get_id(node)):
                self.store[normalize(self.resolution_scope)] = node
                for sub, levels in subschemas(node):
                    self.walk(sub, depth + levels, rewrite_refs)
        else:
            for sub, levels in subschemas(node):
                self.walk(sub, depth + levels, rewrite_refs)
