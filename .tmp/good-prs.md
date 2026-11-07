# Good pull requests: general practice, fastjsonschema specifics, and the merged rules

Date: 2026-10-25. Target repository: `horejsek/python-fastjsonschema`.

> **Status 2026-11-03.** Still applies; the fork PRs follow Part 3. The repository facts in Part 2 are as of 2026-10-25 (`master` `738da70`); upstream `master` is now `4999d6b` (2.22.3).

This document has three parts:

1. What makes a pull request (PR) well written, from widely cited guides and the templates of large projects.
2. What the fastjsonschema repository requires of a PR, explicitly and by convention.
3. Merged rules for a PR to fastjsonschema. Where the two disagree, the repository wins.

---

## Part 1: What makes a PR well written (general research)

### Sources compared

Google and GitHub are included as widely cited guides. The other sources are large FOSS projects.

| Source | Form | What it asks for |
|---|---|---|
| Google, [Writing good CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html) ("CL", change list, is Google's term for roughly a PR) | Guide | First line: "a short, focused summary", "a complete sentence, written as though it were an order (an imperative sentence)" ("Delete the FizzBuzz RPC and replace it with the new system."). Body: explain **why**, the problem and why this approach, known shortcomings, background. Don't rely only on links, because they may be inaccessible later. "Fix bug" is a bad description. Review the description before submitting, so that it "still reflects what the CL does". |
| Linux kernel, [Submitting patches](https://docs.kernel.org/process/submitting-patches.html) | Guide | "Describe your problem" first, then the user-visible impact. Quantify trade-offs. Imperative mood. The description must be "self-contained". "Solve only one problem per patch"; each patch "justifiable on its own merits". Reference commits by at least 12 characters of the SHA-1 and their summary line. |
| GitHub, [Helping others review your changes](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes) | Guide | "Small, focused pull requests are easier to review and safer to merge." A clear title and description cover "the problem, the approach, and the result". Review your own PR first. Link related issues with closing keywords. |
| GitHub, [Allowing changes to a PR branch created from a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork) | Platform docs | "Allow edits from maintainers" lets people with push access to the upstream repository commit to the PR branch. Only the author of a PR from a fork in a personal account can turn it on. If the fork contains GitHub Actions workflows, the option is "Allow edits and access to secrets by maintainers", which can expose the fork's secrets. |
| CPython, [Pull request lifecycle](https://devguide.python.org/getting-started/pull-request-lifecycle/) and `.github/PULL_REQUEST_TEMPLATE.md` | Guide + template | "Most PRs will require an issue number", referenced in the title (`gh-NNNNN: …`); trivial changes don't need one. "Pull requests will not be accepted without the proper tests!" "Keep your pull request focused and small." A short news entry for user-visible changes. Imperative commit subject without a trailing period. During review, don't amend or force-push, because "Reviewers often want to look at individual commits". CPython squash-merges the PR afterwards. |
| CPython devguide, [Guidelines for using AI tools](https://devguide.python.org/getting-started/ai-tools/) | Guide | Authors must review AI output in detail, and are expected to "be able to explain their proposed changes in their own words". Disclosing AI use "is appreciated, while not required". |
| Kubernetes `.github/PULL_REQUEST_TEMPLATE.md` | Template | What type of PR; "What this PR does / why we need it"; linked issues with "Fixes #…"; special notes for the reviewer; a release note for user-facing changes; "AI usage disclosure" (YES/NO, and how). |
| Node.js `.github/PULL_REQUEST_TEMPLATE.md` | Template | "Include tests for any bug fixes or new features"; update documentation if relevant; run the test suite; follow the commit message guidelines; Developer's Certificate of Origin. |
| Django `.github/pull_request_template.md` | Template | Ticket number; a concise branch description; a required AI assistance disclosure ("fully reviewed and verified their output"); a checklist including tests, docs, a commit message "written in past tense … and ends with a period", and that the PR "does not disclose a security vulnerability". |
| Rust `.github/pull_request_template.md` | Template | Disclose LLM use per the project's policy; link a tracking issue if there is one. The PR description becomes part of the merge commit message. |

### Distilled principles

Each principle is followed by the sources it comes from. Part 3 refers to them as P1–P15.

1. **Search for an existing issue first.** (CPython: "assuming you already performed a search on the issue tracker for a pre-existing issue")
2. **One problem per PR.** Keep it small and focused, with no unrelated changes. (Kernel, GitHub, CPython)
3. **Title: one short imperative sentence** that says what the change does. No vague titles such as "Fix bug". (Google, CPython)
4. **Problem first, then the change, then the result.** Explain why the change is needed and why this approach. (Google, Kernel, GitHub, Kubernetes)
5. **Self-contained.** The description must make sense without following links, because links can break. (Google, Kernel)
6. **Link the issue it resolves** with a closing keyword. Some projects require an issue first. (CPython, Kubernetes, GitHub, Django)
7. **Tests are part of the change.** A bug fix comes with a regression test. (CPython, Node.js, Django)
8. **Name shortcomings and trade-offs**, including alternatives that were rejected. (Google, Kernel)
9. **User-visible changes get a release note or changelog entry.** (CPython, Kubernetes, Django)
10. **Review your own PR before asking others,** and check before merging that the description still matches the code. (GitHub, Google)
11. **Commit messages follow the project's format.** Formats differ: CPython and the kernel want an imperative subject (CPython without a trailing period); Django wants past tense and a trailing period. (CPython, Node.js, Django, Kernel)
12. **Keep the review history readable.** CPython asks not to rewrite commits during review, because reviewers want to see individual commits. Extra commits cost nothing there, because CPython squash-merges at the end. How this applies depends on the project's merge method. (CPython)
13. **Disclose AI assistance**, verify the output, and be able to explain the change in your own words. (Kubernetes, Django, Rust, CPython)
14. **Never disclose a security vulnerability in a public PR.** (Django)
15. **From a fork, allow edits by maintainers,** so they can make small fixes without a round trip. Check first that the fork holds no secrets. (GitHub)

---

## Part 2: What fastjsonschema requires of a PR

Checked on 2026-10-25 through the GitHub API, the repository at `master` (`738da70`), and the 20 most recently merged PRs (#180–#227).

### Explicit requirements

| Source | Requirement |
|---|---|
| `.github/` | Contains only `FUNDING.yml` and `workflows/`. There is **no PR template**, and there is no `CONTRIBUTING` file or code of conduct. |
| `.github/workflows/tests.yml` | Runs on every push and pull request. It runs `tox -e py` on Python 3.10–3.14, on Linux, macOS and Windows. It doesn't check out the JSON-Schema-Test-Suite submodule, so CI runs only the unit tests, not the suite: 631 tests passed in the CI run for #227, while with the suite #223 reports 4,512 passed locally. |
| `.github/workflows/codeql-analysis.yml` | CodeQL also runs on PRs to `master`. |
| Workflow approval | PR runs from first-time contributors show `action_required` until a maintainer approves them. That is GitHub's default. |
| `tox.ini` | `tox -e py` runs `pytest -m "not benchmark"`. `tox -e lint` runs `pylint fastjsonschema`. CI runs only `tox -e py`. |
| `Makefile` | `make test` initializes the JSON-Schema-Test-Suite submodule and runs pytest. `make lint` runs pylint. |
| `SECURITY.md` | "If you discover a security vulnerability in this project, please report it privately by email: **fastjsonschema@horejsek.com** … Please do not open public GitHub issues for security vulnerabilities." Assumption: the same applies to a public PR, which discloses the problem just as much. |

### Conventions visible in merged PRs

- **Merge commits, not squash.** All 20 PRs were merged with "Merge pull request #N from …", so a PR's commits land in `master` unchanged. 18 of the 20 PRs have one commit. In 15 of those, the commit subject equals the PR title (for example #219, #223, #225, #227). The exceptions are #202, #206 and #214.
- **Titles** are plain descriptive sentences, mostly imperative, without a type prefix: "Fix relative refs in handler-loaded schemas" (#219), "Accept one group before '::' in the ipv6 format" (#223). One Conventional Commits title was also merged ("fix: don't leak variables from not blocks into the outer scope", #209).
- **Descriptions vary from empty (#203) to about 2,800 characters (#214).**
  - Short ones state the fix and the issue. For example, #219: "Avoid resolving relative refs twice … Fixes horejsek/python-fastjsonschema#218".
  - Longer ones, from two contributors (#214; #223, #225 and #227 by the same author), follow a pattern. They give the problem with a runnable example, the cause and the change. Then a "Tests" part names what was added, what fails on `master`, and any manual comparison.
- **Tests come with almost every code change.** 13 of the 15 PRs that change `fastjsonschema/` also add or change tests. The exceptions are #198 and #183.
- **Linked issues are optional.** "Fixes #N" is used when an issue exists (#209, #212, #219). Several fixes came without an issue (#214, #223, #225, #227).
- **`CHANGELOG.txt` is optional.** Four of the 20 PRs touch it (#206, #214, #225, #227). Its entries start with "Fixed …" or "Added …". The unreleased heading has changed over time; today it is `=== UNRELEASED`.
- **No formal reviews.** None of the 20 PRs has a GitHub review, and 11 have no comments. The maintainer merges without a formal review. Time to merge ranged from the same day to 271 days.
- **Rewriting a PR after comments is accepted, and so are extra commits.** #198 and #214 were force-pushed after maintainer comments, and both were merged. #196 added a second commit instead and was merged with two commits.
- **The maintainer can push to a contributor's branch.** Among the 20 checked PRs, this happened once: in #209 the maintainer committed a merge of `master` (`606503d`) to the contributor's branch.
- **The maintainer sometimes fixes reported problems directly** in their own commits instead of through a PR (for example `3926b2e` for issue #220).
- **AI assistance is accepted when disclosed.** #207 carries a full disclosure, and #209's commit and description end with `Assisted-by: ClaudeCode:claude-fable-5`. #223, #225 and #227 say they were made with Claude Code. All were merged without comment on the AI use.
- **Branch names** in contributors' forks are free-form, often `fix/…` or `fix-…`.
- **Open PRs:** seven PRs were open on 2026-10-25 (#222, #224, #226, #228–#231). Some touch nearby code, for example #228 on the date formats.

---

## Part 3: Merged rules for a PR to fastjsonschema

### Precedence

**fastjsonschema requirements > fastjsonschema conventions > general principles.** The repository's practice wins where it differs from the general research. Where the repository says nothing, the general principles apply.

The owner's own rules (attribution, writing style) always apply. If one of them ever conflicts with a repository requirement, ask the owner before opening the PR.

### Decisions

| Topic | General principle | fastjsonschema | Decision |
|---|---|---|---|
| Duplicates | Search for an existing issue (P1) | Seven open PRs, some in nearby code | Search open issues and also open PRs for the same problem before opening. |
| Scope | One problem per PR (P2) | Recent PRs fix one thing each | One bug per PR. Related but separate problems get their own PR. |
| Title | Short imperative sentence (P3) | Plain sentence, mostly imperative, no prefix; usually equals the commit subject | Imperative sentence without a type prefix, identical to the commit subject. |
| Commits | Project's format (P11) | Merge commits keep every commit; 18 of 20 PRs have one commit | One commit. Its message must stand on its own in `git log`: problem, cause, change. |
| Description layout | Problem, change, result; self-contained (P4, P5) | No template; longer descriptions give the problem with an example, the cause, the change, "Tests" | Problem with a short runnable example, cause, change, decisions where needed, "Tests". Use headings only where they help. Keep it as short as the change allows; merged descriptions range from empty to about 2,800 characters. |
| Issue link | Link with a closing keyword; some projects require an issue (P6) | Optional; "Fixes #N" when an issue exists | If an upstream issue exists, add "Fixes #N". If not, the description carries the reproduction, so it doesn't depend on an issue. A bare `#N` links to an issue in the same repository. For an issue elsewhere, use the full form `owner/repo#N`, as #219 did. |
| Tests | Required for a bug fix (P7) | 13 of 15 code PRs add tests | Regression tests that fail on `master`. Say in the description which tests were added and that they fail on `master`. |
| Changelog | Release note for user-visible changes (P9) | Optional; four merged PRs added a line | Add one line under the current unreleased heading, starting with "Fixed …" like the existing entries. |
| Trade-offs | Name rejected alternatives (P8) | Longer PRs explain the approach (#214, #223) | A short "Decisions" part when the approach isn't obvious, with the rejected alternative and why. |
| Review history | Don't rewrite during review (P12); CPython can afford the extra commits because it squash-merges | Merge commits keep every commit; force-pushes after comments were accepted (#198, #214) | Keep one commit. After a review comment, amend and push with `--force-with-lease`, and say in a PR comment what changed. Extra fix-up commits would stay in `master`, because fastjsonschema doesn't squash. |
| Self-review | Review your own PR first (P10) | CI runs only the unit tests | Before opening: run `make test` (with the JSON-Schema-Test-Suite) and `make lint`, read the diff, and re-check every claim in the description. |
| AI disclosure | Disclose and verify (P13) | Accepted, including `Assisted-by:` trailers in commit and description (#209) | End both the commit message and the PR description with the owner's attribution trailers as the final paragraph. Use one `Assisted-by: <model> (code generation)` line per vendor, plus a `(code review)` line if a review took place. Name the latest model, or the most expensive one of the same release. No `Co-Authored-By` trailer and no "Generated with Claude Code" footer. |
| Security | Never in a public PR (P14) | `SECURITY.md`: report vulnerabilities privately by email | If the bug could be a vulnerability, the owner emails fastjsonschema@horejsek.com with a description and steps to reproduce, and opens no public issue or PR. Open a public PR only when the bug is clearly not a vulnerability, or after the maintainer agrees by email. |
| Maintainer edits | Allow edits from a fork (P15) | The maintainer pushed to a contributor's branch once among the 20 checked PRs (#209) | Leave "Allow edits and access to secrets by maintainers" enabled, as long as the fork holds no secrets. If it does, decide this separately. |
| Writing | Clear and precise (P3–P5) | Matter-of-fact descriptions | Plain, factual English. Short sentences, active voice, no claims about the quality of the work. |

### Checklist before opening the PR

1. Open issues and open PRs upstream have been searched for the same problem.
2. Whether the bug could be a security vulnerability is settled, by email if in doubt.
3. The branch is based on the current upstream `master` and contains one commit.
4. `make test` (with the JSON-Schema-Test-Suite) and `make lint` pass, and the new tests fail on `master`.
5. `CHANGELOG.txt` has one line under the current unreleased heading.
6. The title equals the commit subject, an imperative sentence without a prefix.
7. The description states the problem with a short example, the cause, the change and the tests. It reads on its own.
8. No bare `#N` refers to an issue outside the repository.
9. The commit message and the description both end with the attribution trailers.
10. "Allow edits and access to secrets by maintainers" is enabled, and the fork holds no secrets.
