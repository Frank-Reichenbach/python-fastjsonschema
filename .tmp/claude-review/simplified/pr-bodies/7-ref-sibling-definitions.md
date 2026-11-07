Fixes #{I_SIB}.

**Needs all the other resolver PRs.** Its base branch `simple/integration-base` is a merge of #{P_URN}, #{P_ARRAYS} and #{P_HANDLER} with their bases, so the diff shows only this change. Once those are merged, retarget it to `master`. Overview: #{META}.

`walk()` didn't descend into a schema object with a `$ref`. If that object also had `definitions` and another `$ref` pointed into them, the schemas there lost their `$id`. A common form is `{"$ref": "#/definitions/a", "definitions": {"a": {"$id": ...}}}`.

## Changes

- Next to a `$ref`, `walk()` also descends into the schemas under `definitions` and `$defs`, and into no other keyword there. Draft-07 says the other keywords of a `$ref` object must be ignored, and walking an unknown one could register an `$id` from data.
- **An `$id` next to the `$ref`** is where the drafts differ. Draft-04 to draft-07 ignore it, so the definitions are walked in the outer scope. In 2019-09, the `$id` identifies the object and is the base URI of the `$ref` and of the definitions next to it. In the root schema, and at the root of a loaded schema, nothing changes.
- **The draft comes from the code generator.** `ID_NEXT_TO_REF` is `True` on `CodeGeneratorDraft2019` and `False` on the earlier drafts. `compile()`, `compile_to_code()` and a generator that builds its own resolver pass it to `RefResolver` as `id_next_to_ref`. A `RefResolver` created without it reads the draft from `$schema`, with the rule of `_get_code_generator_class()`. The test-suite harness builds its debug resolver and generator for the draft it tests; it used to print 2019-09 code for every draft.
- The `compile()` docstring says that 2019-09 is used without `$schema`, as the code does. It used to say draft-07.

## Behavior changes (in the CHANGELOG)

- Schemas without `$schema` use 2019-09, so in them an `$id` next to a `$ref` now counts. Such a `$ref` can no longer point into the outer schema with `#/...`; it raises `JsonSchemaDefinitionException`. A relative `$ref` there resolves against that `$id`.
- Schemas under `definitions` and `$defs` next to a `$ref` count toward the nesting limit, as schemas everywhere else do.

## Tests

`tests/test_ref_siblings.py`.
- On the base branch, 47 of the 56 cases that can run there fail. `test_resolver_reads_the_draft_like_the_compiler` can't run there, because `id_next_to_ref_applies()` is new.
- 9 cases pass there and guard what must stay ignored: `id` next to a `$ref`, other keywords next to a `$ref`, and data next to a `$ref`.
- Official suite: 11 cases of 2019-09 `ref.json`, `refRemote.json`, `unevaluatedItems.json` and `unevaluatedProperties.json` pass now. Those files stay listed as expected failures, because other cases in them still fail, so the new passes show as XPASS.
