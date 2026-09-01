# AG-UI protocol model

## Boundary

AG-UI is the semantic boundary where an agent runtime meets a user-facing application:

```text
user-facing application -> RunAgentInput -> agent runtime
user-facing application <- ordered BaseEvent stream <- agent runtime
```

The application may be a web UI, mobile app, terminal, Slack, Teams, or another messaging surface. The protocol standardizes what is happening and why; a transport such as SSE, WebSocket, Action Cable, webhook delivery, or an in-process stream moves the data.

AG-UI does not specify model inference, agent orchestration, backend tool execution, channel APIs, or component rendering. `AbstractAgent`, `HttpAgent`, RxJS observables, CopilotKit hooks, and framework middleware are SDK or integration choices rather than universal requirements.

AG-UI complements other agent protocols:

| Boundary | Protocol | Responsibility |
| --- | --- | --- |
| Agent ↔ user-facing application | AG-UI | Runs, messages, events, shared state, UI-facing tool calls, and human interaction |
| Agent ↔ tools and context | MCP | Tool and data access |
| Agent ↔ agent | A2A | Distributed agent coordination |

## Adoption levels

### Conceptual alignment

Use the names and lifecycle patterns that improve an internal contract. Existing transports and channel payloads can remain unchanged. This is often sufficient for a Ruby agent loop with several renderers.

### Semantic compatibility

Make the internal contract losslessly mappable to AG-UI. Preserve correlation IDs, event ordering, terminal outcomes, state semantics, tool results, and unsupported-feature behavior. The wire representation can still differ.

### Wire compatibility

Implement a versioned endpoint/input and event stream. Validate exact camelCase fields, discriminators, optional/null behavior, ordering, media type, and the selected transport against the target SDK schemas. Test with an independent consumer.

## Identities

| Identity | Meaning | Common mistake |
| --- | --- | --- |
| `threadId` | Conversation/session continuity across runs | Treating it as one HTTP request or one channel delivery |
| `runId` | One top-level agent execution | Reusing it for later resumes or retries that are new runs |
| `parentRunId` | Run-lineage pointer for branching/time travel inside a thread | Assuming it is the interrupt being resumed or always the immediately previous run |
| `messageId` | One durable conversation or activity entity | Reusing it for different message shapes |
| `toolCallId` | One proposed tool invocation and its result | Minting a new ID after approval instead of correlating the original proposal |
| `interruptId` | One open human-input requirement | Using tool-call or run IDs as an implicit substitute |
| `subagentRunId` | One invocation of a nested agent | Treating it as a reusable subagent definition or name |

IDs are opaque strings. Correlate by ID, not by event adjacency. Concurrent messages, tool calls, steps, and subagents can interleave.

## `RunAgentInput`

The current cross-SDK model is:

| Field | Required | Meaning |
| --- | --- | --- |
| `threadId` | Yes | Conversation identity |
| `runId` | Yes | Current invocation identity |
| `parentRunId` | No | Lineage/branch pointer |
| `state` | No | Arbitrary current shared state; absent means no state and a bare `null` is read as absent |
| `messages` | Yes | Conversation/history messages |
| `tools` | Yes | Client-provided tools available for this run |
| `context` | Yes | `{ description, value }` context entries |
| `forwardedProps` | Yes in the core schema | Opaque integration/application properties |
| `resume` | No | Per-interrupt responses for an interrupted prior run |

Use separate fields for transcript, state, context, tools, and forwarded integration data. The protocol does not define a safe schema for `forwardedProps`; validate and authorize it at the application boundary.

`RunStarted.input` can record the input for serialization and debugging, but compacted history may omit messages already represented earlier in the event log.

## Run lifecycle

A normal run has one first event and one terminal event:

```text
RUN_STARTED
  zero or more message/tool/state/activity/step/reasoning/subagent events
RUN_FINISHED or RUN_ERROR
```

`STEP_STARTED`/`STEP_FINISHED` are optional progress boundaries. A `RUN_FINISHED` interrupt outcome terminates the current run; resumption is a new run on the same thread, not a paused stream that remains open.

Do not emit ordinary run events after a terminal event. On an aborted stream or `RUN_ERROR`, consumers may need to mark open entities as aborted rather than inventing their missing end events.

## Capability discovery

Capabilities are an optional, dynamic declaration model, not negotiation. Omitted means unknown rather than unsupported. Categories are:

- identity
- transport
- tools
- output
- state
- multi-agent
- reasoning
- multimodal
- execution
- human-in-the-loop
- custom

The documentation defines SDK methods such as `getCapabilities()`, but not a universal network discovery endpoint. Do not claim remote capability discovery unless the implementation exposes one.

## Source precedence

For exact questions, use this order:

1. The concrete typed schema/source for the target version and language.
2. Dedicated current concept pages for semantics.
3. SDK reference pages for language-specific behavior.
4. Quickstarts as examples only.
5. Introduction, roadmap, and marketing-oriented feature lists as orientation only.
6. `/drafts/*` only as explicitly labeled proposals.

See [sources-and-drift.md](sources-and-drift.md) for known contradictions and snapshot provenance.
