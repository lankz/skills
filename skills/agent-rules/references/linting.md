# Linting AGENTS.md files

Run `scripts/lint_rules.py` from this skill with Python 3.9 or newer. It uses only the standard library and never edits files. Substitute the actual skill installation path in these examples:

```sh
python3 /path/to/agent-rules/scripts/lint_rules.py AGENTS.md app/views/AGENTS.md
python3 /path/to/agent-rules/scripts/lint_rules.py /path/to/repository
python3 /path/to/agent-rules/scripts/lint_rules.py --chain AGENTS.md app/AGENTS.md app/views/AGENTS.md
```

The first invocation checks specific files after edits. The second discovers AGENTS.md files recursively for an audit. Multiple inputs are accepted and paths resolving to the same file are deduplicated. Discovery includes hidden and ignored directories, except `.git`, `.hg`, `.svn`, `node_modules`, `.venv`, and `__pycache__`; it does not follow discovered directory symlinks. Explicit file paths can target excluded locations. Report these discovery limits when they affect requested coverage. Lowercase filenames are discovered but receive a naming warning.

The third invocation also checks a selected chain's combined size. `--chain` accepts explicit files only: supply every applicable ancestor and additional rule file required by the task, including transitive references. The agent resolves conditional references and scope; the script does not infer them or load omitted ancestors. Run separate checks for distinct applicable chains, not the whole repository as one chain. A normal directory scan checks file sizes but does not assess chain completeness or totals. Failed reads make the selected chain assessment incomplete.

Output uses `absolute-path:line: severity code: message`, followed by counts. Exit status is 0 for no errors (warnings may remain), 1 for lint errors, and 2 for usage or discovery/read failures. An empty scan or missing input fails rather than reporting a clean result.

## Diagnostics

| Code | Level | Meaning |
|---|---|---|
| E001 | Error | Empty file or text outside a rule |
| E002 | Error | Invalid category or heading syntax, including empty title |
| E003 | Error | Duplicate title within a file, ignoring case and repeated whitespace |
| E004 | Error | Missing rule body |
| E005 | Error | Missing blank line between heading/body or adjacent rules |
| E006 | Error | Multiple paragraphs or detected list, table, quotation, or code-block syntax |
| E007 | Error | Action, Dependency, or Check has no recognized uppercase requirement keyword outside inline code |
| E_IO | Failure | Discovery, input, or decoding failed |
| W001 | Warning | Legacy square-bracket or older heading rules, summarized once per file |
| W002 | Warning | Lowercase must, shall, or should deserves a wording review |
| W003 | Warning | Ambiguous MAY NOT |
| W004 | Warning | Body exceeds 120 whitespace-delimited words |
| W005 | Warning | Filename differs from AGENTS.md |
| W006 | Warning | File exceeds 10 recognized rules, including legacy rules |
| W007 | Warning | File exceeds approximately 1,000 tokens |
| W008 | Warning | Explicit `--chain` selection exceeds approximately 5,000 tokens |

Size warnings use strict greater-than comparisons. Token estimates divide the complete text's character count by four and round up; this is not a model tokenizer or a byte limit. Rule counts include recognized headings even when their bodies or titles have errors, but exclude fenced examples and malformed headings. Aim for 5–8 rules per file without treating that as a minimum. Review size findings using the [maintenance guidance](maintenance.md#review-rule-density-and-inherited-size); warnings remain advisory and do not change exit status.

The 120-word body threshold is also an advisory brevity heuristic, not a token count or a standard. Lowercase modal words are not RFC violations. The linter accepts all BCP 14 equivalents; the authoring convention prefers MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY.

Legacy rules retain body-format compatibility and produce a migration warning; their heading titles and nonempty bodies are still checked. This permits a file to migrate incrementally. Do not reinterpret its policy or rewrite an entire repository merely to remove warnings.

## Agent workflow

After rule edits, check the surviving changed files and fix task-introduced errors. Review warnings before deciding whether to edit: capitalization can change meaning. Preserve authorized exceptions and existing policy, and follow the maintenance proposal workflow where a decision is needed. Recheck files after corrections.

For a requested audit, start with the directory scan. Report structural errors separately from advisory warnings and semantic findings. Mention failed reads or excluded areas that limit coverage. Do not describe exit 0 as “no findings” when warnings were emitted.

The script checks a restricted authoring format, not arbitrary Markdown conformance. Keyword presence is a lexical check: a quotation of MUST in prose can satisfy it without conveying an operative obligation. It cannot prove that rules agree, are enforceable, have appropriate scope, belong in the right directory, retain valid references, or capture all useful gotchas. These require reading the rules and relevant code. No automatic fixes or policy inference are performed.

## Maintaining the linter

Run its behavior tests after changing the script:

```sh
python3 -B -m unittest discover -s /path/to/agent-rules/scripts -p 'test_*.py'
```

Use temporary files for scan and CLI tests. Keep the convention, diagnostics, and skill workflow aligned with changes to lint behavior.
