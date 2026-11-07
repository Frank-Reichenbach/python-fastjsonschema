# Review: resolver-fix issues and PRs on Frank-Reichenbach/python-fastjsonschema

Date: 2026-11-03 · Reviewer: Claude Code (Opus 5.5), one reviewer per issue/PR pair plus a review across the stack
Scope: all 8 open issues and all 8 open PRs of the fork, checked against the 20-item checklist (Correctness … Regression).

## Files

| File | Content |
|---|---|
| `README.md` (this file) | Overall verdict, cross-PR findings, all findings ranked, checklist matrix, verification log |
| `simplification-proposal.md` | How to simplify the issue/PR chain (measured dependency graph, using upstream #224, fixes at the origin, text cuts) |
| `pr-8-issue-3.md` | #8 "Use one validation function name per URI" / #3 |
| `pr-9-issue-6.md` | #9 "Treat the values of const, enum, default and examples as data" / #6 |
| `pr-2-issue-1.md` | #2 "Resolve local refs inside a subschema with a urn: $id" / #1 |
| `pr-16-issue-15.md` | #16 "Leave the $ref values of the schema unchanged" / #15 |
| `pr-10-issue-4.md` | #10 "Resolve refs inside allOf, anyOf, oneOf and items arrays against their $id" / #4 |
| `pr-12-issue-7.md` | #12 "Resolve each URI once under a relative $id with a directory" / #7 |
| `pr-11-issue-5.md` | #11 "Walk schemas loaded through handlers like the main schema" / #5 |
| `pr-14-issue-13.md` | #14 "Register $id and resolve refs in definitions next to a $ref" / #13 |
| `scripts/` | Repro scripts and their outputs. The reports cite them under the session scratchpad path `/private/tmp/claude-501/.../scratchpad/pr-<N>/`; those are the same files as `scripts/pr-<N>/`, which keeps them after the scratchpad is cleaned up |

Each per-PR file has: Verdict · Issue review · Findings (severity, checklist area, file:line, repro + output, suggested fix) · Checklist table · Verification log.

## Stack

Each PR branch is its parent plus exactly one commit (verified). Base: `master` = `4999d6b` (= upstream/master).

| Order | PR | Issue | Branch | Head |
|---|---|---|---|---|
| 1 | #8 | #3 | fix/unique-validation-function-names → master | 2ee7fbb |
| 2 | #9 | #6 | fix/data-keyword-values | a467003 |
| 3 | #2 | #1 | fix/urn-id-local-refs | 77b3985 |
| 4 | #16 | #15 | fix/keep-schema-unchanged | c4840e2 |
| 5 | #10 | #4 | fix/walk-schema-arrays | 35ae4a3 |
| 6 | #12 | #7 | fix/relative-id-resolved-once | a1e7dc3 |
| 7 | #11 | #5 | fix/handler-schema-nested-id | 5fd4ad5 |
| 8 | #14 | #13 | fix/ref-sibling-definitions | 2375eb3 |

## Overall verdict

**All 8 PRs: approve with nits. No blockers, no majors.** Every issue report was reproduced on `master` (and on the PR's parent) as written. Every PR fixes its issue, and its new tests fail on the parent and pass on the branch. Generated code stays byte-identical outside the intended cases (spot checks across 800–2400 official-suite schemas per PR). Suite outcomes don't regress, and pylint shows no new messages.

What should be done before merging (all small):

1. **#11 F1:** cap the depth before or while deep-copying handler results. A deeply nested remote document now raises a bare `RecursionError` instead of `JsonSchemaDefinitionException` (verified by me, see below).
2. **#8 F1:** keep a next-suffix counter per base name. Naming is quadratic when many URIs share one base name (verified by me: 4000 colliding names take 1.42 s on the tip vs 0.10 s on master; master is fast there because it generates wrong code).
3. **CHANGELOG across the stack (cross-cutting C1):** several "Fixed" lines hide behaviour changes users can notice. Add "Changed" lines for #9 F2, #10 F1, #11 F4, #12 F3 and #14 F1.
4. **PR bodies and issues (C5):** correct #12's "only needs #2" (it also needs #16), and update the stale "Possible fix"/"Limitation" sections of issue #7.

The remaining findings are minor or nits that can go into follow-ups.

## Cross-PR findings (not visible when looking at a single PR)

**C1 — minor — Documentation/Compatibility.** The CHANGELOG labels several behaviour changes as "Fixed". Users upgrading from 2.22.3 will see:
- #9: some `$id`s that resolved locally now trigger a remote fetch (`urlopen` with the default handlers): an `$id` inside `const`, entries named like data keywords in custom maps such as `x-defs`, and draft-07 schemas placed directly under `$defs`.
- #10: in draft-06+, an `id` annotation inside an `allOf`/`anyOf`/`oneOf`/`items` item now changes the base URI. Verified by me: `{"$schema": draft-07, "definitions": {"n": …}, "allOf": [{"id": "other/", "properties": {"a": {"$ref": "#/definitions/n"}}}]}` compiles and validates on master, and on the tip raises `Unresolvable ref: definitions`.
- #11: a handler-loaded `dir/main.json` with `"$id": "dir/main.json"` now resolves siblings under `dir/dir/` (follows RFC 3986, unlike 2.22.3 and `jsonschema`).
- #14: schemas without `$schema` (Draft2019 generator) now honour an `$id` next to a `$ref`, while the `compile()` docstring still says draft-07 is the default.

Suggestion: one "Changed" block listing these, plus a docstring fix for the default draft.

**C2 — minor — Integration (merge timing).** #16 removes the in-place `$ref` rewrite that accidentally hid #5 for handler-served objects that were compiled earlier. Between #16 and #11, such a schema accepts invalid data silently, where it used to be rejected (#16 F1). Merge or release #16 … #11 together and never ship #16 without #11.

**C3 — minor — Consistency.** #12 and #11 disagree on relative `$id`s in handler-loaded documents (`a/b/other.json` with its own `$id: "a/b/other.json"` and `$ref: "third.json"`): after #12 it loads `a/b/third.json` (matches `jsonschema`), after #11 `a/b/a/b/third.json` (RFC 3986). The tip has #11's behaviour. Decide which one is intended, document it, and pin it with a test.

**C4 — minor — Completeness (pre-existing, but advertised as fixed).** #8's CHANGELOG uses `?#/definitions/ab` as its example, but on the tip that ref still crashes `compile()` with `ValueError: unknown url type: '?'` as soon as an enclosing schema has a keyword such as `type` (`_expand_refs` resolves the raw `$ref`). Verified by me on master and tip:
```
{'definitions': {...}, 'properties': {'x': {'$ref': '?#/definitions/ab'}, ...}}             master: NameError   tip: OK
{'type': 'object', 'definitions': {...}, 'properties': {'x': {'$ref': '?#/definitions/ab'}}}  master: ValueError  tip: ValueError
```
Fix it in #8 or a follow-up, or change the CHANGELOG example.

**C5 — nit — Documentation.** In #12's body, "only needs #2" is wrong (it uses `get_ref`/`_resolved_refs` from #16). Issue #7's "Possible fix"/"Limitation" sections describe the design from before #16, and its outputs are labelled 2.22.2.

**C6 — nit — Maintainability.** The traversal rules now live in two places: `ref_resolver.subschemas()` and `generator._expand_refs()`. #9 copies the rules by hand. After #10 the `_expand_refs` comment claims "same rules as subschemas" but it still recurses into every list, and it can call a handler for a `$ref` inside an unknown-keyword array. A follow-up should make `_expand_refs` use `subschemas()`.

**C7 — nit — Testability/Regression guard.** Newly passing official-suite cases are often only XPASS, because whole files (`ref.json`, `refRemote.json`) are xfailed: 11 new XPASS in 2019-09 with #14, and 835 XPASS overall on the tip vs 970 on master. CLAUDE.md asks to remove fixed cases from the xfail lists. Moving these files to `ignore_tests` with the remaining failing descriptions would turn the fixes into real regression guards. The xfail removals the PRs did make (#9: 4 cases, #10: 18 cases) match the newly passing cases exactly; no case was left behind.

**C8 — nit — Reliability (process).** CI has run once, via `workflow_dispatch` on 72ab6ba (15/15 jobs green, Python 3.10–3.14 × Linux/macOS/Windows). Its tree is byte-identical to the current tip 2375eb3; only commit messages changed. No intermediate branch has CI results; I ran all of them locally on Python 3.14 only. Since each merge commit lands an intermediate state on master, consider dispatching CI for each branch, especially #2 and #12, whose reviewers could not test `urllib.parse` on real Python 3.10–3.13.

**C9 — info — Compatibility (upstream).** Upstream horejsek/python-fastjsonschema#224 (open) fixes #3 differently, inside `get_scope_name()`. If both land, names are deduplicated twice; still unique, but one mechanism should be removed. #8's body already says this.

Checked and fine: the stack is linear with no extra commits. Each commit has a CHANGELOG line in `=== UNRELEASED` and consistent `Assisted-by:` trailers. The test removed in #16 (`…_rewritten_by_urljoin`) was renamed to `…_resolved_by_urljoin` and adapted, not dropped. No new pylint messages anywhere. The security rule (schema values are never interpolated raw into generated code) is not touched by any PR.

## All findings, by severity

Format: PR · finding no. in the per-PR file · checklist areas · summary. ✔ = I re-ran it myself on the tip.

### Minor
| PR | F | Areas | Summary |
|---|---|---|---|
| #11 | 1 ✔ | Robustness, Security | `deepcopy` of handler results runs before the depth guard → bare `RecursionError` for deep remote documents (master: clean `JsonSchemaDefinitionException`) |
| #8 | 1 ✔ | Performance | Suffix search is quadratic when many URIs share one base name (8000 → 6.6 s vs 0.9 s); a per-base counter fixes it |
| #11 | 2 | Performance | `cache=False`: every `resolving()` deep-copies and re-walks the remote document (200 refs × 2000 defs: 0.019 s → 1.75 s) |
| #11 | 3 | Correctness | Store entries the resolver didn't load are walked uncopied; a shared/default `store={}` applies a relative nested `$id` twice (direct `RefResolver` use only; `compile()` not affected) |
| #11 | 4 | Compatibility, Docs | Relative root `$id` equal to the fetch path now resolves under `dir/dir/` (see C1/C3) |
| #11 | 6 | Test coverage | The `ValueError`-in-unknown-keyword CHANGELOG line has no test for the case it describes |
| #8 | 2 | Completeness, Docs | `?#/…` CHANGELOG example still crashes in most schema shapes (C4) |
| #9 | 1 | Correctness | A `$ref` pointing into a data value: relative `$ref`s inside it now resolve against the document base, not the enclosing `$id` (outside the spec; mention in the PR body) |
| #9 | 2 | Compatibility, Docs, Security-adjacent | Some formerly local `$id`s now trigger a remote fetch; not in the CHANGELOG (C1) |
| #2 | 1 | Usability, Observability | New compile error `Unresolvable ref: definitions` names neither the ref nor the base URI, and is misleading because the root does have `definitions` |
| #16 | 1 | Integration, Regression | Between #16 and #11, #5 surfaces silently for handler-served objects that were compiled earlier (C2) |
| #10 | 1 ✔ | Compatibility, Regression, Docs | draft-06+ `id` annotation inside array items now changes the base URI; not in the CHANGELOG (C1) |
| #14 | 1 | Compatibility, Docs | No-`$schema` schemas change behaviour (2019-09 `$id` next to `$ref`), and the docstring still says draft-07 (C1) |
| #14 | 2 | Robustness | An invalid-URI `$id` that is now walked raises a raw `ValueError` (pre-existing root cause, scope widened) |
| #14 | 3 | Architecture, Testability | The resolver detects the draft on its own instead of getting it from the generator; `template_test` prints 2019-09 debug code for draft-04..07 cases; a list-valued `$schema` makes the two disagree |

### Nit
| PR | F | Summary |
|---|---|---|
| #8 | 3 | No test pins the trailing-`_` suffix or the root name `validate` in `compile_to_code()` |
| #8 | 4 | `compile()` finds the root by recomputing `get_scope_name()`, which works only because the root is named first |
| #8 | 5 | (opinion) Suffixes depend on generation order; `_a_2_` next to `_a_2` is easy to confuse |
| #9 | 3 | Traversal rules duplicated in `_expand_refs` and `subschemas()` (C6) |
| #2 | 2 | No direct unit test for `join_uri`, for nested `urn:` subschemas, or for `#` in a plain-name subschema |
| #2 | 3 | Follow-up: relative non-`#` refs under `s3://`-like schemes still raise a raw `ValueError` (unchanged; `jsonschema` fails too) |
| #16 | 2 | "Code otherwise unchanged / first base wins as it did" is not exact for relative bases (parent crashed there) |
| #16 | 3 | No test for the visible `JsonSchemaValueException.definition` change or for the issue's nested-relative-`$id` compiled-twice case |
| #10 | 2 | The same array object under two `$id`s resolves against the first (first-wins rule from #16; better than before) |
| #10 | 3 | `_expand_refs` comment claims the same rules as `subschemas()` but recurses into every list (C6) |
| #10 | 4 | The improved error `definition` for refs in arrays has no test |
| #12 | 1 | PR body: "only needs #2"; it also needs #16 (C5) |
| #12 | 2 | Issue #7's "Possible fix"/"Limitation" sections are stale (C5) |
| #12 | 3 | CHANGELOG omits the former hang (self-referencing subschema) and that a nested relative `$id` is no longer registered under the doubled URI |
| #12 | 4 | New positional `resolved=` argument breaks old `resolving`/`in_scope` overrides; make it keyword-only like `id_applied` |
| #11 | 5 | CHANGELOG line is too narrow (an absolute root `$id` that differs from the fetch URI is fixed too); untested |
| #11 | 7 | Handlers returning `MappingProxyType` now fail (`cannot pickle`) |
| #11 | 8 | Test comment at `tests/test_integration.py:884` still says "rewrites" |
| #14 | 4 | Comment says `id` is unknown in 2019-09; the branch below it honours `id` |
| #14 | 5 | Test file style: 3 blank lines, trailing blank line at EOF, import order |
| #14 | 6 | Fixed suite cases only XPASS (C7) |
| #14 | 7 | "nesting limit of 500 levels" = 500 depth units = 249 nested `definitions` |

Pre-existing bugs the reviewers found that no PR causes (candidates for new issues): a `$ref` into a string `const` value raises `TypeError` (#9 report); a root `$id` ending in an empty `#` combined with a root-level `$ref` raises `URLError` (#2 report); a root `$id` with a non-empty fragment breaks local refs (#12 report); `$id` with dot segments plus a `$ref` to its own file name fails (#12 report; `jsonschema` fails too).

## Checklist matrix

OK = no finding · Fn = finding n in that PR's file · N/A = not applicable · Cn = cross-PR finding above

| # | Area | #8 | #9 | #2 | #16 | #10 | #12 | #11 | #14 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Correctness | OK | OK (F1) | OK | OK | OK | OK | OK / F3 | OK |
| 2 | Completeness | F2 | OK | F3 | OK | OK | OK | OK | OK |
| 3 | Consistency | OK | F3 | OK | F2 | F3 | F4 | OK | F4 · C3 |
| 4 | Robustness | F1 | OK | OK | OK | OK | OK | F1, F7 | F2 |
| 5 | Reliability | OK | OK | OK | OK | OK | OK | OK | OK · C8 |
| 6 | Security | OK | F2 | OK | OK | OK | OK | F1 | OK |
| 7 | Performance | F1 | OK | OK | OK | OK | OK | F2 | OK |
| 8 | Maintainability | F4 | F3 | OK | OK | OK | OK | OK | F3, F5 · C6 |
| 9 | Readability | OK | OK | OK | OK | OK | OK | F8 | F4 |
| 10 | Testability | OK | OK | F2 | OK | OK | OK | OK | F3 |
| 11 | Test coverage | F3 | OK | F2 | F3 | F4 | OK | F5, F6 | F6 · C7 |
| 12 | Compatibility | F5 · C9 | F1, F2 | F1 | F1 | F1 | F4 | F4, F7 | F1 · C1 |
| 13 | Architecture | OK | OK | OK | OK | OK | OK | OK | F3 |
| 14 | Integration | OK | OK | OK | OK · C2 | OK | F1 | OK / F3 | OK |
| 15 | Data integrity | OK | OK | OK | OK (F1) | OK | OK | OK | OK |
| 16 | Usability | F5 | OK | F1 | OK | OK | OK | OK | F1 |
| 17 | Accessibility | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 18 | Observability | N/A | N/A | F1 | N/A | N/A | N/A | N/A | N/A |
| 19 | Documentation | F2 · C4 | F2 | OK | F2 | F1 | F1–F3 · C5 | F4–F6 | F1, F7 · C1 |
| 20 | Regression | OK | OK | OK | F1 · C2 | F1 | OK | F1 | OK |

Accessibility doesn't apply to a library without a UI. The nearest equivalent, clear error messages, is covered under Usability/Observability (#2 F1, #11 F1).

## Verification log (lead)

- Data: `gh issue view` / `gh pr view` / `gh pr diff` for #1, #3–#7, #13, #15 and #2, #8–#12, #14, #16. One detached worktree per branch plus master; the `JSON-Schema-Test-Suite` submodule is symlinked in. Venv: Python 3.14.10, pytest 9.2, `jsonschema` as an oracle.
- Full suite per branch (`pytest -W default --benchmark-skip`), all green:

  | Branch | passed | xfailed | xpassed |
  |---|---|---|---|
  | master | 4758 | 415 | 970 |
  | #8 | 4776 | 415 | 970 |
  | #9 | 4814 | 411 | 954 |
  | #2 | 4841 | 411 | 954 |
  | #16 | 4847 | 411 | 954 |
  | #10 | 5024 | 393 | 824 |
  | #12 | 5042 | 393 | 824 |
  | #11 | 5062 | 393 | 824 |
  | #14 | 5123 | 382 | 835 |
- Per-test outcome diff between consecutive branches (`scripts/lead-suite-outcomes.py`). No test went from passed to failed or xfailed anywhere. #9: 16 XPASS→pass, 4 XFAIL→pass. #10: 130 XPASS→pass, 18 XFAIL→pass. #14: 11 XFAIL→XPASS (2019-09 `ref.json`, `refRemote.json`, `unevaluated*`). #16: one test renamed (not removed).
- pylint per branch: the same 3 pre-existing messages as master (generator `comparison-with-itself`, draft04 `dangerous-default-value`, `too-many-return-statements`), 9.90–9.91/10.
- CI: one `workflow_dispatch` run on 72ab6ba, all 15 jobs green. `git diff 72ab6ba 2375eb3` is empty.
- Re-checked reviewer findings myself on the tip (`scripts/lead-verify.py`, `scripts/lead-empty-query-ref.py`): #11 F1 (`RecursionError` vs master's clean error), #8 F1 (1.42 s vs 0.10 s for 4000 colliding names; 0.11 s for distinct names), #10 F1 (`Unresolvable ref: definitions` vs master OK), C4 (`ValueError: unknown url type: '?'` on master and tip).
- Not done: no GitHub comments or edits, no pushes. Benchmarks (`make benchmark`) not run; reviewers did quick timings only. Python 3.10–3.13 not run locally (covered for the tip tree by the CI run).
