# CHANGELOG

## [Unreleased]


## [0.9.2] - 2025-06-16

### Added
- Major enhancements to the HTML report generator (`recap_json_to_html.py`):
  - Switched ANSI-to-HTML rendering from Rich to ansi2html for terminal-style colored output in error/traceback and captured output sections.
  - Improved CSS and HTML structure for colored output, whitespace, and monospace formatting.
  - Multi-session navigation UI: dropdown/session selector for viewing multiple TestSessions in a single report.
  - Outcome filter checkboxes reinstated and fixed for both single- and multi-session reports.
  - Charts now render correctly for each session in multi-session HTML reports.
  - Added "HTML File Generated: <timestamp>" metadata in reports.
- Project release workflow shortcut: /release rule added for versioning, changelog, and README update automation.

### Changed
- Updated HTML template to remove <pre> wrappers and use ansi2html-compatible <div> blocks for colored output.
- Improved test data and demo suite for more diverse outcome/duration scenarios.
- Enhanced robustness of TestSession and nested model deserialization (ignores extra keys).

### Fixed
- Bug: Charts not displaying for single-session HTML reports.
- Bug: Test result details not expanding/collapsing after outcome filter reinstatement.
- Bug: Template file accidental deletion now documented and recovery steps clarified.

## [0.9.1] - 2025-06-14

### Added
- New HTML report generator (`recap_json_to_html.py`) for pytest-recap sessions.
  - Generates a modern, interactive HTML report from `recap.json`.
  - Features include:
    - Summary stats and pie chart of outcomes
    - Expandable/collapsible test details
    - Sortable and filterable results table
    - Session metadata section (collapsible)
    - Outcome filtering and master toggle
    - User-friendly, responsive design
- Documentation and usage instructions for the HTML report in README.
- New `--recap-pretty` CLI flag, `RECAP_PRETTY` environment variable, and `recap_pretty` ini option for controlling recap JSON output format (pretty-printed or minified). Default is minified. Precedence: CLI > ENV > INI > default.
- Tests for pretty/minified output at both plugin and storage layers.

### Changed
- Improved duration formatting in HTML reports: durations <10s now display with 6 decimal places (e.g., `0.123456s`), while longer durations are shown in human-friendly formats (`1m 2s`, `2h 3m 4s`).
- Session metadata extraction is now robust to both root-level and nested JSON structures; session duration and human-readable duration are always computed and displayed.
- Warnings and errors are deduplicated by `(nodeid, message)` to reduce noise in reports.
- Test results table now always sorts by outcome and start time for consistency.
- Outcome percentages are now computed and displayed in the report summary.
- Added a `main(json_path, html_path)` entrypoint to `recap_json_to_html.py` for easier CLI and test integration.
- Improved test suite: updated duration tests, removed legacy/broken test for rerun group rendering, and fixed imports and assertions for robustness.
- Recap JSON format now uses timezone-aware UTC timestamps for all session/test times.
- `TestSessionStats` constructor and usages now require `warnings_count` (plural) for consistency.
- `RecapEvent` API provides `.is_warning()` and `.is_error()` helpers for event type checks.
- All logger calls use `logger.warning` (not `logger.warnings`).
- Updated recap.json sample and documentation to match new format.
- Improved test coverage and restored/fixed test suite (including demo suite failures and expected errors).
- Codebase uses `ruff` and `ruff format` for linting/formatting; pre-commit hooks recommended.

### Fixed
- Robust handling of ini values for session metadata (now always parsed as string, even if provided as a list by pytest).
- Warning messages for invalid session metadata now always reference the correct environment variable or CLI option, improving clarity and testability.
- Improved debug output for session metadata resolution and parsing.

## [0.8.0] - 2025-05-21

### Added
- Refactored session schema: replaced `sut_name` with `system_under_test` (now a dict), and updated all code/tests accordingly.
- Enhanced both `system_under_test` and `testing_system` fields for user-extensible metadata.
- Improved JSON schema: added recommended keys, allowed custom properties, and linked schema in README.
- Expanded and clarified README: added schema section, extensibility guidance, example output, and a neutral comparison with JUnit-XML and pytest-json-report.
- Added `demo-tests/README.md` to clarify demo structure and subfolder purposes.

### Changed
- Updated plugin logic and file naming to use new extensible fields.
- Improved concurrency: added thread/process safety to JSONStorage using threading.RLock and FileLock.
- Made session loader stricter: only accepts lists or dicts with 'sessions' key as valid session lists.
- Improved test coverage and reliability, including edge cases and permission scenarios.
- Updated pre-commit config to match pytest's standard test file naming convention (`test_*.py`).

### Fixed
- Fixed and clarified permission error handling and related tests for robust cross-platform behavior.
- Addressed linter feedback and pre-commit hook config issues.

---

## [0.7.0] - 2025-05-06

### Added
- Initial implementation of core recap models and storage logic.
- Full support for rerun test groups and session metadata.
- Pre-commit hooks for code quality: ruff, isort, pytest-cov.
- Integration tests and coverage for models, storage, and plugin.
- Support for cloud storage recap output: S3 (`s3://`), Google Cloud Storage (`gs://`), Azure Blob Storage (`azure://`).
- Parametrized tests for cloud upload logic (mocked and moto-backed).
- Color-highlighted recap output path/URI in terminal.

### Changed
- README and documentation fully updated for release, including cloud configuration, test strategy, and developer workflow.
- Test suite: S3 tests now skipped unless `moto` and `boto3` are installed; GCS/Azure use direct mocking for speed and minimal deps.
- Improved error handling and output clarity for cloud upload failures.
- Recap JSON schema: added `warnings`, `errors`, and `session_stats` fields.
- Refactored `SessionStats` to `TestSessionStats` for clarity.
- Output recap file path/URI is now color-highlighted in the terminal.
- Overhauled plugin and test structure for maintainability and extensibility.

### Fixed
- Improved test coverage and reliability.
- Various README and doc updates.

### Removed
- Obsolete `hello()` stub from `pytest_recap/__init__.py`.
- Black from dependencies (using ruff format instead).

---

### Previous (pre-v0.7.0) commit history:

```
81b2796 Release v0.7.0
46907e1 Overhaul on all fronts.
e457832 Update README.md
fd92026 Update README.
e953802 Bump version to 0.4.0, add requests dependency, and adjust session_tags serialization in models.py. Add a bunch of unit tests for models.py.
1df59dd Added conftest.py to test/ dir with ‘tester’ fixture that provides either testdir or pytester test fixture depending on version of Pytest running. Also added more coverage to plugin.py.
0621ffd Removed black from dependencies (we have ruff format now).
c8925b9 Add support for rerun test groups. Add pre-commit, ruff, isort, and pytest-cov via pyproject.toml.
96c45d2 Initial commit. models.py and storage.py in place, fully implemented, with unit tests. Next: plugin.py; dev tools/process.
b4b2aea Initial commit
