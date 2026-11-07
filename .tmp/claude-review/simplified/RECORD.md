# Record: old vs new resolver issues and PRs (fork Frank-Reichenbach/python-fastjsonschema)

Date: 2026-11-03. Implements `../simplification-proposal.md` with your two decisions:
1. Go with upstream horejsek/python-fastjsonschema#224 for the function-name collisions (no fork PR for it).
2. Handler-loaded schemas: their base URI stays the URI they were loaded from, and their root `$id` doesn't change it, as in 2.22.3 and `jsonschema`. Only `$id`s of subschemas apply.

Nothing old was closed, edited or commented on: old issues #1, #3–#7, #13, #15 and PRs #2, #8–#12, #14, #16 are still open. Close them when you're happy with the new set; the mapping is below.

## Which belongs to which

| Topic | Old issue | Old PR (branch) | New issue | New PR | New branch → base | Solution |
|---|---|---|---|---|---|---|
| Overview / merge order | – | (PR preambles) | **#24** | – | – | new |
| Function names per URI | #3 | #8 (`fix/unique-validation-function-names`) | – | – | – | **upstream #224**, see `comment-draft-upstream-224.md` |
| Data keywords (`const`, `enum`, `default`, `examples`) | #6 | #9 (`fix/data-keyword-values`) | **#17** | **#25** | `simple/data-keyword-values` → `master` | new |
| Schema left unchanged | #15 | #16 (`fix/keep-schema-unchanged`) | **#18** | **#26** | `simple/keep-schema-unchanged` → `master` | new |
| `urn:` `$id` local refs | #1 | #2 (`fix/urn-id-local-refs`) | **#19** | **#27** | `simple/urn-id-local-refs` → `simple/data-keyword-values` | new |
| Schema arrays (`allOf`…`items`) | #4 | #10 (`fix/walk-schema-arrays`) | **#20** | **#28** | `simple/walk-schema-arrays` → `simple/base-for-walk-schema-arrays` | new |
| Relative `$id` with directory | #7 | #12 (`fix/relative-id-resolved-once`) | **#21** | **#29** | `simple/relative-id-resolved-once` → `simple/keep-schema-unchanged` | new |
| Handler-loaded schemas (2.22.3 regression) | #5 | #11 (`fix/handler-schema-nested-id`) | **#22** | **#30** | `simple/handler-schema-nested-id` → `simple/relative-id-resolved-once` | new |
| Definitions next to `$ref` | #13 | #14 (`fix/ref-sibling-definitions`) | **#23** | **#31** | `simple/ref-sibling-definitions` → `simple/integration-base` | new |

Branches without a PR, which exist only so that a PR with two parents shows only its own diff:
- `simple/base-for-walk-schema-arrays` = merge of #25 and #26;
- `simple/integration-base` = merge of #27, #28 and #30 (and so of all their bases).

GitHub links "Fixes #N" to an issue only for PRs that target the default branch. So only #25 → #17 and #26 → #18 show the link now; the others get it once they're retargeted to `master`.

## Dependencies (measured, not assumed)

```
master ─┬─ #25 data keywords ──┬─ #27 urn: ids  (and: merge after upstream #224)
        │                      └──┐
        └─ #26 schema unchanged ──┴─ #28 schema arrays
                 └─ #29 relative ids ── #30 loaded schemas
#31 definitions next to $ref: needs all of the above
```

- #25 and #26 can be merged now, in any order. Release #26 together with #30.
- **Correction to the proposal:** the proposal called #2 (now #27) and #16 (now #26) independent of everything, and #10 (now #28) dependent on #9 only. That held for the code, but not for behaviour. Guard tests show that merging them alone would bring temporary regressions:
  - #27 without #25: a `{"$ref": "#"}` inside `const`/`default` under a `urn:` `$id` gets rewritten, so equal data is rejected (`test_ref_object_in_data_keyword_under_urn_id_is_data` passes on master and fails on #27 without #25).
  - #27 without upstream #224: `#foo` under `urn:example:root` and `urn:example:root:foo` get the same function name. On master this case validates correctly; on #27 alone `{'a': 1, 'b': 'x'}` is rejected. With #224 applied it works again. #27's second commit adds the test as `xfail(strict=True)`, so it fails, and the mark has to go, once #224 is in.
  - #28 without #26: an array shared by two schemas with different `$id`s keeps the first base URI (`test_schema_array_shared_by_schemas_with_different_ids` passes on master and fails on #28 without #26).

  The old PR #2 body already listed "Needs #9" and "Needs #8"; the new structure keeps those dependencies instead of hiding them.

## What changed compared with the old PRs

| New PR | Changes besides restructuring | Old review finding |
|---|---|---|
| #25 | CHANGELOG: an `$id` in a data value / custom-map entry is no longer registered and is loaded through handlers | #9 F2 |
| #25 | PR body: mentions a `$ref` pointer into a data value | #9 F1 |
| #26 | Body: "release together with #30"; commit message corrected for relative bases | C2, #16 F2 |
| #27 | `test_join_uri` (unit test) replaces the test that inspected the rewritten schema, which would break once #26 is in | #2 F2 + hidden conflict with #26 |
| #27 | Naming test as strict xfail | dependency on #224 |
| #28 | `_expand_refs()` uses `SCHEMA_ARRAYS`, like `subschemas()` (no `$ref` resolution or handler call for arrays of unknown keywords) | C6, #9 F3, #10 F3 |
| #28 | Test for the error `definition` | #10 F4 |
| #28 | CHANGELOG "Changed" lines for `id` in arrays and for `definition` | #10 F1, C1 |
| #29 | `resolved=` keyword-only | #12 F4 |
| #29 | Base corrected to #26 (it never needed #2) | #12 F1, C5 |
| #29 | CHANGELOG mentions the hang and the doubled registration | #12 F3 |
| #30 | **Root `$id` of a loaded schema keeps the retrieval URI as base** (your decision 2). Verified against `jsonschema` 4.26 in 7 cases, all equal | C3, #11 F4 |
| #30 | `copy_document()` replaces `copy.deepcopy`: depth limit → `JsonSchemaDefinitionException` instead of `RecursionError`; any mapping works | #11 F1, F7 |
| #30 | `_expand_refs()` leaves an invalid-URI `$ref` as written. The old CHANGELOG claim only held for schemas without a keyword such as `type` | #11 F6 (+ test) |
| #30 | Test comment "rewrites" fixed | #11 F8 |
| #31 | `ID_NEXT_TO_REF` on the generator classes, passed to `RefResolver(id_next_to_ref=…)` by `compile()`, the generator and the test harness. Deviation from the proposal: `id_next_to_ref_applies()` stays, as the default for direct `RefResolver` users, so the public API keeps its behaviour | #14 F3 |
| #31 | `compile()` docstring: default draft is 2019-09 | #14 F1 |
| #31 | CHANGELOG "Changed" for 2019-09; depth wording | #14 F1, F7 |
| #31 | Misleading comment fixed; tests in their own module | #14 F4, F5 |
| all | Tests in topic modules `tests/test_ref_*.py` instead of appending to `test_integration.py` | P1.8 |
| all | Shorter issues (P4 of the proposal) | C5 |
| all | Shorter PR bodies: no preamble, no "Changes after review", per-test "fails on parent" | P4 |

Not done, on purpose or left for later:
- #2 F1 (error message naming the ref);
- #11 F2 (`cache=False` re-walk cost) and F3 (direct `RefResolver` with a shared store);
- #8 F1 (it's #224's code now);
- C7 (XPASS instead of removed xfails for 2019-09 `ref.json`/`refRemote.json`);
- P5 (test helpers);
- the `?#` one-liner, which is in the #224 comment draft.

**Attribution:** the old commits and PR bodies had `Assisted-by:` lines. The new commits and PR bodies don't, because of an instruction in this session. Add them if upstream wants them. The new issues keep the line "Found and analyzed with AI assistance (Claude Code and Codex)."

## Verification

- **Each branch, Python 3.14 locally:** full suite green, and pylint gives exactly the same 9 messages as `master`.

  | Branch | Passed | xfailed | xpassed |
  |---|---|---|---|
  | `master` | 4758 | 415 | 970 |
  | #25 | 4796 | 411 | 954 |
  | #26 | 4764 | 415 | 970 |
  | #27 | 4827 (+2 strict xfail) | 411 | 954 |
  | base-for-arrays | 4802 | 411 | 954 |
  | #28 | 4981 | 393 | 824 |
  | #29 | 4782 | 415 | 970 |
  | #30 | 4806 | 415 | 970 |
  | integration | 5054 (+2 strict xfail) | 393 | 824 |
  | #31 | 5117 (+2 strict xfail) | 382 | 835 |

  The official-suite outcomes at the tip (382 xfailed, 835 xpassed) are identical to the old stack tip.
- **New tests against the parent of each PR:** every PR's new tests fail there, except guard tests that pass by design. Details are in each PR body; the script is `scripts/simplification-impl/parentdetail.py`.
- **Generated code:** `compile_to_code()` for all 1204 official-suite schemas, old tip (2375eb3) vs new tip. 1202 are identical. The 2 that differ are 2019-09 `refRemote.json` "remote HTTP ref with different $id" and "… URN $id". There the new code equals `master`'s (your decision 2), and the suite cases pass in both.
- **Library code:** old #11 vs the new integration branch differs only in the intended items (no #8 code, `copy_document`, the root-`$id` rule, keyword-only `resolved`, `_expand_refs` rules).
- **Handler rule vs `jsonschema`:** `scripts/simplification-impl/handler_ids.py`, 7 cases, all equal. It also showed that 2.22.2's in-place rewrite distorts comparisons unless each library gets its own copy.
- **CI on GitHub:** started with `workflow_dispatch` for every PR branch and the integration branch (see the table below). Pushes and PRs don't trigger CI on this fork.

## Sizes, old → new

| | Old | New |
|---|---|---|
| Issues | 8 issues, 91.9 KB | 7 issues + meta, 45.5 KB |
| PR bodies | 8, 53.2 KB | 7, 16.7 KB |
| Library code (vs master) | 185+/39− (incl. #8's 24 lines) | 214+/44− (no #8, plus the review fixes above: `copy_document`, `ID_NEXT_TO_REF`, `_expand_refs` rules, root-`$id` rule) |
| Tests | 1088+ in `test_integration.py` | 1124+ in 7 modules (+join_uri, definition, ValueError, root-`$id`, draft-flag tests) |
| Longest chain | 8 | 4 (#26 → #29 → #30 → #31) |
| Mergeable right away | 1 (#8) | 2 (#25, #26) |

Per PR (code / tests):

| PR | Code | Tests |
|---|---|---|
| #25 | 35+/8− | 85+ |
| #26 | 19+/6− | 67+ |
| #27 | 23+/4− | 154+ |
| #28 | 14+/8− | 155+ |
| #29 | 30+/13− | 136+ |
| #30 | 58+/20− | 230+ |
| #31 | 60+/9− | 297+ |

## Files

- `issues/issue-from-<old>.md` and `issues/meta.md`: bodies as filed (with `TITLE:`; the meta one has placeholders).
- `pr-bodies/*.md`: PR bodies with placeholders; `created.json` holds the numbers.
- `comment-draft-upstream-224.md`: the comment for #224, not posted.
- Fixed on 2026-11-04 in #24, #27 and #30 (and in the local copies): references to upstream #218/#219/#224 written as bare `#N` or `horejsek#N` now use `horejsek/python-fastjsonschema#N`. Bare, they would have pointed at the fork, which has no such numbers.
- `../scripts/simplification-impl/`: the scripts used.

## CI results

Workflow `tests` started with `workflow_dispatch` on 2026-11-03: Python 3.10–3.14 on ubuntu, windows and macos (15 jobs per branch).

| Branch | PR | Head | Run | ubuntu | windows | macos |
|---|---|---|---|---|---|---|
| `simple/data-keyword-values` | #25 | `0d756d6` | 41648870463 | 5/5 ✓ | 5/5 ✓ | 5/5 ✓ |
| `simple/keep-schema-unchanged` | #26 | `fa8aa14` | 41648874937 | 5/5 ✓ | 5/5 ✓ | 5 cancelled |
| `simple/urn-id-local-refs` | #27 | `02c8082` | 41649221110 | 5/5 ✓ | 5/5 ✓ | 1 ✓, 4 cancelled |
| `simple/walk-schema-arrays` | #28 | `5542b60` | 41648883822 | 5/5 ✓ | 5/5 ✓ | 5 cancelled |
| `simple/relative-id-resolved-once` | #29 | `4c88f1d` | 41648888128 | 5/5 ✓ | 5/5 ✓ | 1 ✓, 4 cancelled |
| `simple/handler-schema-nested-id` | #30 | `768b7f5` | 41648891900 | 5/5 ✓ | 5/5 ✓ | 5 cancelled |
| `simple/integration-base` | – | `e3a3457` | 41649226480 | 5/5 ✓ | 5/5 ✓ | 1 ✓, 4 cancelled |
| `simple/ref-sibling-definitions` | #31 | `f12ef88` | 41649231249 | 5/5 ✓ | 5/5 ✓ | 5 cancelled → re-run, see below |

- **No job failed.** All 32 non-green jobs are macOS jobs that GitHub cancelled before their first step: "The job was not acquired by Runner of type hosted even after multiple attempts". GitHub showed "Due to capacity constraints, jobs targeting macOS arm64 runners may experience longer queue times." So these are runner-capacity cancellations, not test results. The run status shows "failure" only because of them.
- macOS is covered anyway: the local verification above ran on macOS (CPython 3.14) for every branch.
- The cancelled macOS jobs were re-run only for the tip #31, because it contains all the code (`gh run rerun 41649231249 --failed`). Result of the re-run: none. GitHub accepted it at 08:23 UTC on 2026-11-04 but never created the jobs. It was stopped on 2026-11-04. Cancel and force-cancel are both refused ("Cannot cancel a workflow re-run that has not yet queued"), so the run still shows as queued, but no job of it exists or runs.
- **What CI runs:** `tests.yml` and `tox.ini` are identical to upstream's, and no branch changes them. CI runs `pipx run tox -e py` (pytest, `-m "not benchmark"`), not the `lint` env. `actions/checkout` doesn't fetch the `JSON-Schema-Test-Suite` submodule, so the official-suite tests collect nothing, upstream as well (upstream master on 3.14: 866 collected, 850 passed). Fork CI on 3.14: #25 884 collected, integration branch 996. The official suite and pylint were run only locally (see Verification).
