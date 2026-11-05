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
# keywords whose values are one schema (`items` is in SCHEMA_ARRAYS)
SCHEMA_VALUES = (
    'additionalItems', 'additionalProperties', 'contains', 'contentSchema', 'else', 'if', 'items', 'not',
    'propertyNames', 'then', 'unevaluatedItems', 'unevaluatedProperties',
)
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
    if not fragment:
        return schema
    # Only one "/": each further one starts a token, and that token can be empty.
    parts = unquote(fragment.removeprefix('/')).split('/')
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


def subschemas(node: dict[str, Any]) -> Iterator[tuple[dict[str, Any], int, bool]]:
    """
    Yield the subschemas of ``node`` that are objects, with how many levels below ``node`` they are,
    and whether they are the value of a keyword that isn't known to hold a schema.
    """
    for key, item in node.items():
        if key in DATA_KEYWORDS:
            continue
        if key in SCHEMA_ARRAYS and isinstance(item, list):
            for sub in item:
                if isinstance(sub, dict):
                    yield sub, 2, False
        elif key in SCHEMA_MAPS and isinstance(item, dict):
            for sub in item.values():
                if isinstance(sub, dict):
                    yield sub, 2, False
        elif isinstance(item, dict):
            yield item, 1, key not in SCHEMA_VALUES


def join_uri(base: str, ref: str) -> str:
    """
    Resolve ``ref`` against ``base`` with ``urljoin``.

    ``urljoin`` returns a fragment-only ``ref`` (``#...``) unchanged when the scheme of
    ``base`` is not in ``urllib.parse.uses_relative``, for example ``urn:``. For such
    a ``ref``, keep ``base`` and replace its fragment instead, as defined in
    https://tools.ietf.org/html/rfc3986#section-5.2.2. The fragment is everything
    after the first ``#``.
    """
    if ref.startswith('#'):
        # Only for schemes that urljoin doesn't handle. For the others, keep urljoin's result as it was:
        # urljoin also normalizes the URI, for example it lowercases the scheme.
        if urlparse.urlsplit(base).scheme not in urlparse.uses_relative:
            # Not urldefrag: it normalizes the URI only when it has a fragment, differently per Python version.
            return base.partition('#')[0] + ref
    return urlparse.urljoin(base, ref)


def copy_document(node: Any, depth: int = 0) -> Any:
    """
    Copy the objects and arrays of a document, so that each place in it has its own objects.
    Any mapping becomes a ``dict``.

    ``copy.deepcopy`` keeps shared objects shared, and it fails with ``RecursionError`` on a deep
    document. This stops at the depth limit of ``walk``, and data that deep can't be compiled
    either. Loops instead of comprehensions keep it at one stack frame per level on every Python
    version.
    """
    if depth >= MAX_SCHEMA_WALK_DEPTH:
        raise JsonSchemaDefinitionException(
            'Schema is too deeply nested (maximum depth is {})'.format(MAX_SCHEMA_WALK_DEPTH)
        )
    copied: Any
    if isinstance(node, Mapping):
        copied = {}
        for key, value in node.items():
            copied[key] = copy_document(value, depth + 1)
        return copied
    if isinstance(node, list):
        copied = []
        for item in node:
            copied.append(copy_document(item, depth + 1))
        return copied
    return node


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
        *,
        base_uri_is_id: bool = False,
        keywords_next_to_ref: bool = False,
    ) -> None:
        """
        `base_uri` is URI of the referring document from the `schema`.
        `store` is an dictionary that will be used to cache the fetched schemas
        (if `cache=True`).
        `base_uri_is_id` says that `base_uri` is already the `$id` of the `schema`,
        as `from_schema` sets it, so that the `$id` isn't applied to it again.
        `keywords_next_to_ref` says that the keywords next to a `$ref` count, as in 2019-09.

        Please notice that you can have caching problems when compiling schemas
        with colliding `$ref`. To force overwriting use `cache=False` or
        explicitly pass the `store` argument (with a brand new dictionary).
        With `cache=False`, every `$ref` into a remote document loads, copies
        and walks that document again.
        """
        self.base_uri = base_uri
        self.resolution_scope = base_uri
        # A copy, so that each place in the schema has its own objects: walk() resolves the $refs of
        # an object once, and the same object can be used under several base URIs.
        self.schema = copy_document(schema)
        self.store = store
        self.cache = cache
        self.handlers = handlers
        # The schema objects walked so far, by id(). Holding them keeps their ids, and the ids of
        # the objects inside them, from being reused while the resolver exists.
        self._walked: dict[int, Any] = {id(self.schema): self.schema}
        # The function name of each URI, and how many URIs share each name before it is made unique.
        self._scope_names: dict[str, str] = {}
        self._scope_name_counts: dict[str, int] = {}
        # The $refs that walk() resolved, by id() of the object with the $ref. A table and not the
        # object itself, so that a $ref is resolved once and stays as written in error messages.
        self._resolved_refs: dict[int, str] = {}
        self._keywords_next_to_ref = keywords_next_to_ref
        self.walk(self.schema, id_applied=base_uri_is_id)

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
            base_uri_is_id=True,
            **kwargs
        )

    @contextlib.contextmanager
    def in_scope(self, scope: str, *, resolved: bool = False) -> Iterator[None]:
        """
        Context manager to handle current scope. A ``resolved`` scope is used as it is.
        """
        old_scope = self.resolution_scope
        self.resolution_scope = scope if resolved else join_uri(old_scope, scope)
        try:
            yield
        finally:
            self.resolution_scope = old_scope

    @contextlib.contextmanager
    def resolving(self, ref: str, *, resolved: bool = False) -> Iterator[Any]:
        """
        Context manager which resolves a JSON ``ref`` and enters the
        resolution scope of this ref. A ``resolved`` ref is used as it is.
        """
        new_uri = ref if resolved else join_uri(self.resolution_scope, ref)
        uri, fragment = urlparse.urldefrag(new_uri)

        document_uri = uri or self.base_uri

        if uri and normalize(uri) in self.store:
            schema = self.store[normalize(uri)]
        elif not normalize(uri) or normalize(uri) == normalize(self.base_uri):
            schema = self.schema
        else:
            # Handlers can return the same objects for several URIs.
            schema = copy_document(resolve_remote(uri, self.handlers))
            if self.cache:
                self.store[normalize(uri)] = schema

        old_base_uri, old_schema = self.base_uri, self.schema
        self.base_uri, self.schema = document_uri, schema
        try:
            with self.in_scope(document_uri, resolved=True):
                self._ensure_walked(schema)
                if fragment and not fragment.startswith('/'):
                    plain_name = normalize(join_uri(document_uri, '#' + fragment))
                    if plain_name in self.store:
                        yield self.store[plain_name]
                        return
                    raise JsonSchemaDefinitionException('Unresolvable ref: {}'.format(fragment))
                yield resolve_path(schema, fragment)
        finally:
            self.base_uri, self.schema = old_base_uri, old_schema

    def _ensure_walked(self, schema: Any) -> None:
        if id(schema) not in self._walked:
            self._walked[id(schema)] = schema
            self.walk(schema, loaded=True)

    def get_ref(self, node: dict[str, Any]) -> str:
        """
        The ``$ref`` of ``node``, resolved once: against its base URI if ``walk`` reached it,
        otherwise against the current scope.
        """
        resolved = self._resolved_refs.get(id(node))
        return join_uri(self.resolution_scope, node['$ref']) if resolved is None else resolved

    def get_uri(self) -> str:
        return normalize(self.resolution_scope)

    def get_scope_name(self) -> str:
        """
        Get current scope and return it as a valid function name: one name per URI, and different
        URIs get different names.
        """
        uri = self.get_uri()
        if uri not in self._scope_names:
            name = 'validate_' + unquote(self.resolution_scope).replace('~1', '_').replace('~0', '_').replace('"', '')
            name = re.sub(r'($[^a-zA-Z]|[^a-zA-Z0-9])', '_', name)
            name = name.lower().rstrip('_')
            count = self._scope_name_counts[name] = self._scope_name_counts.get(name, 0) + 1
            # A sanitized name never ends in "_", so a suffixed name is never the name of another URI.
            self._scope_names[uri] = name if count == 1 else '{}_{}_'.format(name, count)
        return self._scope_names[uri]

    def _resolve_ref(self, node: dict[str, Any]) -> None:
        # An object is only reached twice if a passed store holds it under two URIs: the first wins.
        # A $ref that isn't a valid URI stays as it is. If it is used, the generator reports it.
        if id(node) not in self._resolved_refs:
            with contextlib.suppress(ValueError):
                self._resolved_refs[id(node)] = join_uri(self.resolution_scope, node['$ref'])

    def walk(
        self,
        node: dict[str, Any] | bool,
        depth: int = 0,
        *,
        id_applied: bool = False,
        loaded: bool = False,
        unknown: bool = False,
    ) -> None:
        """
        Walk thru schema, register ``id`` and resolve ``$ref`` instances. The schema
        stays unchanged; the resolved ``$ref`` values are available through ``get_ref``.
        ``id_applied`` says that the ``$id`` of ``node`` is already the current scope.
        ``loaded`` says that ``node`` is the root of a loaded document, whose base URI
        is the current scope, the URI it was loaded from.
        ``unknown`` says that ``node`` is inside the value of a keyword that isn't known
        to hold a schema.
        """
        if depth >= MAX_SCHEMA_WALK_DEPTH:
            raise JsonSchemaDefinitionException(
                'Schema is too deeply nested (maximum depth is {})'.format(MAX_SCHEMA_WALK_DEPTH)
            )

        if isinstance(node, bool):
            return

        has_ref = '$ref' in node and isinstance(node['$ref'], str)
        if has_ref:
            # Draft-04 to draft-07 ignore every keyword next to a $ref. In 2019-09, they count, and
            # $id identifies the object and is the base URI of the $ref. (id isn't a keyword.)
            node_id = node.get('$id') if self._keywords_next_to_ref else None
            has_id = isinstance(node_id, str) and bool(node_id)
        else:
            node_id = get_id(node)
            has_id = ('$id' in node or 'id' in node) and isinstance(node_id, str)

        # As in 2.22.3 and jsonschema, the $id of a loaded document doesn't change its base URI.
        enters_scope = has_id and not loaded
        with self.in_scope(node_id, resolved=id_applied) if enters_scope else contextlib.nullcontext():
            if has_id:
                uri = normalize(self.resolution_scope if enters_scope else join_uri(self.resolution_scope, node_id))
                # An $id inside an unknown keyword isn't an identifier, but schemas keep subschemas
                # under custom keywords and refer to them by $id. It never replaces a real one.
                if not unknown or uri not in self.store:
                    self.store[uri] = node
                # A $ref to this $id resolves to this node, which must not be walked again.
                self._walked[id(node)] = node
            if has_ref:
                self._resolve_ref(node)
                # Before 2019-09, the other keywords next to a $ref are ignored, but another $ref
                # can point into the definitions there, so their $ids and $refs still count.
                if not self._keywords_next_to_ref:
                    node = {key: node[key] for key in ('$defs', 'definitions') if key in node}
            # The loop stays here: each level of the schema takes one stack frame, so the depth
            # limit raises JsonSchemaDefinitionException before Python's recursion limit.
            for sub, levels, in_unknown in subschemas(node):
                self.walk(sub, depth + levels, unknown=unknown or in_unknown)
