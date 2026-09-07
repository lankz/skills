# Maintaining agent rules

Use this reference when the current work reveals a rule that should be added, clarified, relocated, consolidated, or retired. Keep the investigation proportional to the rule's scope. The SKILL.md conflict workflow governs user interaction; the [convention](convention.md) governs wording and format.

## Capture useful knowledge

A user saying “we always put form labels above the input” or “we never enqueue jobs directly” is a strong signal to suggest a rule. Use the instruction in the current task, then check whether it is already recorded and where it belongs. If the user specifically asks to record it, or has authorized ongoing policy edits, make the edit without asking again; otherwise present the proposal below.

Agent discoveries also merit suggestions: a verified ordering dependency, a non-obvious exception, or a reproducible failure with an established cause may prevent a costly future mistake. Explain the evidence and draft the smallest useful rule. One clear discovery can be enough; an unexplained failure or incidental workaround is not. Do not wait for a conflict or an explicit request to review AGENTS.md before noticing these opportunities.

Before adding a rule, identify the future mistake it prevents and search applicable rules for existing coverage. Record the smallest useful instruction, its trigger, and any essential rationale. Prefer updating an existing rule when the new information clarifies it. Do not preserve a debugging diary, temporary task status, generic advice, or implementation details that are already clear from the code. Follow the repository's documentation placement rules for longer explanations.

Keep suggestions selective. Favor explicit recurring user conventions and well-supported gotchas over speculative improvements. Present a concise proposal at a natural break, usually no more than one unsolicited suggestion at a time; batch closely related changes. A rules audit requested by the user can cover more. Do not interrupt each edit, create a separate proposal backlog, or repeat a declined or unanswered suggestion without new evidence. Optional rule proposals do not block the underlying task; raise a conflict promptly when it affects the current decision.

## Routine cleanup versus policy decisions

Using this skill includes a light maintenance sweep around touched code. Read relevant ancestors and descendants, notice misplaced rules, exact duplication, and stale references, and make verified corrections without seeking confirmation. Creating an AGENTS.md as the destination of an existing rule is routine relocation, not introducing a new policy. Removing a redundant copy is routine cleanup when the canonical rule still reaches all intended subjects.

Adding an obligation, changing its strength or intended subjects, and deleting a still-meaningful rule are policy changes. Use the proposal format when those changes have not already been authorized. An uncertain relocation also needs a scope decision; do not infer new policy merely to avoid asking. A necessary rule update that directly reflects an already-authorized policy or implementation change does not need another approval. Report routine maintenance briefly after making it, using source and destination paths for moves.

## Choose the right directory

Start with the rule's intended subjects and operations, not its current path or category. Search the repository for the relevant file types, callers, generators, or configuration using `rg --files`, globs, and targeted text searches. Include hidden, ignored, generated, or vendored locations only when they are relevant to the rule; distinguish files people edit from outputs they regenerate. Inspect applicable ancestor and descendant rules before deciding coverage.

| Finding | Maintenance action |
|---|---|
| A broad rule governs only one subtree | Move it down to that subtree's root |
| A rule governs sibling areas but exists in only one | Move shared guidance to their lowest common ancestor |
| Equivalent rules are repeated across siblings | Consolidate shared intent; preserve distinct local conditions |
| One rule mixes broad and local instructions | Split it into a shared rule and the smallest necessary local rule |
| A rule is in the correct ancestor but applies to only a file type or operation | State the trigger explicitly so unrelated work is not constrained |
| The correct directory has no AGENTS.md | Create it as part of the relocation; no separate confirmation is needed |

For each move, compare current directory coverage with intended coverage and proposed coverage. A move down may intentionally remove irrelevant readers; a move up may introduce new readers. Both require evidence that the instruction's explicit trigger reaches the intended work without spreading the policy farther. Do not call a relocation mechanical merely because the paragraph is unchanged.

Use one canonical rule where practical. An ancestor's applicable guidance is already inherited; copying it into descendants wastes context and permits drift. A child reference is useful only when it adds a local trigger or identifies a dependency that would otherwise be missed. Do not put a rule in the root just to make it more visible.

If the lowest common ancestor would include much unrelated code, keep the rule there with an explicit path, file-type, or operation condition when that gives the correct coverage. Split rules only when the obligations actually differ. Creating a higher AGENTS.md means a suitable directory within the repository; do not widen the task to parent repositories or user-wide instructions without authorization.

### Example: an ERB rule placed at the root

A rule requiring localized labels in application view templates currently lives at the repository root. Inspect ERB paths and their uses before moving it. If every intended template lives under `app/views`, create or use `app/views/AGENTS.md` and move the rule there. If relevant application templates also live under another subtree, `app/views` alone loses coverage: use the lowest shared ancestor with an explicit trigger or separate rules if the requirements differ. An ERB configuration file is not automatically subject to a rule about user-facing labels simply because its extension matches.

### Example: a rule placed too low

A transaction rule in `app/services/billing/AGENTS.md` also governs refund services in `app/services/refunds`. Check that the same contract applies to both. If it does, move the common obligation to `app/services/AGENTS.md`, creating that file if needed, and name the affected operations. Preserve any billing-only conditions locally instead of extending them to all services.

## Review rule density and inherited size

During authoring and audits, assess both individual files and the applicable chain. Use the skill's advisory size thresholds to flag review candidates, not failed policy. Estimate tokens as characters divided by four, including headings and whitespace; label the result approximate because language and code identifiers affect tokenization. For a target, combine applicable ancestor rules and any additional rule files their instructions require for that task, including transitive references, counting each file once. Check distinct affected branches separately; unrelated siblings are not one inherited chain. Skills, global instructions, and ordinary referenced documentation add further context beyond this repository-rule budget.

The 5,000-token chain budget is a maintenance heuristic: at roughly 100 tokens per rule across eight files it allows about six rules per file, or 0.5% of a hypothetical million-token context. Neither that depth nor that percentage is a measured universal optimum. Keep thresholds independent of model capacity and respect any smaller active instruction-loading limits.

Review oversized files for verbose wording, duplication, obsolete guidance, and genuinely narrower scope. Preserve useful safeguards and authorized exceptions. Do not combine unrelated obligations, create artificial directory splits, or remove valid rules just to clear a warning. Moving a rule down the same inherited chain does not reduce that chain's total; a scope change saves context only for work that no longer needs the rule. Explain justified excess briefly in the task report rather than adding waiver rules. Size findings alone do not authorize unrelated repository cleanup; follow the existing maintenance and policy workflow.

## Resolve discrepancies with evidence

| Observation | Response |
|---|---|
| The rule is current and the code violates it | Fix code within the task; otherwise surface the drift with locations |
| An authorized change makes the rule stale | Update the rule alongside the implementation and relevant documentation |
| Code and rule disagree, but neither is established as correct | Explain the evidence and ask for the policy decision; do not erase the rule to fit the code |
| A path or command changed | Verify the replacement and update the reference; do not guess a new check |
| A requirement appears obsolete | Verify whether governed behavior and consumers remain; propose removal unless retirement is already authorized |
| A local exception conflicts with an ancestor | Identify the ancestor and record the authorized boundary explicitly |

For lasting exceptions, make the broader rule's scope and the narrower instruction consistent. A short parent qualification and precise local rule can establish the boundary without copying the whole policy. Preserve mandatory protections outside the agreed exception. Context can explain the reason, but an explanation alone does not cancel an obligation.

## Consistent proposal format

Use this presentation whenever asking to add, change, or remove a rule. Keep the explanation short and show complete rule blocks so the decision is reviewable. Render file paths as clickable links to their absolute locations; identify a proposed new file as new.

````md
**Rule proposal — Add / Change / Remove: Rule title**

**File:** AGENTS.md path
**Why:** User statement or verified discovery, and the future mistake this prevents.

**Current:**
```md
Existing rule block, for Change or Remove only.
```

**Proposed:**
```md
Complete new rule block, for Add or Change only.
```

**Decision:** One concise question about the proposed edit.
````

Choose one operation in the heading. Omit Current for Add. For Remove, replace Proposed with “Remove this rule; no replacement,” or identify where equivalent guidance remains. Ask “Add this rule?”, “Replace the current rule with this?”, or “Remove this rule?” as appropriate. If a move needs a policy decision, present it as Change, show both paths, and ask the unresolved scope question. For a conflict, quote the existing rule under Current and use the decision question to distinguish a one-off exception from adopting the proposed policy. Continue already-authorized task work while that question is pending.

For example, after the user states the form-label convention and repository inspection establishes that the relevant templates are under `app/views`:

````md
**Rule proposal — Add: Position form labels above inputs**

**File:** app/views/AGENTS.md
**Why:** You said form labels always sit above inputs; recording this would keep future form changes consistent.

**Proposed:**
```md
## Action: Position form labels above inputs

Form field labels in these views MUST appear above their input controls.
```

**Decision:** Add this rule?
````

This is a presentation example, not an instruction to add a form-label rule to the current repository. Preserve the scope supported by the actual user statement and code; do not infer exceptions or apply one component's layout preference to every interface.

A qualified SHOULD deviation can be exercised within task judgment when its consequences are understood. Explain consequential departures; do not request approval for every default that has a legitimate exception. Ask about persistent policy only when the conversation or repeated work suggests the default itself may need revision.

## Complete the maintenance

Run the [linter](linting.md) on surviving changed rule files. Review the actual before and after rules, including those inherited at representative governed paths. For moves or splits, check at least one intended path in each affected subtree and a nearby excluded path where scope changed. Verify that obligations, exceptions, dependency guidance, and required checks remain reachable and consistent. Update references to moved rules and remove obsolete copies.

Keep the changed files readable in their existing transition state; do not turn a targeted correction into a full format migration. Report what policy or coverage changed, why, and what verification was performed. Batch unrelated findings into a concise recommendation for later work rather than silently expanding the task.
