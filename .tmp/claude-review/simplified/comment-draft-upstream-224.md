# Draft comment for horejsek/python-fastjsonschema#224 (NOT posted; post it yourself if you want)

Posting on someone else's upstream PR is public, so this was only drafted.

---

Thanks for this. We ran into the same function-name collisions while working on `$ref` resolution, and checked this PR against our cases: all of them pass. A few observations, in case they're useful:

1. **Cases this PR fixes, and that might be worth tests:**
   - targets that differ only in case (`#/definitions/Address` vs `#/definitions/address`);
   - targets that differ in `-` vs `_`, `/` (as `~1`) vs `_`, non-ASCII letters (`größe` vs `grüße`), or a trailing `_` (`id` vs `id_`);
   - two `$id`s that differ only in punctuation (`http://example.com/user-id.json` vs `.../user_id.json`);
   - a `$ref` whose target gets the root function's name, such as `#/-`. Before this PR, `compile()` returned the validator of the referenced schema instead of the whole schema.

   All of these pass with `fast_fail` on and off.

2. **`?#/definitions/ab` next to `#/definitions/ab`:** this one still fails with `ValueError: unknown url type: '?'` as soon as the enclosing schema has a keyword such as `type`. The cause isn't naming: `RefResolver.resolving()` compares the URI before normalization (`elif not uri or uri == self.base_uri:`). This one-line change fixes it:

   ```python
   elif not normalize(uri) or normalize(uri) == normalize(self.base_uri):
   ```

   We ran the full test suite with it, and it stays green. The change may be out of scope for this PR.

3. **Interaction with a `urn:` fix:** with a root `$id` like `urn:example:root`, `#foo` should resolve to `urn:example:root#foo`. Once it does, its function name is the same as the one for `urn:example:root:foo`, and this PR keeps the two apart. Test case:

   ```python
   {'$id': 'urn:example:root',
    'definitions': {'a': {'$id': '#foo', 'type': 'integer'},
                    'b': {'$id': 'urn:example:root:foo', 'type': 'string'}},
    'properties': {'a': {'$ref': '#foo'}, 'b': {'$ref': 'urn:example:root:foo'}}}
   ```

   `{'a': 1, 'b': 'x'}` must be valid.
