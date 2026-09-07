---
name: agent-rules
description: 'Apply, lint, and maintain AGENTS.md working rules while editing code or discussing changes with the user. Use to check rule files, follow existing rules, suggest guidance from explicit user preferences or discovered gotchas, reconcile conflicts, and correct stale, duplicated, or misplaced rules.'
license: MIT
---

# Agent Rules

Maintain the rules as well as following them. An AGENTS.md records durable, local guidance an agent needs while changing the code. Keep it accurate, concise, and scoped to the directories it actually governs; put explanations of the system in documentation.

## Working loop

1. **Before acting:** read applicable AGENTS.md files from the repository root through each target directory, together with any instructions already supplied for the workspace. Identify relevant obligations, defaults, exceptions, dependencies, and checks. Revisit this when the task enters another directory or the user changes direction.
2. **While working and responding:** listen for explicit conventions such as “we always” and “we never,” and notice gotchas, hidden dependencies, and recurring mistakes in the code. Compare these with existing rules; suggest useful missing guidance even when nothing conflicts. Use the conflict workflow only for actual contradictions.
3. **Maintain where warranted:** make a light sweep of rules relevant to the touched files and their directory ancestry. Correct placement, duplication, and stale references autonomously when the intended policy is established. Use [maintenance guidance](references/maintenance.md) for the distinction between routine cleanup and policy proposals, and its consistent Add/Change/Remove presentation when a user decision is needed.
4. **Before finishing:** run the bundled linter after changing rule files, run other required checks, review affected rules for drift, and report material changes or unresolved decisions. Distinguish checks actually run from checks that remain unavailable.

Keep this loop local to the work. A newly encountered inconsistency justifies a targeted search; it does not automatically justify a repository-wide audit. Reuse rules already read unless their contents or applicable scope changes.

## Reading and applying rules

Each AGENTS.md applies to its directory and descendants. Combine ancestor and local instructions; sibling rules do not automatically apply across directories. A narrower file can clarify scope; contradictory rule files need reconciliation through an authorized exception or policy change. A direct user request can authorize a bounded action without using the word “exception”; separately establish whether the standing rule should change. A repository rule cannot elevate itself above higher-priority instructions by saying MUST.

Categories identify purpose; keywords identify strength. Interpret uppercase keywords using BCP 14: [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html). MUST is mandatory, MUST NOT prohibits, SHOULD and SHOULD NOT allow justified exceptions after considering consequences, and MAY permits an option. Lowercase words retain ordinary English meanings; do not dismiss a clear instruction merely because it lacks capitalization.

Read existing square-bracket rules and older heading blocks according to their established meanings. Legacy always/never rules are mandatory, prefer/avoid are defaults, and caveats protect intentional conditions. Do not treat an unfamiliar or older format as permission to ignore a rule. Use the migration table in [the convention](references/convention.md) when editing them.

## Conflicts with user requests

When a request appears to contradict a rule:

1. Establish whether it is a real conflict: check the file's scope, the rule's trigger, its strength, existing exceptions, and the conversation. A justified departure from SHOULD is different from changing a MUST. Consider whether the rule is simply stale.
2. Highlight the applicable rule by quoting the relevant wording and linking its exact AGENTS.md path. Explain the conflict and give a recommendation: retain the rule with a one-off exception, or change the policy. Ground the recommendation in the request and repository evidence.
3. If the user's intent about persistence is unresolved, ask whether this is a one-off exception or a lasting rule change. If they already specified either, act on that instruction without asking again. Do not turn a clear, authorized action into another approval gate; continue that work while clarifying any unresolved policy question. Pause only actions whose scope or authorization is actually unclear, and continue independent work.
4. For a one-off exception, follow the authorized request and leave the persistent rule intact. For a lasting policy change, update or remove the rule and reconcile affected ancestors, descendants, and references. Keep an agreed exception's scope explicit; do not generalize it to unrelated work.

A rule is evidence of the repository's intended policy, not a reason to silently refuse the user. Equally, one conflicting request or implementation is not proof that the persistent policy should be erased. If the user has not resolved persistence, do not silently convert the request into a lasting policy change.

## Active maintenance

Treat explicit user conventions and verified discoveries as candidates for persistent guidance. For example, “we always put form labels above inputs” should prompt a scoped rule suggestion when not already covered. Apply the user's instruction to the current work immediately; a statement of convention alone is a signal to suggest recording it, not an instruction to edit AGENTS.md. An explicit request to record or maintain policy, or standing authorization to do so, needs no further confirmation.

Suggest only durable, repository-specific guidance that is easy to miss and prevents a meaningful mistake. Check for existing coverage first. One verified, consequential gotcha can justify a suggestion; repetition is not required. Avoid turning temporary workarounds, unexplained failures, or a one-screen preference into general policy. Usually offer one concise, high-value suggestion at a natural pause or task completion, batch related candidates, and do not repeat declined or unanswered proposals without new evidence. Keep working while optional proposals are pending.

Continually reconsider placement when the work reveals new evidence: rules can sit too high, too low, or be duplicated across siblings. Determine which files and operations the rule is intended to govern, inspect their actual distribution, and choose the lowest common directory that covers them. Do not assume a file type lives in its conventional directory. A rule about ERB may belong in `app/views/AGENTS.md` only if that scope covers every intended template; inspect other ERB locations before moving it.

Routine maintenance is part of using this skill: do not ask for confirmation to move a rule up or down, create its destination AGENTS.md, remove a redundant copy, or repair a verified reference when evidence establishes the intended policy and scope. Check that placement fixes preserve or restore coverage of the intended subjects. If the intended scope is unclear, or adding, changing, or removing a rule would establish new policy, use the proposal format unless that change is already authorized. Prepare exact wording and paths before asking; do not request abstract permission to investigate.

## Authoring

Read [the convention](references/convention.md) before writing or migrating rules. The format is:

```md
## Action: Preserve the token refresh lock

Token refresh MUST use the locking mechanism in this directory. Bypassing it can invalidate stored credentials when refreshes overlap.
```

Use `## Category: Title`, a blank line, and one short paragraph. The categories are **Context** for explanatory constraints, **Action** for behavior, **Dependency** for coordinated changes, and **Check** for verification. Action, Dependency, and Check paragraphs use explicit uppercase requirement language. Keep one idea per rule, with a clear scope or trigger and only the rationale needed to avoid a mistake.

## Linting and verification

Aim for 5–8 rules per AGENTS.md; fewer is fine. Flag files with more than 10 rules or approximately 1,000 tokens, and applicable rule chains above approximately 5,000 tokens. These are advisory review thresholds, not validity limits or permission to discard safeguards. Include ancestors and explicitly required rule files once each; see [size review guidance](references/maintenance.md#review-rule-density-and-inherited-size) and the linter's explicit `--chain` check.

After creating, editing, or moving AGENTS.md rules, run [scripts/lint_rules.py](scripts/lint_rules.py) with Python 3 on every surviving changed file, including move destinations and sources that still exist. Resolve the script relative to this skill's installed directory, not the repository being checked. On a request to lint or check a codebase's rule files, run it on the requested directory first, then review semantic concerns separately. See [linting usage and diagnostics](references/linting.md).

Fix errors introduced by the task, assess warnings, and rerun after corrections. Do not blindly capitalize words or migrate unrelated legacy rules to silence diagnostics. A warning-only exit does not mean no attention is needed. If a required run fails or remains unavailable, report it; do not claim a clean check. For deleted files, verify remaining coverage and references rather than passing nonexistent paths to the linter.

The script is read-only. Review scope, conflicts, requirement meaning, exceptions, and paths manually even when lint passes. Lint findings identify candidates for maintenance; use the existing proposal workflow when fixing them would change policy.
