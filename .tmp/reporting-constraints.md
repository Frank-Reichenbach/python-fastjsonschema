# Reporting constraints: how to file the `urn:` `$ref` scope bug upstream

Date: 2026-10-25. Target: `horejsek/python-fastjsonschema`. Input: `.tmp/bug-report.md`.

> **Status 2026-11-03.** Parts 1 and 2 still apply to every upstream report. Part 3 is the plan for the `urn:` bug alone, written before the fork issues existed. That bug is now fork issue #1 with PR #2, one of eight issue/PR pairs on the fork (`merge-order.md`, `review/README.md`); its input `bug-report.md` was removed, because issue #1 replaces it. Facts about upstream (open PRs, recent issues) are as of 2026-10-25; upstream `master` is now `4999d6b` (2.22.3), and its open PR #224 overlaps with fork PR #8.

This document has three parts:

1. What large FOSS projects ask of a bug report (general research).
2. What the fastjsonschema repository requires, explicitly and by convention.
3. A merged proposal for filing this bug, in which the fastjsonschema requirements override the general findings.

---

## Part 1: What makes a well-written bug report (general research)

### Sources compared

| Project / source | Form | What it asks for |
|---|---|---|
| CPython (`.github/ISSUE_TEMPLATE/bug.yml`, `config.yml`) | Issue form | Search the tracker first; "clear and concise description"; a [minimal, reproducible example](https://stackoverflow.com/help/minimal-reproducible-example); code as text in fenced blocks, "rather than using screenshots"; CPython versions tested on (required); OS (optional). Support questions are redirected to Discourse. |
| CPython devguide, [Guidelines for using AI tools](https://devguide.python.org/getting-started/ai-tools/) | Guide | "We expect PR authors and those filing issues to be able to explain their proposed changes in their own words. Disclosure of the use of AI tools in the PR description is appreciated, while not required. Be prepared to explain how the tool was used and what changes it made." |
| Rust (`.github/ISSUE_TEMPLATE/bug_report.md`) | Markdown template | "I tried this code", "I expected to see this happen", "Instead, this happened", `rustc --version --verbose`; check whether beta/nightly still has the bug; backtrace in a collapsed `<details>` block. |
| Kubernetes (`.github/ISSUE_TEMPLATE/bug-report.yaml`) | Issue form | What happened; what you expected; "How can we reproduce it (as minimally and precisely as possible)?"; anything else; versions in `<details>`. Security problems: "disclose it privately via https://kubernetes.io/security". |
| Node.js (`.github/ISSUE_TEMPLATE/1-bug-report.yml`) | Issue form | Version on a currently supported release; platform; subsystem; a snippet runnable "without installing third-party dependencies or downloading code from the internet (i.e. no ZIP archive, no GitHub repository, etc.)"; how often it reproduces; "What is the expected behavior? Why is that the expected behavior?"; what you see instead, as text. |
| VS Code (`.github/ISSUE_TEMPLATE/bug_report.md`) | Markdown template | Search existing issues; test the latest (Insiders) build; isolate the cause (disable extensions); versions; numbered steps to reproduce. |
| curl ([`docs/CONTRIBUTE.md`](https://github.com/curl/curl/blob/master/docs/CONTRIBUTE.md) "On AI use in curl", [`docs/VULN-DISCLOSURE-POLICY.md`](https://github.com/curl/curl/blob/master/docs/VULN-DISCLOSURE-POLICY.md)) | Guide | If an AI tool found the problem, "you **must** make sure to reveal this fact"; validate that the issue really exists, because "AI-based tools frequently generate inaccurate or fabricated results"; "it is *rarely* a good idea to copy and paste an AI generated report … Those generated reports typically are too wordy"; and, in its vulnerability policy, about all communication in the project: "Do not lazily paste massive, AI-generated explanations". |
| Mozilla [Bug Writing Guidelines](https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html) | Guide | One bug per report; a summary of about 10 words that names the problem, not "your suggested solution"; precise steps to reproduce ("most important part"); guidance for intermittent bugs; actual vs expected results; "Clearly separate facts (observations) from speculations"; search for duplicates; test the latest version; name the earliest affected version. |
| Django ([Reporting bugs](https://docs.djangoproject.com/en/dev/internals/contributing/bugs-and-features/)) | Guide | Search first; "complete, reproducible, specific bug reports"; "A nice small test case is the best way to report a bug"; add as much debug information as possible; no support questions or long discussions in tickets; security issues "**only**" to a private address, never the public tracker. |
| Simon Tatham, [How to Report Bugs Effectively](https://www.chiark.greenend.org.uk/~sgtatham/bugs.html) | Essay | "let the programmer see the failure with their own eyes"; otherwise detailed instructions to make it fail; report symptoms as well as your diagnosis; exact error messages; version numbers; "Be verbose. Give more information rather than less."; "be precise"; follow the project's own guidelines; "If a programmer asks you for extra information, don't make it up!" |
| GitHub, [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) | Platform docs | Read the security policy shown above the form; fields: summary, details, proof of concept, impact; optional "I used AI assistance to find or write up this report" checkbox. |

All the projects above have broad reach and many contributors. None of them is a JSON Schema project; for the closest peer, see Part 3, step 5.

### Distilled principles

Each principle is followed by the sources it comes from.

1. **Respect the project's own channels and rules first.** Security problems go private; support questions go elsewhere. (Tatham, Django, Kubernetes, CPython)
2. **Search for duplicates first.** (CPython, VS Code, Mozilla, Django)
3. **Check the newest code**, ideally the development branch, and **name the affected versions**, including the earliest one and whether it is a regression. (Rust, VS Code, Mozilla, Node.js)
4. **One bug per report.** (Mozilla)
5. **Title: a short summary of the problem, not the fix.** Mozilla suggests about 10 words. (Mozilla)
6. **A minimal reproduction** (CPython, Kubernetes, Django), pasted as text (CPython) and runnable without third-party code or archives (Node.js).
7. **Actual vs expected result**, as exact text output, **and why** the expected result is right. (Rust, Kubernetes, Node.js "Why is that the expected behavior?", Mozilla, Tatham)
8. **How reliably it reproduces**, and under which conditions. (Node.js, Tatham; Mozilla for intermittent bugs)
9. **Separate facts from speculation.** Diagnosis is welcome but labelled, and never replaces the symptoms. (Mozilla, Tatham)
10. **Versions and environment.** (all templates)
11. **Complete, but structured.** Give everything needed (Tatham: "Be verbose"; Django: as much debug information as possible). Put bulky output in collapsed `<details>` blocks, and keep discussion out of the ticket (Rust, Kubernetes, Django). The sources pull in both directions here; the shared point is that the reader must find the essentials quickly.
12. **Precision, and no invented information.** (Tatham)
13. **AI-assisted reports:** disclose AI use, verify every claim yourself, write short and in your own words, and be able to answer follow-up questions personally. (CPython devguide, curl, GitHub PVR checkbox)

---

## Part 2: Requirements found in the fastjsonschema repository

Checked on 2026-10-25 through the GitHub API and in the repository at `master` (`738da70`).

### Explicit requirements

| Source | Requirement |
|---|---|
| `SECURITY.md` (added 2026-05-23, `8f5c02e`) | "If you discover a security vulnerability in this project, please report it privately by email: **fastjsonschema@horejsek.com**". Include "a description of the issue, steps to reproduce it, and any relevant details". "Please do not open public GitHub issues for security vulnerabilities." It does not define what counts as a vulnerability. |
| GitHub repository settings | Private vulnerability reporting is **enabled** (`GET /repos/…/private-vulnerability-reporting` returns `{"enabled": true}`), but `SECURITY.md` doesn't mention it. Issues are enabled; Discussions are disabled. |
| `compile()` docstring (`fastjsonschema/__init__.py`, `ce2890c`) | The only documented security model: do not compile untrusted **schemas** without custom `handlers`, because of server-side request forgery (SSRF). It doesn't say whether a validation result that is wrong for **data** counts as a vulnerability. |
| Module docstring (`fastjsonschema/__init__.py`, "Note that there are some differences compared to JSON schema standard:") | Lists the documented deviations from the standard: Python regular expressions, the `$` → `\Z` rewrite, and `default` handling. `$id`/`$ref` resolution and URI schemes are **not** listed, so this behaviour is not documented as a deviation. |
| `tests/json_schema/test_draft*.py` | The suite runner marks `ref.json` (draft6, draft7, 2019-09) and `id.json` (all four drafts) as non-strict `xfail`, with "TODO: fix ref". The maintainer knows reference resolution is incomplete, and a failing suite test in those files wouldn't fail fastjsonschema's CI. |

### Absent

- No `.github/ISSUE_TEMPLATE/`, no `CONTRIBUTING`, no code of conduct, no PR template (GitHub community profile: 57 %). `horejsek` is a user account, and there is no account-level `.github` repository.
- No published security advisories (`GET /repos/…/security-advisories` returns an empty list). The earlier security fixes (`65dcd12` deeply nested schemas, `a491757` dependencies escaping) went in as plain commits by the maintainer. `CHANGELOG.txt` marks them explicitly as security fixes ("prevents schema-controlled code injection", "potentially causing denial of service").
- No AI-usage policy.
- Labels (`bug`, `enhancement`, …) exist, but only maintainers can set them, and recent issues mostly have none.

### Conventions visible in recent issues and PRs (2025–2026)

- **The maintainer judges by the spec.** #217 ("Unknown format no longer raises") was closed as "expected behaviour … not following the JSON schema standard". The reporter cited no spec section; only afterwards did they confirm it from the spec. #220 cited Draft-07 sections and was fixed. So citing the relevant sections up front heads off a "works as intended" close.
- **Well-received bug reports are compact and technical.** For example:
  - #218: regression, standalone repro, wrong vs right value, suspected commit, a source-level explanation, related #56. Fixed by the reporter's own PR #219 the next day.
  - #220 (about 60 lines): Summary / Reproduction / Actual result / Expected behavior and why (with Draft-7 links) / Source-level explanation / Environment. Fixed by the maintainer 11 days later: "Thanks for the report, fixed here: <commit>".
  - #208: MWE plus annotated generated code, and links the similar #157. Fixed by the reporter's PR #209.
- **Titles** are single descriptive sentences of 7–13 words with no type tag such as "[Bug]". A regression is flagged with its version: "Regression in 2.22.x: relative $ref in a handler-loaded schema is resolved twice" (#218), "Unknown format no longer raises since 2.22.0" (#217).
- **Related issues are linked** in the body (#218 → #56, #208 → #157).
- **Issue + PR pairs are common.** The PR says "Fixes horejsek/python-fastjsonschema#218" or "Fixes #N".
- **Regression tests** (`tests/…`) are part of every fix PR checked: #207, #209, #219, #223, #225, #227.
- **CHANGELOG lines and long before/after descriptions are optional.** Only #225 and #227, both by the same contributor, touched `CHANGELOG.txt` and described before/after and failing tests in detail. Otherwise the CHANGELOG entries come from the maintainer's own commits, and some fixes have none. #219's description is two lines, and the maintainer answered "Thank you for the report and fix!".
- **Several validation-correctness fixes came as public PRs, with no visible prior report.** #207 (IPv4 leading zeros) cites "CVE-2021-28918, an octal-parsing SSRF class". #225 and #227 fix date-time/time ranges. All three are bugs where invalid input was accepted, and all three were filed after `SECURITY.md` existed. The maintainer merged them publicly, and `CHANGELOG.txt` lists #207 as a plain fix ("Fixed IPv4 validation (rejecting leading zeros)") without a security note.
- **The maintainer also fixes bugs directly in a plain commit**: #220 → `3926b2e`. The security fixes above went in the same way; whether they were reported privately isn't visible.
- **AI disclosure is accepted.** #208 implies AI help with the MWE ("it's easier to produce a MWE now with AI tools"). PR #207 carries a full disclosure that an AI agent (Claude Code) found the bug and wrote the PR. PR #209 ends with the trailer `Assisted-by: ClaudeCode:claude-fable-5`. PRs #225 and #227 say "This change was made with Claude Code". The maintainer merged the PRs and fixed #208 without commenting on the AI use.
- **Attachments** are not needed. #220 attached a ZIP, but all issues carry the repro inline.

---

## Part 3: Proposal: how to file this bug

### Precedence rule

**Explicit fastjsonschema requirements > fastjsonschema conventions > general principles.** Where the general research and the repository disagree, the repository wins. Where the repository says nothing, the general principles apply.

### Override decisions

| Topic | General principle | fastjsonschema requirement or convention | Decision |
|---|---|---|---|
| Channel | Public issue tracker; security issues privately (P1) | `SECURITY.md` names the channel for security vulnerabilities but doesn't define them. Conventions suggest validation-accuracy bugs are treated as ordinary bugs: #207 (despite its CVE reference), #225 and #227 were filed publicly after `SECURITY.md` existed, and none got a security note in the CHANGELOG. | Explicit rule: no say on whether this is a vulnerability. Conventions: "not a vulnerability". So under the precedence rule, filing publicly is acceptable. **Owner's decision:** (a) a short courtesy email first, asking whether the maintainer prefers private handling, with a stated deadline. This is more cautious than the precedents require, but costs only the waiting time, and the bug can make validation accept invalid data. Or (b) file the public issue directly, citing the precedents. **Recommendation: (a)**, because it's a cheap way to respect the policy's intent when you are unsure. |
| Email vs GitHub private vulnerability reporting (PVR) | PVR is the GitHub-native private channel | PVR is enabled; `SECURITY.md` names only email | If (a): **email**, because that is the channel the policy names. Offer PVR in the email if the maintainer prefers it. |
| Template | Use the project's template | None exists | Use the section structure of #220, which the maintainer fixed, merged with the Node.js/Kubernetes fields below. |
| Expected-behaviour justification | "Why is that the expected behavior?" (P7) | The maintainer judges by the spec (#217, #220). The module docstring doesn't list this as a known deviation. | **Required**: cite Draft-07 Core §8.2, §8.2.3 (plain-name identifiers, for the `#name` part), §8.2.4 (the `urn:uuid:…#` example) and §8.3.2, and RFC 3986 §5.2.2, by link and section number. Add that the documented deviations don't include this. The jsonschema comparison (an independent implementation that agrees) comes only from the private Forge evaluation and hasn't been run in this setup. Include it only after running the minimal repro against a named jsonschema version (Re-check row). |
| Diagnosis | Optional, labelled as a guess (P9) | Source-level explanations are welcome (#218, #220, #208) | Include a short, clearly labelled root-cause section with file/function names, and the observed `urljoin` behaviour as fact. |
| Fix | Report the problem, not the fix (P5) | Issue + PR pairs are common and welcome (#218/#219, #208/#209). The maintainer also fixes reported bugs directly. | Keep the fix out of the title. Mention in one line that a fix with tests can follow as a PR. Send the PR only after the channel question is settled. Don't expect that our PR will be the one merged. |
| Scope | One bug per report (P4) | — | **Main report: only the `urn:`/non-hierarchical `$id` bug**, including its `#name` collision (same root cause). Separate problems are not part of it (see steps 4 and 5): the array-keyword problem, which also fails with `http:`, and `$id` next to `$ref` not being registered (a different root cause: `walk` skips the `$id` when the same subschema has a `$ref`; shown by a 2019-09 suite test, and relevant to default users because fastjsonschema uses its 2019 generator when `$schema` is missing). Leave the trailing-newline "not a bug" section out of the upstream text entirely. |
| Versions / regression | Name the affected versions, the earliest one, and whether it is a regression (P3, P10) | Regressions are flagged in titles (#217, #218); recent reports give the version and the runtime | Tested on 2.21.2, 2.22.2 and `master` `738da70`: the `#` and `#/definitions/x` variants fail the same way on all three, so they are **not a regression**. 2.21.2 is only the earliest version tested; the resolver has used `urljoin` since 2018 (`8de0ad2`). The `#name` variant can only be tested from 2.22.0 on, because 2.21.2 doesn't support plain-name refs at all ("Unresolvable ref: foo", even at the root); plain-name support was added in 2.22.0 (`b8c5ce8`). Environment: CPython 3.14.9, macOS. No "regression" in the title. |
| Length | Complete but structured (P11); short, own words for AI-assisted reports (P13) | Compact reports; #220 is about 60 lines with 6 sections | Issue body about as long as #220: seven short sections (facts, expected behaviour, diagnosis and workaround kept apart, P9); extra cases in `<details>`. The email is much shorter than the issue. No process history, review rounds or private project context. |
| Reproduction | Minimal, pasted as text, no archives (P6) | Inline repros; a ZIP isn't needed | Paste the minimal repro inline. Don't attach a ZIP and don't link `.tmp/` paths, which only exist locally. |
| Re-check | Check the newest code (P3) | `master` moves; 7 PRs are open (#222, #224, #226, #228–231) | Right before sending each step, re-run the minimal repro on the then-current `master` and redo the duplicate search. Update the commit in the Environment line. If the jsonschema comparison is to be included, run the minimal repro against a named jsonschema version first; installing it needs the owner's go. |
| AI disclosure | Disclose, verify, own words, be able to answer follow-ups (P13) | Accepted in #207, #208, #209, #225, #227 | The AI provides facts and drafts; the owner edits each text, sends it under their own name, and answers follow-ups personally. Add one line that says exactly that, for example: "Found and analysed with AI assistance (Claude Code). I checked every behavioural claim by running the reproductions on 2.22.2 and master (the `#` and `#/definitions` variants also on 2.21.2), checked the spec references against the texts, and wrote/edited this text myself." |
| Attribution (PR/commits) | — | #209 merged with an `Assisted-by:` trailer | Follow the owner's global instruction (`~/.claude-f1/CLAUDE.md`): every commit message and the PR description end with `Assisted-by: <model> (code generation)` as the final trailer. Name the model that actually generates the code, using the latest/most-expensive rule. No `Co-Authored-By: Claude …` trailer and no "Generated with Claude Code" footer, even though #227 used both. |
| Tone | Courteous and precise (P12) | Short replies from the maintainer, matter-of-fact | One sentence of thanks at most, then facts. No speculation about impact beyond what the repro shows. |

### Step 1 (option (a) only): email to fastjsonschema@horejsek.com

- **Subject:** `fastjsonschema: local $ref inside a urn: $id subschema resolves against the root schema`
- **Who writes it:** the AI provides the facts and a draft; the owner rewrites or edits it into their own words before sending.
- **Body**, short, in this order:
  1. One paragraph: what is wrong (with `urn:` and other non-hierarchical schemes such as `tag:`), which versions are affected, and that it can make validation accept invalid data and reject valid data. Versions: the same results on 2.21.2, so it is not a 2.22 regression; the resolver has used `urljoin` since 2018 (`8de0ad2`), so the bug is probably much older. The `#name` part exists only since plain-name support in 2.22.0.
  2. The minimal reproduction (inline), with actual vs expected output.
  3. Two or three sentences on the cause (`urljoin` and non-hierarchical schemes) and the spec references.
  4. The workaround (absolute self-references).
  5. The question: does the maintainer want this handled privately as a security issue? Offer GitHub private vulnerability reporting as an alternative channel. State the fallback: "If I don't hear back within N days, I'll open a public issue (and a PR with a fix and tests)." The owner picks N before sending (suggestion: 14).
  6. The AI-assistance line.
- **Not in the email:** the full matrix, the separate problems, the newline topic.
- The email is an outward action. Send it only after the owner approves the text and N.

**If the maintainer answers "security issue":**

- Keep it private. Offer the patch privately: by email attachment, or, if the maintainer opens a temporary private fork on a PVR advisory and adds us as collaborators, by pushing it there. Only maintainers can create that fork.
- Hold back any public issue, PR, test-suite contribution (step 5) or discussion until the maintainer has released the fix.
- Expect that the maintainer may fix it directly in a plain commit, as with #220 and the earlier security fixes.

### Step 2: public issue

**When:** directly in option (b). In option (a), when the maintainer agrees or the N days have passed without an answer.

**Title:** one descriptive sentence like #218/#220 (12 words), no type tag, no fix: `Local $ref inside a urn: $id subschema resolves against the root schema`. The Summary says that other non-hierarchical schemes (such as `tag:`) are affected too.

**Body sections**, modelled on #220:

1. **Summary**: 2–3 sentences. Name the `#/definitions/x` and `#name` variants, that other non-hierarchical schemes such as `tag:` are affected too, and that it is not a regression.
2. **Reproduction**: the minimal repro inline, plus the command and the version line.
3. **Actual result**: exact output. In `<details>`, the further observed cases: handler-loaded, Draft-04/06, `#/definitions/x` (wrong definition or `Unresolvable ref`), `#name` collisions with the root, a subschema evaluated in place, `fast_fail` on and off; `http:` as the control.
4. **Expected behavior and why**:
   - Draft-07 Core §8.2, §8.2.3, §8.2.4 (the `urn:uuid:…#` example) and §8.3.2; RFC 3986 §5.2.2 (resolution is the same for every scheme); links.
   - The deviations documented in the module docstring don't cover this.
   - Only if checked first (see the Re-check row): how jsonschema behaves, with its version.
5. **Source-level explanation**, clearly labelled as diagnosis:
   - `RefResolver.in_scope`/`resolving`/`walk` use `urllib.parse.urljoin`, which leaves `#…` unchanged for schemes outside `uses_relative`. Include the three-line `urljoin` demo.
   - Why the tests don't catch it: the official URN tests have the `urn:` `$id` on the root, and fastjsonschema's suite runner marks `ref.json`/`id.json` as `xfail` anyway.
6. **Workaround**: absolute self-references; for `#name`, use JSON pointers instead.
7. **Environment**:
   - fastjsonschema 2.21.2, 2.22.2 and the then-current `master` commit; CPython 3.14.9; macOS.
   - Related: #218 / PR #219 (same resolver, different bug).
   - One line that a fix PR can follow, and the AI-assistance line.

### Step 3 (optional): fix PR

- **When:** only after the channel question is settled. Opening a PR is outward-facing, so it needs the owner's go.
- **Branch** in the fork, re-based on the then-current `master`.
- **Content:**
  - The `_join` helper at all four `urljoin` call sites, including the `walk` rewrite.
  - Regression tests (the consistent upstream convention) for embedded, handler and in-place subschemas; for `#`, `#/definitions/x` and `#name`; in two orderings; with `fast_fail` on and off. Put the refs under dict keywords.
  - Optionally, a `CHANGELOG.txt` line under `=== UNRELEASED`. Upstream accepts this (#225, #227) but doesn't require it, and the maintainer often adds the entries in their own commits. It is the owner's convention for this fork.
- **Description:** short, with "Fixes #<issue>". Structure like #227 (before/after, which tests fail on `master` and pass with the change), but **not** #227's attribution. Use the `Assisted-by:` trailer described above, in every commit and in the PR description.

### Step 4 (later, separate): issue for the array-keyword problem

Independent of the URI scheme. Base it on `array_keyword_separate.py`, and name the 12 failing draft6/draft7 suite tests it explains.

### Step 5 (optional, separate): JSON Schema peers

- **Official test suite:** propose a test case to `json-schema-org/JSON-Schema-Test-Suite` for a non-root subschema with a `urn:` `$id` (draft4: `id`) that refers to itself (`#`, `#/definitions/x`). The suite has no such test for draft4/6/7. fastjsonschema marks the draft6/draft7 `ref.json` as `xfail`, so a new test there wouldn't fail its CI. Draft4 `ref.json` is not `xfail`. Either way, new suite tests only reach fastjsonschema's CI when the pinned submodule is updated. A suite test would document the expected behaviour for every implementation. Follow that repo's contribution rules. If the maintainer chose private handling, wait until the fix is released.
- **`$id` next to `$ref`:** the problem that a `$id` next to a `$ref` is never registered (the 2019-09 test "URN ref with nested pointer ref") has a different root cause (`walk` skips that `$id`). Report it separately if wanted.

### Mapping `.tmp/bug-report.md` to the upstream issue

| `bug-report.md` section | Upstream issue |
|---|---|
| Summary | Shortened into **Summary** |
| Origin | Left out (private project context) |
| Minimal reproduction | **Reproduction** + **Actual result** |
| Observed results (identical for v2.22.2 and `master`) | Condensed into `<details>` under **Actual result** |
| Where: root cause | Shortened into **Source-level explanation** |
| Is this really a bug? Check against the specification | **Expected behavior and why**. Keep the jsonschema comparison only after re-checking it (Re-check row); drop "probe 2" and the Forge reference. |
| Why the official test suite does not catch it | One sentence in **Source-level explanation**, including the `xfail`. The 2019-09 `$id`-next-to-`$ref` note goes to step 5. |
| Workaround | **Workaround** |
| Possible fix (prototyped, not applied to the repo) | One line ("PR can follow"), details in the PR (step 3) |
| Related, separate: inline `$id` subschemas with refs inside array keywords | Separate issue (step 4) |
| Upstream status | Left out; the search result informs the "Related" line |
| Not a bug: trailing newline and `$` in `pattern` | Left out |
