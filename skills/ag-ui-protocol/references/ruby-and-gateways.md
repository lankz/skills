# Applying AG-UI concepts to Ruby and multi-channel gateways

## Goal

Use AG-UI as a vocabulary and semantic design reference without assuming a full AG-UI endpoint, replacing an existing transport, or coupling the agent loop to one channel's rendering model.

Keep four boundaries explicit:

```text
provider/framework callbacks
  -> agent-loop semantic events
  -> channel gateway rendering policy
  -> transport/platform delivery
```

Normalize provider-specific callbacks at the first boundary. Do not make Slack, Teams, or web renderers interpret model-provider chunks independently.

## Ruby contract shape

Ruby identifiers can remain idiomatic internally and serialize only at an actual wire boundary:

```ruby
{
  type: :text_message_content,
  message_id: "msg-123",
  delta: "Hello",
  metadata: { trace_id: "trace-9" }
}
```

If wire compatibility is required, normalize and validate once, then serialize the equivalent `TEXT_MESSAGE_CONTENT` with camelCase fields. Do not spread casing conversion, dynamic probing, or provider reflection across renderers.

Prefer explicit value objects or discriminated hashes with required fields, owner IDs, and constructors/factories for valid events. Validate:

- known type/discriminator;
- required fields;
- legal start/content/end transitions;
- matching IDs and owners;
- one terminal run event;
- JSON-serializable metadata/state/custom payloads.

The internal event set can be a supported subset. Document the subset and explicit degradation rules instead of defining empty placeholders for every AG-UI event.

## Gateway rendering policy

Separate semantic preservation from visual parity:

| Semantic event | Rich web rendering | Slack/Teams-style fallback |
| --- | --- | --- |
| Run/step lifecycle | Loading and progress UI | Typing/status indicator or concise status update |
| Text deltas | Incremental message | Buffer/coalesce and post or edit at safe intervals |
| Tool proposal/result | Tool card and result component | Platform block/card or labeled text; preserve failures |
| Activity snapshot/delta | Structured live component | Brief status/card update or intentional suppression with diagnostics |
| Interrupt | Form/approval controls | Buttons/card/input flow; if unsupported, fail safely or cancel explicitly |
| Reasoning summary | Collapsible progress | Short working-status text, never hidden chain-of-thought |
| Subagent attribution | Grouped/nested timeline | Prefix, thread, status group, or flattened output with recorded provenance |
| Shared state | Update client-side UI model | Usually server-side only; never dump raw state into chat |
| Custom/raw | Registered renderer or diagnostic view | Known fallback; log/ignore unknown events without treating them as success |

A channel may coalesce delivery without erasing semantic IDs or terminal outcomes. For example, Slack need not receive every token delta, but the internal message should still have one start, ordered content, and one end.

## Approval and side effects

- Keep tool proposal, approval, execution, and result distinct.
- If a channel cannot render an approval schema, do not implicitly approve. Provide a safe fallback, mark it unsupported, or cancel.
- Authenticate and authorize at the executor. Renderer filtering is not a safety control.
- Make retries idempotent at the side-effect boundary and resume entries replay-safe.
- Preserve the original `toolCallId` across approval and execution.

## Incremental adoption

A low-risk sequence is:

1. Standardize identities and top-level run terminals.
2. Standardize text message and tool-call lifecycles.
3. Move provider translation ahead of the gateway renderers.
4. Add explicit activity/progress and error degradation policies.
5. Add snapshots/state only where a client actually consumes shared state.
6. Add interrupts or subagent attribution only when producers and all relevant consumers can support them.
7. Add a wire endpoint only if interoperability justifies it.

Each slice should be independently testable and need not commit the system to the next slice.

## Verification

Test at three levels:

1. **Semantic reducer tests** — given an event stream, reconstruct messages, tool calls, activity, and state with correct ordering and ownership.
2. **Gateway contract tests** — the same semantic stream produces an appropriate output or explicit degradation for every channel.
3. **Delivery tests** — retries, disconnects, rate limits, buffering, and platform edits do not invent or lose terminal meaning.

Include concurrent tool calls/messages, a provider error mid-stream, unknown custom events, tool failure, channel fallback, and an interrupted/resumed run when those features exist.

## Community Ruby SDK status

The official AG-UI monorepo contains an AG-UI-hosted community Ruby SDK and publishes the `ag-ui-protocol` gem. The inspected release was 0.2.0, dated 2026-05-26 and published 2026-05-27, MIT-licensed, Ruby 3.0+, with `json` and `sorbet-runtime` dependencies. It provides Sorbet-backed data models, snake_case Ruby constructors, camelCase JSON serialization, and SSE event encoding.

Treat it as an optional implementation reference, not this skill's dependency or the protocol source of truth. At the inspected 2026-09-02 main commit it lagged the reference TypeScript schema in material ways:

- no subagent lifecycle events or `subagentRunId` surface;
- no base event/message/tool-call metadata model;
- interrupt/resume fields were incomplete;
- no terminal token-usage surface;
- `RunFinished` rejected a `result` alongside an outcome although current reference semantics allow coexistence;
- the README still advertised 16 core events and legacy binary multimodal input;
- its encoder covered JSON SSE, not the full client/verifier/middleware surface.

Before adding or using the gem, compare its released version with the target protocol schema and list every unsupported event/field the application needs. Do not add Sorbet merely to imitate the community SDK.

Other independent Ruby projects provide fuller servers or transport-neutral adapters, but they are third-party implementations with their own captured schema versions and architecture choices. Use their boundary patterns only after verifying their source, license, and parity; do not encode them as AG-UI fundamentals.

Authoritative links:

- [Ruby SDK source](https://github.com/ag-ui-protocol/ag-ui/tree/main/sdks/community/ruby)
- [Ruby SDK docs](https://github.com/ag-ui-protocol/ag-ui/tree/main/docs/sdk/ruby)
- [`ag-ui-protocol` on RubyGems](https://rubygems.org/gems/ag-ui-protocol)
