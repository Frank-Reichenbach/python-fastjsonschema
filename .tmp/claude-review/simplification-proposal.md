# Proposal: simplifying the resolver-fix chain (issues #1, #3–#7, #13, #15 / PRs #2, #8–#12, #14, #16)

Date: 2026-11-03 · Builds on `README.md` (the review; finding IDs like C2 or "#11 F1" refer to it).
Constraint from the request: issue descriptions shouldn't get longer and PRs shouldn't get larger. Every proposal below says what it does to size.

## TL;DR

1. **Don't submit #8 and #3; use upstream #224 instead.** Upstream horejsek#224 (open, someone else's) passes all 18 tests of #8. The rest of the stack without #8, on top of #224, passes the full suite (5139 passed, 0 failed). Offer #8's extra test cases and the one-line `?#` fix (point 3) as a comment on #224 instead. That removes one issue, one PR, and the "names deduplicated twice" conflict (C9).
2. **Replace the linear chain of 8 by the real dependency graph.** Measured: #9, #2 and #16 depend on nothing in the chain, and neither does #8. Only #9 → #10 and #16 → #12 → #11 → #14 are real chains. Three PRs become independent of everything else: they can be reviewed and merged today, in any order, without the "merge commit only" rule. This needs no extra text and no larger PRs. It does need 3 interaction tests to move and the new tests to go into topic files (P1).
3. **Fix the cross-PR problems in the PR where they start**, so no later PR or CHANGELOG line has to explain them: the `?#` crash (1 line, verified), the deep-copy depth/`RecursionError` (16 lines, verified), quadratic naming (only if #8 is kept), traversal rules kept in two places, and the draft detected inside the resolver.
4. **Cut the prose, not the content.** Issues (92 KB) and PR bodies (54 KB) are 146 KB of text for 185 lines of library code. About 40% of it is duplicated or fork-internal: "Possible fix" in issues, "Changes after review", the stack preamble, and repro/cause restated in the PR (P4). Removing those sections makes every issue and PR shorter, and they can no longer go stale (C5).
5. **Don't merge code PRs.** Merging saves almost no code (measured: 266 → 224 changed lines for the whole stack). Merging #16 + #12 + #11 would remove the temporary regression window (C2), but the result would be a PR with ~400 test lines. A release note does the same job for free (P3).

Nothing has been filed upstream yet: no issue or PR by Frank-Reichenbach exists in horejsek/python-fastjsonschema (checked with `gh`). So the restructuring costs nothing outside the fork.

## 1. What the chain actually costs (measured)

| | Issues (8) | PR bodies (8) | Library code | Tests | CHANGELOG |
|---|---|---|---|---|---|
| Size | 92 KB, 1 491 lines | 54 KB | 185 +/39 − (cumulative); 266 changed lines if summed per commit | 1 088 + lines, 61 test functions | 14 lines |

- **Code churn across PRs is small:** 266 changed lines summed per commit vs 224 cumulative. Merging #12 + #11 would save 8 of 86 lines. Merging is not a size lever.
- **Text is the real weight.** Biggest sections overall:

  | Section | Size |
  |---|---|
  | Issues: "Actual result" | 26.4 KB, of which 21.8 KB is `<details>` "Further cases" scripts and outputs |
  | PR intros | 19.1 KB, of which 3.7 KB is stack preambles and the rest restates the issue's repro and cause |
  | Issues: "Cause" | 18.6 KB |
  | PRs: "Tests" | 13.2 KB |
  | Issues: "Possible fix" | 12.4 KB |
  | Issues: "Expected" | 12.2 KB |
  | PRs: "Decisions" | 7.6 KB |
  | PRs: "Changes after review" | 4.5 KB |
- **Tests repeat the same idioms:**

  | Idiom | Count |
  |---|---|
  | `parametrize('fast_fail', …)` | 31 |
  | `assert validator(…)` | 48 |
  | `pytest.raises(JsonSchemaException)` blocks | 44 |
  | inline `def handler(uri)` | 11, 9 of them recording `loaded.append(uri)` |
  | `handlers=` | 38 |

  All 8 PRs append to the end of `tests/test_integration.py`. On top of the real code dependencies, that alone forces any two PRs to conflict textually.

## 2. Real dependencies (measured, not inferred)

Method: master + only the listed commits' library-code diffs (fuzzy `patch`; where #2 is missing, `join_uri(` → `urlparse.urljoin(`), the test file of the target commit, and only the tests that commit adds. Scripts: `scripts/simplification/port.py`, `try.sh`.

| PR (issue) | Applied on master together with | Result of its own new tests | Real dependency |
|---|---|---|---|
| #8 (#3) | nothing | 18/18 pass | none |
| #9 (#6) | nothing | 18/18 pass | none |
| #2 (#1) | nothing | 23 pass, 4 fail: `test_ref_object_in_data_keyword_under_urn_id_is_data` (needs #9), `test_plain_name_ref_under_urn_id_next_to_similar_urn` (needs #8 or #224) | **code: none**, 2 interaction tests |
| #16 (#15) | nothing | 7/7 pass | none (one textual line: `join_uri` vs `urljoin` in `walk`) |
| #10 (#4) | #9 | 27 pass, 2 fail: `test_schema_array_shared_by_schemas_with_different_ids` (needs #16) | #9; 1 interaction test |
| #10 | #9, #16 | 29/29 pass | |
| #12 (#7) | #16 | 18/18 pass | #16 (not #2 and not #10, as its PR body claims) |
| #11 (#5) | #16, #12 | textual reject (`walk` loops come from #9) | #16, #12; #9 textual only |
| #11 | #9, #16, #12 | 20/20 pass | |
| #14 (#13) | everything except #8 | 61/61 pass | #9, #10, #16, #12, #11 (+#2 for 1 urn test param) |
| #14 | everything except #10 | 12 fail | #10 is real |
| #14 | everything except #2 | 2 fail (`…with_other_ids[urn:…]`) | interaction test only |
| whole stack minus #8, on upstream #224 | | **full suite 5139 passed, 0 failed**, incl. #8's tests | #8 replaceable by #224 |

Resulting graph:

```
master ─┬─ #9 ─── #10 ──────────────┐
        ├─ #2                       │
        ├─ #16 ── #12 ── #11 ───────┴── #14
        └─ (#8, or upstream #224)
```

## 3. Proposals

### P1 — Turn the chain into the graph (recommended; no size increase)

What to do:
1. **#8/#3:** see P2-a. If you keep #8, base it on master (it already is).
2. **#9, #2, #16:** rebase each onto master. Conflicts are one-liners: for #2/#16, `urljoin` vs `join_uri` in `walk`; for #2, the context of `subschemas()`.
3. **#10:** keep it on #9. Move `test_schema_array_shared_by_schemas_with_different_ids` into #16, where the same object under two `$id`s is the topic.
4. **#12:** base it on #16, not #10. Correct its body: it needs #16, not #2 (#12 F1 / C5).
5. **#11:** keep it on #12. After #9 is merged, rebase (textual only).
6. **#14:** keep it as a draft until #10 and #11 are in master, then base it on master. Its CI can only pass once both lines are in.
7. **Interaction tests:** the two #2 tests that need #8/#9, and the `urn:` parameter of #14's `…with_other_ids`, go to whichever of the PRs involved is merged **second**. Or rewrite them so they exercise only one fix (rename the colliding definition and drop the `enum` part).
8. **Tests in topic modules** instead of the end of `tests/test_integration.py`. Upstream #224 already uses `tests/test_ref_resolver.py`. Example layout: `tests/test_ref_names.py`, `test_ref_data_keywords.py`, `test_ref_urn.py`, `test_ref_schema_unchanged.py`, `test_ref_arrays.py`, `test_ref_relative_id.py`, `test_ref_handlers.py`, `test_ref_siblings.py`. Independent PRs then don't touch the same lines. Each PR's test diff is the same size as now.

What it removes:
- the "Nth of eight … merge with a merge commit" preamble in every PR (P4);
- the rule that squash/rebase merges break the chain, for all PRs that no longer have a child;
- the problem of untested intermediate states (C8): every PR is based on master or on a short real chain, so its own CI run checks exactly what gets merged.

What stays: CHANGELOG lines conflict trivially (everyone appends to `=== UNRELEASED`). Upstream resolves that with each merge, as for any two PRs.

### P2 — Solve the cross-PR problems at their origin (small, verified where marked)

| | Where | Change | Size | Status |
|---|---|---|---|---|
| a | #8 / #3 | **Use upstream #224** for #3. Post a comment on #224 with #3's further cases (they all pass with #224) and the `?#` one-liner below. Keep #8 locally as a fallback in case #224 stalls. Posting on someone else's PR is outward-facing: your call. | −1 issue, −1 PR | verified: #224 passes #8's 18 tests; the stack without #8 on #224 passes the full suite |
| b | #3 / CHANGELOG (C4) | In `RefResolver.resolving()`: `elif not normalize(uri) or normalize(uri) == normalize(self.base_uri):` instead of `elif not uri or uri == self.base_uri:`. Then `?#/definitions/ab` works in every schema shape, and the CHANGELOG/issue claim becomes true. Alternative: drop the `?#` example from #3 and the CHANGELOG (shorter). | 1 line | verified: both shapes OK on master + #8 + this line and on the tip; full suite green on both |
| c | #8 F1 (only if #8 is kept) | Keep a next-suffix counter per base name instead of searching from `_2_`. | ~3 lines | verified by the #8 reviewer (8000 colliding names: 6.6 s → 0.91 s) |
| d | #11 F1 + F7 | Replace `copy.deepcopy(...)` with a copy that respects the depth limit and turns any `Mapping` into a dict (`copy_document` below). Restores the clean "too deeply nested" error, and handlers returning `MappingProxyType` work again. #11's CHANGELOG then needs no caveat. | +16/−1 lines, `import copy` removed | verified on the tip: full suite 5123 passed; deep remote doc → `JsonSchemaDefinitionException`; `MappingProxyType` handler OK |
| e | #9 (C6, #10 F3) | Let `_expand_refs` use the resolver's keyword tables in #9, and `SCHEMA_ARRAYS` in #10, instead of its own copy of the rules. Then #10 only extends the table, and the comment "same rules as subschemas" is true. | ±0 lines (the rules exist anyway) | proposal, not run |
| f | #14 F3 | Have the generator class carry the draft rule (for example `ID_NEXT_TO_REF = True` on `CodeGeneratorDraft2019`, `False` on 04/06/07). `_factory`/`CodeGenerator` pass it to `RefResolver`. That removes `id_next_to_ref_applies()` (13 lines), the test import of it, and the list-`$schema` disagreement, and fixes the `template_test` debug output. | net smaller | proposal, not run |
| g | C3 (#12 vs #11) | Decide **once**, in #11's body plus one test, whether a handler-loaded `dir/main.json` with `$id: "dir/main.json"` resolves siblings under `dir/` (matches `jsonschema` and 2.22.3) or `dir/dir/` (RFC 3986, the tip's behaviour). Then mention it in the CHANGELOG as "Changed". | 1 test, 1 CHANGELOG line | decision needed from you |
| h | C1 | Write the "Changed" CHANGELOG lines in the PR that causes the change (#9 F2, #10 F1, #11 F4, #12 F3, #14 F1). Then no summary PR or later correction is needed. | +1 line per PR | — |
| i | C2 | One sentence in #16's body: "Release together with #11." That's cheaper than merging the PRs (P3). | 1 sentence | — |

`copy_document` as tested (goes into `ref_resolver.py`):

```python
def copy_document(node: Any, depth: int = 0) -> Any:
    """
    Copy the dicts and lists of a loaded document, up to the depth that walk() accepts.
    """
    if depth >= MAX_SCHEMA_WALK_DEPTH:
        raise JsonSchemaDefinitionException(
            'Schema is too deeply nested (maximum depth is {})'.format(MAX_SCHEMA_WALK_DEPTH)
        )
    if isinstance(node, Mapping):
        return {key: copy_document(value, depth + 1) for key, value in node.items()}
    if isinstance(node, list):
        return [copy_document(item, depth + 1) for item in node]
    return node
```

### P3 — Merges and splits I evaluated

| Option | Effect | Verdict |
|---|---|---|
| Merge #16 + #12 + #11 (issues #15, #7, #5: "each `$ref` resolved once, schema unchanged") | Removes C2 and C3 by construction, and the `rewrite_refs` / `_walked_uris` churn. Code 111 → ~100 changed lines; tests ~404 lines in one PR; text ~3 bodies → 1 | **No.** A larger PR for a gain that P2-g and P2-i get with one sentence and one test |
| Merge #9 + #10 (issues #6 + #4: "walk visits the wrong parts of a schema") | Same function, same tables, and C6 gets fixed once. PR: ~45 code lines, ~200 test lines; one issue instead of two (~24 KB → est. 14 KB with P4 applied) | **Optional.** Only if you'd rather have fewer PRs; P1 alone already makes the pair a short chain of 2 |
| Split #14 into "definitions next to `$ref`" + "2019-09 `$id` next to `$ref`" | With the draft rule off everywhere (draft-07 behaviour): only `test_id_next_to_ref_with_definitions` fails (4 params) and 2 suite XPASS are lost. But then, in the default draft (2019-09, which also covers schemas without `$schema`), a relative `$id` inside definitions next to a `$ref` that has its own `$id` is registered at the wrong URI. The PR body (Changes after review) documents that this replaced another schema. A conservative variant (skip such nodes in every draft) fails 14 tests, including draft-07 cases | **No.** Keep #14 whole, but make it simpler with P2-f |
| Drop the deep copy from #11 (smaller, no F1/F2/F7) | The 4 `objects_shared_by_handler_loaded_schemas` tests then fail. They pass on master/2.22.3 and fail on 2.22.2, so dropping the copy would bring back the bug 2.22.3 fixed | **No.** Use P2-d |
| Merge all issues into one tracking issue | Not shorter: each issue's repro and cause are distinct | **No.** But see P4: one short **meta issue** (≈10 lines) listing the PRs and the graph replaces 8 PR preambles |

### P4 — Shorter issues and PR bodies (same information)

Estimates from the measured section sizes; "→" is the proposed replacement.

| Where | Now | Proposal | Saves (est.) |
|---|---|---|---|
| Issues "Possible fix" | 12.4 KB; goes stale (issue #7, C5) | → "#N proposes a fix." | ~12 KB |
| Issues `<details>` "Further cases" | 21.8 KB of scripts and outputs that the PR tests repeat | → a 3–6-row table (case → actual / expected); the scripts live on as tests | ~15 KB |
| PR intros | 19.1 KB: 3.7 KB preamble + restated repro/cause | → "Fixes #N." + 2–3 sentences on *what changes*; dependencies in one line ("Depends on #16") only where real (P1), plus one meta issue for the order | ~14 KB |
| PRs "Changes after review" | 4.5 KB of fork-internal history | → delete (the review threads keep it) | ~4.5 KB |
| PRs "Tests" | 13.2 KB | → test names, each with "fails on master: yes/no"; the explanations go into one-line comments or names in the test modules | ~6 KB |
| Issues "Environment" + AI note | 2.7 KB, mostly the same text 8 times | → one line each | ~2 KB |
| Issue #3 + PR #8 | 12.7 + 5.7 KB | → replaced by a comment on upstream #224 (P2-a) | ~16 KB |

Total: 146 KB → **about 75–80 KB** (estimate), and every remaining issue and PR is shorter than now. "Expected behaviour and why" (spec citations) and "Cause" (line links) stay: that's the part a maintainer needs.

### P5 — Tests: smaller, without losing cases (optional)

- A helper `check(schema, valid=[...], invalid=[...], **compile_kwargs)` that runs both `fast_fail` modes replaces most of the 31 `fast_fail` parametrizations, 48 asserts and 44 `raises` blocks.
- `recording_handler(documents)` replaces the 11 inline handlers.
- Estimate: 150–250 of the 1088 test lines (not measured).
- Trade-off: a shared helper is a new common root. Put it in `tests/conftest.py` in a tiny first PR, or let the first merged PR bring it and the others rebase. Without P1's topic modules it's not worth it; with them it's a nice-to-have.

## 4. Proposed result

| New PR | Base | Fixes | Changes compared with today |
|---|---|---|---|
| — | — | #3 | Comment on upstream #224 instead (tests + `?#` line). #8 kept locally as a fallback |
| #9 | master | #6 | Rebased; `_expand_refs` uses the tables (P2-e); "Changed" line for remote fetches (#9 F2); tests in `test_ref_data_keywords.py` |
| #2 | master | #1 | Rebased; 2 interaction tests moved; clearer error message (#2 F1) optional |
| #16 | master | #15 | Rebased; gets the shared-array test from #10; "release together with #11" |
| #10 | #9 | #4 | Shared-array test moved out; "Changed" line for `id` in array items (#10 F1) |
| #12 | #16 | #7 | Base corrected; dependency statement fixed; `resolved` keyword-only (#12 F4); "Changed" line |
| #11 | #12 | #5 | `copy_document` (P2-d); relative-handler-`$id` decision + test (P2-g); "Changed" line |
| #14 | master (after #10 and #11) | #13 | Draft from the generator (P2-f); "Changed" line + docstring default draft |
| meta issue | — | — | ~10 lines: the graph above and the merge order constraints that remain |

That's 7 PRs instead of 8. Three of them can be merged immediately and independently, the longest remaining chain is 4 instead of 8, and the text shrinks by about half.

## 5. Order of work

1. Decide P2-a (#224) and P2-g (relative `$id` semantics). These are the only two decisions that are yours.
2. Restructure the branches (P1). Each step changes one branch, verified by CI on that branch. Use the **original parent commits** as the upstream argument, because branch names move as soon as you rebase the first one:
   - `git rebase --onto master 2ee7fbb fix/data-keyword-values` (#9: drop #8 below it)
   - `git rebase --onto master a467003 fix/urn-id-local-refs` (#2)
   - `git rebase --onto master 77b3985 fix/keep-schema-unchanged` (#16)
   - `git rebase --onto fix/data-keyword-values c4840e2 fix/walk-schema-arrays` (#10: onto the new #9, without #2/#16)
   - `git rebase --onto fix/keep-schema-unchanged 35ae4a3 fix/relative-id-resolved-once` (#12: onto the new #16)
   - `git rebase --onto fix/relative-id-resolved-once a1e7dc3 fix/handler-schema-nested-id` (#11). This needs `subschemas()` from #9 as context: until #9 is in master, base #11 on a merge of #9 and #12, or rebase it after #9 is merged.
   - #14 last, once #10 and #11 are in master.
   - Then retarget the PR bases with `gh pr edit <n> --base …`.
3. Apply the P2 fixes in their PRs (b, d, e, f, h, i).
4. Rewrite the issue and PR texts (P4), since the restructuring changes them anyway.
5. Dispatch CI for every branch (C8), then file upstream.

Not done: no branch, PR or issue was changed. Every experiment ran in a temporary worktree, which has been removed. The scripts are in `scripts/simplification/`.
