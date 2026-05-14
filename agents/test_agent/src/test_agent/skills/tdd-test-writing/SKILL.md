---
name: tdd-test-writing
description: Write pytest test files following TDD — tests must fail before any implementation exists. Covers happy path, edge cases, and error cases. Writes the file using write_file to the path given in instructions.
allowed-tools: [read_file, write_file, glob, grep]
---
## Steps
1. `write_todos`: identify test cases from the feature spec
2. Write parametrized tests covering happy path, edge cases, and error cases
3. Use fixtures in conftest.py where appropriate; use monkeypatch for external dependencies
4. `write_file` the test file to the exact path provided in your instructions
5. Tests MUST fail (ImportError or AssertionError) before any implementation — never write tests that pass immediately

## Coverage targets
- Line: ≥80%
- Branch: ≥70%

## Conventions
- Use `pytest.mark.parametrize` for multiple input/output cases
- Group related tests in classes
- Name tests `test_<behaviour>_<condition>`
- Import the module under test inside the test function to produce ImportError (not at top of file)
