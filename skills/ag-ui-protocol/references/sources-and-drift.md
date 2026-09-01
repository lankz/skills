# Sources, coverage, and documentation drift

## Snapshot provenance

This skill was built from the full official corpus at [docs.ag-ui.com/llms-full.txt](https://docs.ag-ui.com/llms-full.txt), fetched on 2026-09-02:

- 15,103 lines
- 523,996 bytes
- SHA-256 `610c1ecf340561b5ce3ad71e9180d60ec5f4a8c5fa4bc08a55898cb1b350c04e`

The official repository was also inspected at commit [`32f838c3565bd6e3cc8baf970eb50e58eb44cc3b`](https://github.com/ag-ui-protocol/ag-ui/commit/32f838c3565bd6e3cc8baf970eb50e58eb44cc3b) on 2026-09-02, especially the TypeScript core schemas and community Ruby SDK.

The full corpus is not vendored into this skill. Curated references are cheaper to load, make conflicts visible, and avoid freezing duplicated upstream documentation. For a detail not covered here, search the live corpus or official repository.

The upstream repository, documentation, and hosted Ruby SDK are MIT-licensed. If a future change vendors the full corpus or substantial verbatim portions, include the applicable upstream copyright and permission notice, source URL, retrieval date, and pinned commit. This skill uses an original synthesis and source links instead.

## Corpus coverage

Every source page in the captured documentation corpus was considered. Content is routed as follows:

| Corpus area | Pages | Treatment |
| --- | --- | --- |
| Protocol stack and introduction | `/agentic-protocols`, `/introduction` | Boundary and product orientation distilled into `protocol-model.md` |
| Core concepts | `/concepts/agents`, `architecture`, `capabilities`, `events`, `interrupts`, `messages`, `metadata`, `middleware`, `reasoning`, `serialization`, `state`, `subagents`, `tools`, `generative-ui-specs` | Protocol semantics distributed across all curated references |
| Drafts | `/drafts/generative-ui`, `meta-events`, `overview` | Explicitly labeled draft in the extension/status guidance |
| Quickstarts | `/quickstart/applications`, `clients`, `introduction`, `middleware`, `server` | Used to understand integration/client/server roles; scaffolding not copied |
| JavaScript SDK | client agent, compaction, HTTP agent, middleware, overview, subscriber; core events/multimodal/types; encoder/proto | Used to verify schemas and separate SDK behavior from protocol behavior |
| Python SDK | core events/multimodal/types/overview and encoder | Used for cross-language checks; Python syntax and setup not copied |
| .NET SDK | abstractions, client, transport, endpoints, hosting, extensibility | Used for cross-language checks and to disprove JavaScript-only assumptions |
| Development/support/tutorials | contributing, roadmap, updates, support, production contact, Cursor, debugging | Status and troubleshooting context only; operational/community material not needed by the skill |

The upstream repository also contains Ruby SDK docs that were not present as separate pages in the captured documentation corpus. They are covered in `ruby-and-gateways.md` as an implementation snapshot, not protocol law.

## Known contradictions and stale statements

When these appear, follow the resolution column and verify the live target version.

| Upstream conflict | Safe resolution |
| --- | --- |
| Architecture/README says 16 event types; current source has many more | Never state a durable total; use the target schema |
| Some generated enum pages omit chunks or subagent events that their own prose describes | Prefer current typed source and explicit triads for portability |
| Concept prose says all agents extend `AbstractAgent` | Treat it as a JavaScript client abstraction, not a protocol requirement |
| Interrupts and reasoning appear in current concepts/SDKs but the draft index still lists them | Treat support as version-sensitive; verify both producer and consumer |
| Intro advertises scoped subagent state; subagent concept says one run-scoped state | There is no AG-UI per-subagent state; attribution is provenance |
| Intro advertises steering, cancellation, tool-output streaming, and conflict resolution without complete stable event contracts | Do not invent core events; require a concrete current schema or use a documented extension |
| Text start roles differ across concept and SDK pages | Use `assistant` for portable agent output unless the target schema verifies another role |
| Generic message uses `encryptedContent`; concrete schemas use `encryptedValue` | Use `encryptedValue` in current concrete shapes |
| Reasoning migration example starts a reasoning message with role `assistant` | Use required role `reasoning` |
| Serialization examples use `STATE_DELTA.patch` and `STATE_SNAPSHOT.state` | Current fields are `delta` and `snapshot` |
| Metadata whole-object `null` handling differs across pages | Never emit `metadata: null`; omit it |
| `MESSAGES_SNAPSHOT` is called fully complete but activity/reasoning have omission semantics | Apply the dedicated role-specific rule |
| Conceptual compaction collapses state/messages; JS `compactEvents` is narrower and can reorder interleavings | Keep raw audit history and verify the exact utility before relying on replay equivalence |
| Binary transport is marketed broadly but maps only a subset of events | Verify the selected event surface; prefer JSON for full fidelity |
| Privacy prose maps features to GDPR/SOC 2/HIPAA | Do not present protocol features as compliance guarantees |
| Ruby SDK README says 16 events and shows legacy binary multimodal input | Inspect the released code/schema; do not copy the README claim |

## Live authoritative entry points

- [AG-UI introduction](https://docs.ag-ui.com/introduction)
- [Architecture](https://docs.ag-ui.com/concepts/architecture)
- [Events](https://docs.ag-ui.com/concepts/events)
- [Messages](https://docs.ag-ui.com/concepts/messages)
- [Tools](https://docs.ag-ui.com/concepts/tools)
- [State](https://docs.ag-ui.com/concepts/state)
- [Metadata](https://docs.ag-ui.com/concepts/metadata)
- [Interrupts](https://docs.ag-ui.com/concepts/interrupts)
- [Subagents](https://docs.ag-ui.com/concepts/subagents)
- [Reasoning](https://docs.ag-ui.com/concepts/reasoning)
- [Serialization](https://docs.ag-ui.com/concepts/serialization)
- [Capabilities](https://docs.ag-ui.com/concepts/capabilities)
- [Generative UI relationship](https://docs.ag-ui.com/concepts/generative-ui-specs)
- [Draft index](https://docs.ag-ui.com/drafts/overview)
- [Official repository](https://github.com/ag-ui-protocol/ag-ui)
- [Documentation license](https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/LICENSE)

For exact implementation work, pin an SDK release or repository commit in the resulting design, test, or documentation. “Current AG-UI” is not a sufficient compatibility target.
