#!/usr/bin/env python3
"""Read-only lint for the Agent Rules Markdown convention; Python standard library only."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys


CATEGORIES = {"Context", "Action", "Dependency", "Check"}
HEADING = re.compile(r"## ([^:]+): (\S.*)")
LEGACY = re.compile(
    r"(?:\[(?:orient|tether|always|never|prefer|avoid|caveat|verify)\] "
    r"|## (?:rule|gotcha|see also): ?)(\S.*)"
)
BOUNDARY = re.compile(r"^\s*(?:#|\[[a-z-]+\](?:\s|$))")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
BLOCK = re.compile(
    r"^(?: {4}|\t| {0,3}(?:`{3,}|~{3,}|>|[-+*]\s|\d+[.)]\s|\|"
    r"|(?:[-*_]\s*){3,}$))"
)
KEYWORD = re.compile(r"\b(?:MUST|SHALL|SHOULD|MAY|REQUIRED|RECOMMENDED|OPTIONAL)\b")
LOWERCASE = re.compile(r"\b(?:must|shall|should)\b")
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "__pycache__"}
LONG_BODY_WORDS = 120
FILE_RULE_LIMIT = 10
FILE_TOKEN_LIMIT = 1000
CHAIN_TOKEN_LIMIT = 5000


@dataclass(frozen=True)
class Finding:
    line: int
    severity: str
    code: str
    message: str


def estimate_tokens(text):
    """Rough characters/4 estimate, rounded up; not a model tokenizer."""
    return (len(text) + 3) // 4


def lint_text(text):
    """Return findings with one-based lines; semantic correctness remains a human review."""
    lines = text.splitlines()
    findings = []
    starts = []
    fence = None
    for index, line in enumerate(lines):
        marker = FENCE.match(line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not tail.strip():
                fence = None
        elif fence is None and BOUNDARY.match(line):
            starts.append(index)

    def report(index, severity, code, message):
        findings.append(Finding(index + 1, severity, code, message))

    preamble_end = starts[0] if starts else len(lines)
    preamble = next((i for i in range(preamble_end) if lines[i].strip()), None)
    if preamble is not None:
        report(preamble, "error", "E001", "Text outside a rule; start with '## Category: Title'.")
    if not starts and preamble is None:
        report(0, "error", "E001", "No rules found.")

    titles = {}
    legacy_lines = []
    rule_count = 0
    for number, start in enumerate(starts):
        end = starts[number + 1] if number + 1 < len(starts) else len(lines)
        heading = lines[start]
        old = LEGACY.fullmatch(heading)
        current = HEADING.fullmatch(heading)
        if old:
            legacy_lines.append(start)
            category, title = None, old[1]
        elif current and current[1] in CATEGORIES and not re.search(r"\s#+\s*$", current[2]):
            category, title = current.groups()
        else:
            report(start, "error", "E002", "Use '## Context|Action|Dependency|Check: Title'.")
            continue

        rule_count += 1
        key = " ".join(title.split()).casefold()
        if key in titles:
            report(start, "error", "E003", f"Duplicate title; first used on line {titles[key]}.")
        else:
            titles[key] = start + 1
        content = [(i, lines[i]) for i in range(start + 1, end) if lines[i].strip()]
        if not content:
            report(start, "error", "E004", "Rule body is empty.")
            continue
        if old:
            continue  # Legacy rules remain supported without imposing the new body format.

        if start and lines[start - 1].strip():
            report(start, "error", "E005", "Separate adjacent rules with a blank line.")
        if lines[start + 1].strip():
            report(start + 1, "error", "E005", "Add a blank line after the rule heading.")
        first, last = content[0][0], content[-1][0]
        if any(not lines[i].strip() for i in range(first, last + 1)):
            report(first, "error", "E006", "Use one paragraph per rule; move detailed procedures to documentation.")
        block = next((i for i, line in content if BLOCK.match(line)), None)
        if block is not None:
            report(block, "error", "E006", "Use paragraph text with inline code, not lists, tables, or code blocks.")

        body = "\n".join(line for _, line in content)
        prose = re.sub(r"(`+).*?\1", "", body, flags=re.DOTALL)
        if category != "Context" and not KEYWORD.search(prose):
            report(first, "error", "E007", "Add an explicit BCP 14 requirement keyword outside inline code.")
        if LOWERCASE.search(prose):
            report(first, "warning", "W002", "Lowercase must/shall/should may be ambiguous; review intended strength.")
        if re.search(r"\bMAY\s+NOT\b", prose):
            report(first, "warning", "W003", "MAY NOT is ambiguous; distinguish prohibition from uncertainty.")
        if len(body.split()) > LONG_BODY_WORDS:
            report(first, "warning", "W004", f"Body exceeds {LONG_BODY_WORDS} words; consider shortening it.")

    if legacy_lines:
        report(legacy_lines[0], "warning", "W001",
               f"Legacy syntax in {len(legacy_lines)} rule(s); preserve meaning during incremental migration.")
    if rule_count > FILE_RULE_LIMIT:
        report(0, "warning", "W006",
               f"{rule_count} rules exceeds {FILE_RULE_LIMIT}; review density and scope, preserving useful safeguards.")
    tokens = estimate_tokens(text)
    if tokens > FILE_TOKEN_LIMIT:
        report(0, "warning", "W007",
               f"Approximately {tokens} tokens (characters/4) exceeds {FILE_TOKEN_LIMIT}; review file size.")
    return sorted(findings, key=lambda finding: (finding.line, finding.code))


def discover(paths):
    """Yield distinct files; report failed inputs rather than silently claiming a clean scan."""
    files = set()
    for value in paths:
        path = Path(value).absolute()
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            def fail(error):
                raise error

            for directory, dirs, names in os.walk(path, onerror=fail, followlinks=False):
                dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
                files.update(Path(directory) / name for name in names if name.casefold() == "agents.md")
        else:
            raise FileNotFoundError(f"Input does not exist or is not a file/directory: {path}")
    if not files:
        raise FileNotFoundError("No AGENTS.md files found in the supplied paths.")
    distinct = {}
    for path in sorted(files):
        distinct.setdefault(path.resolve(), path)
    return list(distinct.values())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chain", action="store_true",
                        help="also budget explicit applicable rule files together; include required references")
    parser.add_argument("paths", nargs="+", help="AGENTS.md files or directories to scan recursively")
    args = parser.parse_args(argv)
    if args.chain and any(Path(path).is_dir() for path in args.paths):
        parser.error("--chain accepts explicit files only, not a directory scan")
    try:
        files = discover(args.paths)
    except OSError as error:
        print(f"error E_IO: {error}", file=sys.stderr)
        return 2

    errors = warnings = read_errors = 0
    chain_characters = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
            findings = lint_text(text)
        except (OSError, UnicodeError) as error:
            print(f"{path}:1: error E_IO: {error}", file=sys.stderr)
            read_errors += 1
            continue
        chain_characters += len(text)
        if path.name != "AGENTS.md":
            findings.insert(0, Finding(1, "warning", "W005", "Use the canonical filename AGENTS.md."))
        for finding in findings:
            print(f"{path}:{finding.line}: {finding.severity} {finding.code}: {finding.message}")
            errors += finding.severity == "error"
            warnings += finding.severity == "warning"
    if args.chain:
        if read_errors:
            print("Selected rule chain: incomplete; resolve read failures before assessing its budget.")
        else:
            tokens = (chain_characters + 3) // 4
            print(f"Selected rule chain: {len(files)} distinct file(s), approximately {tokens} tokens (characters/4).")
            if tokens > CHAIN_TOKEN_LIMIT:
                print(f"{files[0]}:1: warning W008: Selected rule chain exceeds {CHAIN_TOKEN_LIMIT} estimated tokens; "
                      "review combined scope and duplication, not just individual files.")
                warnings += 1
    print(f"{len(files)} file(s): {errors} error(s), {warnings} warning(s), {read_errors} read failure(s).")
    return 2 if read_errors else 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
