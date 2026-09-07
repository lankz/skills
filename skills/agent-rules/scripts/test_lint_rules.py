"""Behavioral checks for the standalone linter; run with unittest discovery."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from lint_rules import discover, lint_text, main


class RuleLintTest(unittest.TestCase):
    def codes(self, text):
        return {finding.code for finding in lint_text(text)}

    def test_valid_categories_wrapping_and_recognized_keywords(self):
        text = """## Context: Shared templates

These templates are shared across accounts.

## Action: Preserve credentials

Agents MUST NOT replace encrypted credentials wholesale.
They MUST merge new values into the existing contents.

## Dependency: Coordinate consumers

Consumer compatibility is REQUIRED before deploying producers.

## Check: Run the focused tests

The focused tests SHALL pass before completion.
"""
        self.assertEqual(lint_text(text), [])
        for word in ["MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY", "OPTIONAL", "RECOMMENDED"]:
            with self.subTest(word=word):
                self.assertEqual(lint_text(f"## Action: A choice\n\nAgents {word} do this.\n"), [])

    def test_malformed_empty_and_duplicate_rules(self):
        cases = {
            "": "E001",
            "Introductory text": "E001",
            "# Action: Wrong level\n\nAgents MUST stop.": "E002",
            "## Unknown: Wrong category\n\nAgents MUST stop.": "E002",
            "## Action: \n\nAgents MUST stop.": "E002",
            "## Action: Closing hashes ##\n\nAgents MUST stop.": "E002",
            "## Check: Empty\n": "E004",
            "## Context: Same title\n\nA fact.\n\n## Action: same title\n\nAgents MUST act.": "E003",
        }
        for text, code in cases.items():
            with self.subTest(text=text):
                self.assertIn(code, self.codes(text))

    def test_spacing_and_paragraph_structure(self):
        self.assertIn("E005", self.codes("## Context: A fact\nSome text."))
        self.assertIn("E005", self.codes("## Context: A fact\n\nText.\n## Context: Another\n\nText."))
        self.assertIn("E006", self.codes("## Context: A fact\n\nFirst paragraph.\n\nSecond paragraph."))
        for body in ["- A list", "1. A step", "> A quote", "| A table |", "    Indented code", "---"]:
            with self.subTest(body=body):
                self.assertIn("E006", self.codes(f"## Context: A fact\n\n{body}"))

    def test_keywords_in_inline_code_do_not_satisfy_requirement(self):
        text = "## Action: Validate wording\n\nInspect `MUST` and ``SHOULD`` in the file."
        self.assertIn("E007", self.codes(text))
        text = "## Action: Validate wording\n\nAgents must inspect `MUST` in the file."
        self.assertEqual(self.codes(text), {"E007", "W002"})

    def test_wording_and_length_are_advisory(self):
        text = "## Action: A choice\n\nAgents MAY NOT do this; they should investigate."
        self.assertEqual(self.codes(text), {"W002", "W003"})
        text = "## Context: Long explanation\n\n" + "word " * 121
        self.assertEqual(self.codes(text), {"W004"})

    def test_mixed_legacy_rules_remain_supported(self):
        text = """[always] Preserve credentials
Merge new values into the existing contents.

## gotcha: Shared templates
These records are intentionally shared.

## rule: Refresh safely
Use the lock.

## see also: Read the lifecycle
Read the lifecycle guide.

## Check: Run focused tests

Focused tests MUST pass.
"""
        findings = lint_text(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual((findings[0].line, findings[0].severity, findings[0].code), (1, "warning", "W001"))
        self.assertIn("4 rule(s)", findings[0].message)

    def test_fenced_examples_are_not_parsed_as_rules(self):
        text = "## Context: Example\n\n````md\n## Action: Fake heading\n\n```\nMUST\n```\n````"
        findings = lint_text(text)
        self.assertTrue(any(finding.code == "E006" for finding in findings))
        self.assertFalse(any(finding.code in {"E002", "E004", "E007"} for finding in findings))
        legacy = "[orient] Read the example\n```md\n## Invalid heading\n```"
        self.assertEqual(self.codes(legacy), {"W001"})

    def run_cli(self, *paths):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main([str(path) for path in paths])
        return result, stdout.getvalue(), stderr.getvalue()

    def test_directory_scan_is_read_only_deduplicates_and_skips_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rule = root / "app" / "AGENTS.md"
            rule.parent.mkdir()
            original = "[always] Use the wrapper\nUse the development wrapper.\n"
            rule.write_text(original)
            excluded = root / "node_modules" / "AGENTS.md"
            excluded.parent.mkdir()
            excluded.write_text("invalid")
            (root / "linked").symlink_to(excluded.parent, target_is_directory=True)
            self.assertEqual(discover([root, rule]), [rule])
            result, output, _ = self.run_cli(root, rule)
            self.assertEqual(result, 0)
            self.assertIn("1 file(s): 0 error(s), 1 warning(s)", output)
            self.assertIn(f"{rule}:1: warning W001:", output)
            self.assertEqual(rule.read_text(), original)
            self.assertEqual(self.run_cli(excluded)[0], 1)

    def test_exit_codes_distinguish_lint_and_scan_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.run_cli(root)[0], 2)
            self.assertEqual(self.run_cli(root / "missing.md")[0], 2)
            rule = root / "AGENTS.md"
            rule.write_text("## Action: Missing keyword\n\nDo this.")
            self.assertEqual(self.run_cli(rule)[0], 1)
            rule.write_text("## Context: A fact\n\nThis is intentional.")
            self.assertEqual(self.run_cli(rule)[0], 0)
            rule.write_bytes(b"\xff")
            result, _, errors = self.run_cli(rule)
            self.assertEqual(result, 2)
            self.assertIn("E_IO", errors)

    def test_lowercase_filename_is_discovered_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            rule = Path(directory) / "agents.md"
            rule.write_text("## Context: A fact\n\nThis is intentional.")
            result, output, _ = self.run_cli(rule.parent)
            self.assertEqual(result, 0)
            self.assertIn("warning W005", output)

    def test_rule_count_warns_only_above_ten_and_counts_legacy_and_duplicates(self):
        ten = "\n\n".join(f"## Context: Rule {i}\n\nA fact." for i in range(10))
        self.assertEqual(self.codes(ten), set())
        self.assertIn("W006", self.codes(ten + "\n\n## Context: Rule 0\n\nAnother fact."))
        self.assertIn("W006", self.codes(ten + "\n\n[always] Legacy rule\nDo this."))
        self.assertNotIn("W006", self.codes(ten + "\n\n## Invalid: Not a rule\n\nA fact."))
        example = "\n\n```md\n## Context: Example\n\nNot an instruction.\n```"
        self.assertNotIn("W006", self.codes(ten + example))

    def sized_rule(self, characters):
        prefix = "## Context: Size boundary\n\n"
        return prefix + "x" * (characters - len(prefix))

    def test_file_token_warning_includes_heading_at_exact_boundary(self):
        self.assertEqual(self.codes(self.sized_rule(4000)), set())
        self.assertEqual(self.codes(self.sized_rule(4001)), {"W007"})

    def test_chain_budget_deduplicates_aliases_and_stays_advisory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = []
            for index in range(5):
                path = root / str(index) / "AGENTS.md"
                path.parent.mkdir()
                path.write_text(self.sized_rule(4000))
                files.append(path)
            alias = root / "alias" / "AGENTS.md"
            alias.parent.mkdir()
            alias.symlink_to(files[0])
            result, output, _ = self.run_cli("--chain", *files, files[0], alias)
            self.assertEqual(result, 0)
            self.assertIn("5 distinct file(s), approximately 5000 tokens", output)
            self.assertNotIn("W008", output)
            files[-1].write_text(self.sized_rule(4001))
            result, output, _ = self.run_cli("--chain", *files)
            self.assertEqual(result, 0)
            self.assertIn("approximately 5001 tokens", output)
            self.assertIn("warning W008", output)
            self.assertIn("0 error(s), 2 warning(s)", output)
            self.assertNotIn("W008", self.run_cli(root)[1])
            self.assertEqual(files[-1].read_text(), self.sized_rule(4001))

    def test_chain_rejects_directory_and_reports_incomplete_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(SystemExit) as error:
                self.run_cli("--chain", root)
            self.assertEqual(error.exception.code, 2)
            bad = root / "AGENTS.md"
            bad.write_bytes(b"\xff")
            result, output, errors = self.run_cli("--chain", bad)
            self.assertEqual(result, 2)
            self.assertIn("Selected rule chain: incomplete", output)
            self.assertIn("E_IO", errors)
            self.assertNotIn("approximately", output)


if __name__ == "__main__":
    unittest.main()
