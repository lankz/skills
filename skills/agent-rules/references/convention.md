# AGENTS.md Rule Convention

Use a small, explicit subset of Markdown for local working rules. Category identifies purpose; requirement language identifies strength. This is our authoring convention, not an ISO or RFC-defined AGENTS.md format.

## Structure

An AGENTS.md consists of rule blocks:

```md
## Category: Concrete title

One short paragraph describing the rule.
```

Use exactly `Context`, `Action`, `Dependency`, or `Check`, followed by a colon and a space. Start headings at the beginning of the line with `## ` and omit optional Markdown closing hashes. Separate the heading from the paragraph, and adjacent blocks, with a blank line. Hard-wrap paragraphs if useful; wrapped lines remain one paragraph.

Give every rule a distinct title within its file and one idea in one to four sentences. Include the trigger, affected code, and rationale when needed to prevent misunderstanding. Keep command names and paths in inline code. Keep detailed procedures, long examples, nested lists, and architecture documentation outside AGENTS.md and link to them from a relevant rule. Do not add document titles, free-standing introductions, or category section wrappers.

The heading syntax follows [CommonMark ATX headings](https://spec.commonmark.org/0.31.2/#atx-headings). The category vocabulary and single-paragraph restriction are local choices that make rule boundaries explicit for readers and future tooling.

Keep file density and inherited context small using the [advisory size guidance](maintenance.md#review-rule-density-and-inherited-size). Oversized files remain valid; preserving rule meaning and scope takes priority over clearing a size warning.

## Categories

| Category | Use for |
|---|---|
| Context | A local fact, constraint, or intentional exception needed to understand the work |
| Action | An instruction about what to do or avoid, including prerequisite reading |
| Dependency | Coordinated changes across code, contracts, data, or documentation |
| Check | Verification with a clear trigger and observable outcome |

Use Context for explanatory facts. If a fact also entails an instruction, give the instruction explicit requirement language; use Action, Dependency, or Check when that instruction is the main point. A category never makes a statement mandatory or optional by itself.

Order rules to suit the work: prerequisites before the actions they affect, and completion checks near the end. Do not create empty categories or require a rule of every category.

## Requirement language

Interpret uppercase requirement keywords using BCP 14, comprising [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html). Only their uppercase forms carry those special meanings; lowercase words retain ordinary English meanings.

| Preferred keyword | Meaning | Recognized equivalent |
|---|---|---|
| MUST | Mandatory requirement within its stated scope | REQUIRED, SHALL |
| MUST NOT | Prohibition within its stated scope | SHALL NOT |
| SHOULD | Recommended default; deviations need a reason and consideration of consequences | RECOMMENDED |
| SHOULD NOT | Discouraged behavior; exceptions need a reason and consideration of consequences | NOT RECOMMENDED |
| MAY | Permitted option | OPTIONAL |

For new rules, use the preferred keywords consistently. Action, Dependency, and Check bodies require at least one operative uppercase requirement keyword; merely mentioning a keyword does not establish an obligation. This explicitness is our convention, not a BCP 14 requirement: RFC 8174 recognizes that normative text can exist without these keywords. Context may be purely explanatory.

Distinguish MAY, which permits a choice, from a statement that something can or might happen. Avoid ambiguous phrases such as “MAY NOT”; use MUST NOT for a prohibition or describe uncertainty in ordinary language. SHOULD is a real default, not an invitation to ignore the rule. Requirement strength does not change an instruction's authority or scope, and capitalization is not an enforcement mechanism.

The skill defines this vocabulary once; do not repeat a full glossary in every AGENTS.md. If a repository needs a standalone adoption note, put a short Context rule in the applicable ancestor and refer to BCP 14.

## Examples

```md
## Context: Templates are shared

These templates are shared across projects. Project-specific settings live separately.

## Action: Preserve encrypted credentials

When adding credentials, agents MUST merge additions into the existing contents. They MUST NOT replace an encrypted credentials file wholesale, because unrelated keys must survive.

## Action: Prefer the existing command

New sync stages SHOULD extend the existing command, which already owns ordering and retries.

## Dependency: Coordinate serialized job contracts

Incompatible changes to serialized job arguments MUST include a compatible consumer rollout before producers enqueue the new format.

## Check: Verify token refresh locking

Changes to token refresh locking MUST pass the concurrency tests before completion.
```

## Scope and inheritance

Each file applies to its directory and descendants. Read ancestors and the local file together. Keep broad rules high in the tree and specific rules close to governed code. A deliberate, authorized exception must identify the broader rule and explain the narrower behavior; do not rely on a category or a deeper path to silently cancel it.

For evidence-based placement, moves, consolidation, and policy changes, read [maintenance guidance](maintenance.md).

## Migration from existing formats

Read and honor existing rules before migrating them. Preserve their meaning, requirement strength, conditions, rationale, and directory coverage. Mixed formats remain readable during incremental migration; write new or edited rules in the new format unless the repository explicitly requires another convention.

| Existing tag | Typical conversion |
|---|---|
| `[orient]` | Context for facts; Action for prerequisite reading or preparation |
| `[tether]` | Dependency with an explicit instruction about what to coordinate or assess |
| `[always]` | Action with MUST |
| `[never]` | Action with MUST NOT |
| `[prefer]` | Action with SHOULD |
| `[avoid]` | Action with SHOULD NOT |
| `[caveat]` | Context for intentional conditions; another category if it contains an instruction |
| `[verify]` | Check with explicit requirement strength |

The old convention treated always/never as mandatory and prefer/avoid as defaults; category conversion alone does not set the strength of the other types. Use the actual wording and applicable rules to establish it. Do not turn “may require a matching update” into a blanket MUST update: an obligation to assess the dependency may be the intended rule. If the force is materially ambiguous, resolve it before rewriting.

Older `## rule:` blocks were treated as mandatory rules, `## gotcha:` as caveats, and `## see also:` as orientation. Preserve those meanings rather than interpreting them as malformed new categories.

## Reviewing an edit

Run the [bundled linter](../scripts/lint_rules.py) after edits; [linting guidance](linting.md) describes its checks and limitations. Check operative requirement meaning, scope, paths, and links manually, and compare before and after meaning. Verify that moving or merging rules preserves intended coverage and does not create conflicting instructions. The linter checks structure and wording patterns, not policy correctness.

## Standards baseline

Requirement vocabulary follows RFC 2119 and RFC 8174 (BCP 14); heading syntax follows CommonMark 0.31.2, linked above. The categories, maintenance workflow, and size budgets are original conventions, not requirements of those standards. Examples describe hypothetical repositories.
