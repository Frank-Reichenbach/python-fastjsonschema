# Merge order for the fork PRs (updated 2026-11-03)

The eight PRs form a linear chain: each one targets the branch of the one before it, so each diff shows only its own commit and no PR conflicts with the ones before it. Fork `master` equals upstream `master` (`4999d6b`, 2.22.3, checked 2026-11-03). Review state and verification: `review/README.md`.

| Step | PR | Fixes | Branch | Head | Base | Needs |
|---|---|---|---|---|---|---|
| 1 | #8 | #3 | `fix/unique-validation-function-names` | `2ee7fbb` | `master` | – |
| 2 | #9 | #6 | `fix/data-keyword-values` | `a467003` | #8's branch | – |
| 3 | #2 | #1 | `fix/urn-id-local-refs` | `77b3985` | #9's branch | #8, #9 |
| 4 | #16 | #15 | `fix/keep-schema-unchanged` | `c4840e2` | #2's branch | #2 (`join_uri`) |
| 5 | #10 | #4 | `fix/walk-schema-arrays` | `35ae4a3` | #16's branch | #9, #16 |
| 6 | #12 | #7 | `fix/relative-id-resolved-once` | `a1e7dc3` | #10's branch | #2 (same calls), #16 |
| 7 | #11 | #5 | `fix/handler-schema-nested-id` | `5fd4ad5` | #12's branch | #16, #12, #9 |
| 8 | #14 | #13 | `fix/ref-sibling-definitions` | `2375eb3` | #11's branch | #11, #10, #9 |

The fork allows only merge commits (squash and rebase merging are off) and deletes a head branch after its merge (checked 2026-11-03). Upstream merges every PR with a merge commit.

## Between merges on GitHub

- Merge with "Create a merge commit". Each merged head stays an ancestor of `master`, so the next PR merges without conflicts and its diff keeps only its own commit. The branch commits reach `master` unchanged, with their messages and trailers; the PR descriptions don't.
- With automatic deletion on, GitHub normally deletes the merged branch and then retargets the next PR to `master` (the fork has no rulesets or branch protection that could prevent it). Check the next PR's base and diff before merging it; if the base is still the merged branch, retarget it to `master` by hand and check the diff again.
- If squash or rebase merging is ever used anyway: the merged commit isn't an ancestor of the next branch. Rebase the next branch onto the updated `master` without the merged commit (`git rebase --onto master <merged head> <branch>`) and force-push it with a lease, one PR at a time.
- If upstream `master` moves: first sync the fork's `master` with it. Then rebase only the PRs still open, in merge order: the first one onto `master`, each later one onto the rebased branch before it (`git rebase --onto <new base> <old base head> <branch>`), resolving conflicts where needed. `CHANGELOG.txt` conflicts are the usual ones: the PRs' lines belong in `=== UNRELEASED`. Force-push each branch with a lease and check every open PR's base and diff.
- Don't use `git rebase --update-refs` while other local branches point at commits of the chain: it moves them too.

## Checks on the chain (2026-11-03)

- Every commit: full suite incl. the JSON-Schema-Test-Suite, and pylint. No outcome gets worse at any step; pylint shows only `master`'s messages. Head: 5123 passed, 382 expected failures (`master`: 4758 and 415). Per-commit numbers: `review/README.md`.
- Published PR heads equal the local `fix/*` branches; nothing is on upstream.

## CI

CI stays off on the fork (owner's decision, 2026-11-01): workflows don't run on pushes or PRs, so no PR has checks. On 2026-11-03, the `tests` workflow was started once by hand (`workflow_dispatch`) on `fix/ref-sibling-definitions`, without knowledge of that decision: all 15 jobs (Python 3.10 to 3.14 on Linux, macOS, Windows) passed, without the official suite, which the workflow doesn't check out.
