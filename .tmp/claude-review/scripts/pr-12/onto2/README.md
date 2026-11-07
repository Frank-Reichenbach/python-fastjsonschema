# onto2 (archived)

This folder used to be a throwaway git repo. It now holds that repo as
`onto2.tar.gz`, so `.tmp/` contains no nested git repos.

A Claude Code review agent (Claude Opus 5.5) created the repo on 2026-11-03
at 13:13 while reviewing fork PR #12 (`fix/relative-id-resolved-once`).

- **Purpose:** check whether the PR #12 patch (`../cp/`) applies onto the tree
  of `fix/urn-id-local-refs` as it was then. It didn't; the result is in
  `.tmp/claude-review/pr-12-issue-7.md` (finding 1).
- **Contents:** copies of `fastjsonschema/`, `tests/`, `CHANGELOG.txt`; one commit
  `d093b7c "base"` by a placeholder author `r <a@b>`; no remote. The working tree
  lacks 30 test data files that are in that commit (shown as deleted).
- **Archived:** 2026-11-07, the whole folder including `.git` (268 entries).
  Verified before the original was deleted: checksum, `diff -r` byte for byte,
  identical paths/types/modes/sizes, same HEAD/refs/object count/status, and
  `git fsck --full --strict` clean on the extracted copy.

Check and restore (extracts to a folder named `onto2` inside the target, so
use a target outside this folder):

```bash
shasum -a 256 -c onto2.tar.gz.sha256
mkdir -p /path/to/target && tar -xzf onto2.tar.gz -C /path/to/target
```
