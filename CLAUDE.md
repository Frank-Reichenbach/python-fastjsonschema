# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

The Makefile builds a `venv/` (via `virtualenv`, installing `-e .[devel]`) and runs everything inside it:

- `make test`: initializes the `JSON-Schema-Test-Suite` git submodule, then runs `pytest -W default --benchmark-skip`
- `make test-lf`: reruns only the tests that failed last time
- `make lint`: `pylint fastjsonschema` (config in `pylintrc`)
- `make benchmark-save` before a change, then `make benchmark` after it: compares the results and fails on a regression of more than 5% (`min`)
- `make printcode`: prints the code generated for `schema.json`. For any schema, use `python3 -m fastjsonschema < schema.json`
- `make performance`: compares this library against other validators (`performance.py`)
- `make doc`: Sphinx docs in `docs/`. The user-facing documentation is the module docstring of `fastjsonschema/__init__.py`

Run a single test with `venv/bin/python -m pytest --benchmark-skip tests/test_format.py -k datetime`.

CI (`.github/workflows/tests.yml`) runs `pipx run tox -e py -- -vvv` on Python 3.10–3.14 on Linux, macOS and Windows. tox runs `pytest -m "not benchmark"`.

The tests in `tests/json_schema/` read the official test suite from the `JSON-Schema-Test-Suite` submodule. If the submodule isn't checked out, pytest skips them (empty parameter set) instead of failing, so run `git submodule update --init` first (`make test` does this for you).

## Architecture

fastjsonschema doesn't interpret a schema at validation time. It **generates Python source code** for a validation function and `exec`s it. `compile()` returns that function, and `compile_to_code()` returns the source as a string so it can be saved as a standalone module.

- **Draft selection** (`_get_code_generator_class` in `__init__.py`): picks the generator class from the `$schema` string. Without `$schema` (or with a boolean schema), `CodeGeneratorDraft2019` is used. Some docstrings still say that draft-07 is the default, but the code uses Draft2019.
- **Generator hierarchy**: `CodeGenerator` (`generator.py`) → `CodeGeneratorDraft04` → `Draft06` → `Draft07` → `Draft2019`. Each subclass:
  - extends `FORMAT_REGEXS`, the built-in format regexes. Changes to the `date-time`, `time` and similar formats go here.
  - registers keyword handlers in `self._json_keywords_to_function`, an ordered mapping from keyword to `generate_*` method.
  - `run_generate_functions` calls the handler of every keyword that is present in the schema. `$ref` is the exception: when it is present, its sibling keywords are ignored.
- **Code emission helpers** in `CodeGenerator`:
  - `self.l(line, ...)` emits a line. The line is `str.format`ted with `variable`, `name` (the data path for error messages), every key of the current definition, and any extra arguments. As a context manager, it indents the block inside it.
  - `self.exc(msg, rule=...)` emits the code that raises the error, or appends it to `errors`.
  - `self.e()` escapes a value for use inside a string literal. `repr_default`/`repr_regex` serialize values into the code.
  - Because schema values end up in generated source, anything taken from the schema must be escaped or `repr`'d, never interpolated raw (see `tests/test_security.py`). Curly braces in property names are a related trap: they would be read as `format` placeholders.
- **`$ref` resolution** (`ref_resolver.py`): `RefResolver` walks the schema and maps each referenced URI to a separate generated function (`_needed_validation_functions`). Remote refs are loaded through the `handlers` (URI scheme → callable).
- **`fast_fail=False` mode**: the generated function collects errors into a list and raises `JsonSchemaValuesException`. Subschemas that are only tried out (anyOf, oneOf, not, if, contains, propertyNames) are generated inside `trial_validation()`, which forces fast-fail because their failure is control flow, not an error to report. `$ref` calls merge the errors of the referenced function. Every keyword change has to work in both modes.
- **Exceptions** (`exceptions.py`): `JsonSchemaValueException` (invalid data; has `.name`, `.path`, `.rule`, `.definition`), `JsonSchemaValuesException` (all collected errors), `JsonSchemaDefinitionException` (invalid schema).

## Tests

- Most unit tests use the `asserter` fixture from `tests/conftest.py`. It prints the generated code (visible when a test fails) and compares the exception's message, value, name, definition and rule. It sets `$schema` to **draft-04** unless the test definition sets one, so tests for later-draft keywords must set `$schema` explicitly.
- `tests/json_schema/test_draft*.py` turn the official suite into parametrized tests and run each case with `fast_fail` both on and off. `ignored_suite_files` (and `ignore_tests`) mark known failures as non-strict `xfail`. After fixing one, remove it from the list, otherwise the fix is only reported as XPASS and the test doesn't guard against regressions.

## Reviews with Codex

Until further notice, every Codex run uses GPT-6.1 Terra with high reasoning effort. Pass both explicitly on each call instead of relying on defaults:

```bash
codex exec -m gpt-6.1-terra -c model_reasoning_effort='"high"' ...
```

`.codex/config.toml` sets the same model and effort for interactive Codex sessions in this repository.

## Conventions

Every user-visible fix or feature gets a line in the `=== UNRELEASED` section of `CHANGELOG.txt`. The version is kept in `fastjsonschema/version.py`, and `setup.py` reads it from there.
