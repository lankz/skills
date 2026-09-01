# Metadata, reasoning, transport, serialization, and extensions

## Metadata

Metadata is the sanctioned extension point on events, messages, tool calls, and resume entries.

- It is an open JSON object. Values under keys may be `null`; the object itself should be omitted rather than emitted as `null`.
- `ag-ui` is reserved for protocol use.
- When events build a message, metadata merges shallowly by key with last write winning.
- Arrays and objects under one key are replaced whole, never recursively blended.
- Tool start/args/end metadata accumulates on that tool call, not its parent assistant message.
- Tool-result event metadata accumulates on the resulting tool message.
- Run, step, state, raw, custom, reasoning-phase, and encrypted-value event metadata remains event-level.
- `MESSAGES_SNAPSHOT` event metadata does not spread to enclosed messages.
- Resume-entry metadata is an input envelope and has no merge behavior.

Use metadata for extra attributes on a known semantic entity. Do not create undeclared top-level fields and hope every consumer preserves them.

## Reasoning and privacy

Reasoning events can carry a visible user-safe summary and opaque encrypted values for provider continuity. The protocol does not define encryption, key management, retention, erasure, or regulatory compliance.

- Never expose raw hidden chain-of-thought by default.
- Treat `encryptedValue` as opaque; clients store/forward but do not decrypt it.
- Attach an encrypted value only to an entity that already exists.
- Keep final assistant output separate from reasoning/progress content.
- Treat privacy/compliance examples in the upstream docs as illustrations, not certifications.

## Transport

The widest documented wire path is:

```text
HTTP POST body: RunAgentInput
response: text/event-stream
frame: data: {JSON event}\n\n
```

AG-UI semantics are transport-agnostic. A WebSocket or Action Cable stream can carry an AG-UI-aligned event contract without being compatible with the standard `HttpAgent`. State which claim applies.

SDK cancellation such as `abortRun()` is transport/execution control, not an AG-UI interrupt. Likewise, the `transport.resumable` capability mentions sequence-number stream resumption but the captured documentation corpus defines no universal sequence field or handshake; do not invent one.

### Protobuf limitations

Do not treat the binary transport as a complete replacement for JSON:

- At the pinned source, the protobuf `EventType` enum maps only 19 of 36 discriminators. It does include all three subagent lifecycle events and `subagentRunId` on mapped attributable events, including state events.
- Missing or inconsistent mappings include tool results, activity, reasoning, deprecated thinking, and chunk shorthands depending on version.
- The pinned proto declares text/tool chunk messages but has no matching enum discriminators, so those definitions are not usable event selections.
- Dynamic numbers use IEEE-754 doubles, so integers beyond 2^53 lose precision.
- Protobuf map byte ordering is not canonical.

Subagent-attributed state over protobuf is therefore representable in that version, but attribution is still provenance over one shared run state, never per-subagent ownership. Verify the exact target version and event set before selecting binary transport. Prefer JSON for archival fidelity.

## Serialization and lineage

An append-only event log supports restoration, debugging, and branches. `parentRunId` creates git-like lineage within a thread. Persist metadata and enough `RunStarted.input` to understand the run.

Keep raw history as audit truth and any compacted representation as a derived cache. Compaction is not automatically semantics-preserving:

- string and argument deltas must retain order;
- state/activity patches require their baseline;
- interleaved streams may be reordered by an SDK utility;
- a snapshot moved across an open stream can overwrite reconstructed output;
- the conceptual compaction page promises broader state/message reduction than the documented JavaScript utility performs.

Do not claim deterministic replay until ordering, snapshots, open-stream handling, and versioned reducers are specified and tested.

## Middleware and normalization

Two uses of “middleware” occur upstream:

1. integration middleware that translates a provider/framework stream into AG-UI semantics;
2. JavaScript client middleware implemented as an RxJS chain around `runAgent()`.

The first is a portable architecture pattern. The second is SDK-specific.

Useful generic normalization responsibilities include:

- translate provider-native callbacks once;
- validate fields, IDs, and event ordering;
- add metadata and tracing;
- map terminal errors;
- preserve native data in `rawEvent` or `RAW`;
- collect metrics without changing semantic ownership;
- apply display filtering only after authorization/execution decisions.

## Extension order

Prefer the narrowest extension mechanism:

1. `metadata` for extra attributes on an existing entity;
2. `CUSTOM(name, value)` for an application-defined semantic event;
3. `rawEvent` on a translated event or `RAW(event, source)` for native/provider material;
4. a namespaced interrupt reason;
5. capability `custom` declarations;
6. an external generative-UI payload transported through a tool or custom event;
7. a draft feature only when intentionally experimenting with that proposal.

Unknown fields and unknown event types have different compatibility profiles. Older decoders often tolerate the former and fail on the latter.

## Generative UI and draft material

AG-UI is not a generative-UI language. It can transport or coordinate A2UI, Open JSON UI, MCP Apps/UI, or an application-specific schema. It does not choose React components, iframes, or a renderer.

The upstream `generateUserInterface` two-step design and `META` annotations are drafts. Do not present them as current core events. Product-introduction references to steering, conflict resolution, tool-output streaming, or “today & upcoming” features also require a concrete schema before implementation.
