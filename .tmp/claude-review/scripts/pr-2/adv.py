"""Adversarial cases for PR #2: compare fastjsonschema (on PYTHONPATH) with jsonschema."""
import copy
import sys
import warnings

import fastjsonschema
import jsonschema
import referencing
import referencing.jsonschema

warnings.simplefilter('ignore')

D4 = "http://json-schema.org/draft-04/schema#"
D6 = "http://json-schema.org/draft-06/schema#"
D7 = "http://json-schema.org/draft-07/schema#"
D2019 = "https://json-schema.org/draft/2019-09/schema"
D2020 = "https://json-schema.org/draft/2020-12/schema"


def node(node_id, id_key="$id", extra=None):
    n = {
        id_key: node_id,
        "type": "object",
        "properties": {
            "all": {"type": "array", "items": {"$ref": "#"}},
            "eq": {"type": "array", "maxItems": 2},
        },
        "additionalProperties": False,
    }
    if extra:
        n.update(extra)
    return n


def fjs(schema, data, **kw):
    try:
        v = fastjsonschema.compile(copy.deepcopy(schema), **kw)
    except fastjsonschema.JsonSchemaDefinitionException as e:
        return 'DEF-ERR: %s' % e
    except Exception as e:  # noqa
        return 'COMPILE-%s: %s' % (type(e).__name__, str(e)[:80])
    try:
        v(copy.deepcopy(data))
        return 'valid'
    except fastjsonschema.JsonSchemaException as e:
        return 'invalid'
    except Exception as e:  # noqa
        return 'RUN-%s: %s' % (type(e).__name__, str(e)[:80])


def oracle(schema, data, resources=()):
    s = copy.deepcopy(schema)
    sch = s.get('$schema', D2019) if isinstance(s, dict) else D2019
    cls = jsonschema.validators.validator_for({'$schema': sch})
    spec = referencing.jsonschema.specification_with(cls.META_SCHEMA['$schema'] if '$schema' in cls.META_SCHEMA else sch)
    reg = referencing.Registry().with_resources(
        [(uri, referencing.Resource(contents=r, specification=spec)) for uri, r in resources])
    try:
        v = cls(s, registry=reg)
        errs = list(v.iter_errors(copy.deepcopy(data)))
        return 'invalid' if errs else 'valid'
    except Exception as e:  # noqa
        return 'ORACLE-%s' % type(e).__name__


CASES = []


def case(label, schema, data, resources=(), **kw):
    CASES.append((label, schema, data, resources, kw))


bad = {"p": {"all": [{"eq": [1, 2, 3]}]}}
good = {"p": {"all": [{"eq": [1, 2]}]}}

# schemes
for sid in ["urn:example:node", "urn:uuid:ee564b8a-7a87-4125-8c96-e9f123d6766f", "tag:example.com,2026:node",
            "mailto:a@example.com", "myapp:/schemas/node", "myapp://host/node", "s3://bucket/node.json",
            "data:,node", "urn:example:node?=q", "urn:example:node?+r", "URN:EXAMPLE:NODE",
            "urn:example:node#", "http://example.com/node.json", "file:///s/node.json", "node.json",
            "x-y.z+w:node", "urn:ex:{node}", 'urn:ex:"q"', "urn:ex:a%23b"]:
    for d in (bad, good):
        case("scheme %-48s %s" % (sid, 'bad' if d is bad else 'good'), {"$schema": D7, "properties": {"p": node(sid)}}, d)

# nested urn inside urn: inner '#' must point to inner
inner = {"$id": "urn:ex:inner", "properties": {"x": {"type": "integer"}, "self": {"$ref": "#"}}}
outer = {"$id": "urn:ex:outer", "properties": {"x": {"type": "string"}, "in": inner, "self": {"$ref": "#"}}}
nested = {"$schema": D7, "properties": {"o": outer}}
case("nested urn: inner self x=1", nested, {"o": {"in": {"self": {"x": 1}}}})
case("nested urn: inner self x='a'", nested, {"o": {"in": {"self": {"x": "a"}}}})
case("nested urn: outer self x='a'", nested, {"o": {"self": {"x": "a"}}})
case("nested urn: outer self x=1", nested, {"o": {"self": {"x": 1}}})

# plain-name $id inside urn, then '#' inside that plain-name subschema -> still the urn doc
pn = {"$schema": D7, "properties": {"p": {
    "$id": "urn:ex:pn", "properties": {"k": {"type": "integer"}, "f": {"$ref": "#foo"}},
    "definitions": {"foo": {"$id": "#foo", "properties": {"back": {"$ref": "#"}}}}}}}
case("plain-name then # back to urn doc: k=1", pn, {"p": {"f": {"back": {"k": 1}}}})
case("plain-name then # back to urn doc: k='a'", pn, {"p": {"f": {"back": {"k": "a"}}}})

# relative non-fragment ref under urn (not fixed; urljoin leaves it unchanged)
rel = {"$schema": D7, "properties": {"p": {"$id": "urn:ex:a", "properties": {"v": {"$ref": "b"}}}},
       "definitions": {"b": {"$id": "b", "type": "integer"}}}
case("relative 'b' under urn (root defines $id b)", rel, {"p": {"v": "x"}})
rel2 = {"$schema": D7, "properties": {"p": {"$id": "s3://bucket/a.json", "properties": {"v": {"$ref": "b.json"}}}},
        "definitions": {"b": {"$id": "s3://bucket/b.json", "type": "integer"}}}
case("relative 'b.json' under s3:// (s3://bucket/b.json exists)", rel2, {"p": {"v": "x"}})

# boolean target
bt = {"$schema": D7, "properties": {"p": {"$id": "urn:ex:b", "definitions": {"f": False},
                                          "properties": {"v": {"$ref": "#/definitions/f"}}}}}
case("bool false target under urn: v present", bt, {"p": {"v": 1}})
case("bool false target under urn: v absent", bt, {"p": {}})

# root urn id with # refs
ru = {"$schema": D7, "$id": "urn:ex:root", "definitions": {"i": {"type": "integer"}},
      "properties": {"a": {"$ref": "#/definitions/i"}, "r": {"$ref": "#"}}}
case("root urn: a=1", ru, {"a": 1})
case("root urn: r.a='x'", ru, {"r": {"a": "x"}})

# handler-loaded doc without $id, with '#' inside
remote = {"properties": {"x": {"type": "integer"}, "self": {"$ref": "#"}}}
hs = {"$schema": D7, "properties": {"p": {"$ref": "urn:ex:remote"}}}
calls = []


def handler(uri):
    calls.append(uri)
    return copy.deepcopy(remote)


for cache in (True, False):
    case("handler no-$id remote cache=%s x='a' deep" % cache, hs, {"p": {"self": {"self": {"x": "a"}}}},
         resources=[("urn:ex:remote", remote)], handlers={"urn": handler}, use_default=True)

# draft 2020 / 2019 with $anchor? (fastjsonschema does not support $anchor; skip) - $defs
d2020 = {"$schema": D2020, "properties": {"p": {"$id": "urn:ex:d", "$defs": {"i": {"type": "integer"}},
                                                "properties": {"v": {"$ref": "#/$defs/i"}}}}}
case("2020-12 $defs under urn v='a'", d2020, {"p": {"v": "a"}})
case("2020-12 $defs under urn v=1", d2020, {"p": {"v": 1}})

# pointer with escaped chars under urn
esc = {"$schema": D7, "properties": {"p": {"$id": "urn:ex:e", "definitions": {"a/b": {"type": "integer"}, "c%d": {"type": "string"}},
                                           "properties": {"v": {"$ref": "#/definitions/a~1b"}, "w": {"$ref": "#/definitions/c%25d"}}}}}
case("escaped pointer under urn v='x'", esc, {"p": {"v": "x"}})
case("escaped pointer under urn w=1", esc, {"p": {"w": 1}})
case("escaped pointer under urn ok", esc, {"p": {"v": 1, "w": "s"}})

# urn subschema refs root definitions (now DEF-ERR)
fb = {"$schema": D7, "definitions": {"x": {"type": "string"}},
      "properties": {"p": {"$id": "urn:ex:item", "properties": {"v": {"$ref": "#/definitions/x"}}}}}
case("urn sub refs root-only def", fb, {"p": {"v": 1}})

for fast_fail in (True, False):
    for label, schema, data, resources, kw in CASES:
        if not fast_fail and kw.get('handlers'):
            continue
        calls.clear()
        r = fjs(schema, data, fast_fail=fast_fail, **kw)
        o = oracle(schema, data, resources)
        flag = '' if r == o else '   <-- differs from jsonschema'
        extra = ' handler_calls=%d' % len(calls) if kw.get('handlers') else ''
        print('ff=%-5s %-72s fjs=%-12s js=%-8s%s%s' % (fast_fail, label, r[:60], o, extra, flag))
