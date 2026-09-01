# AG-UI event reference

This is a portable semantic reference, not a substitute for the target version's schema. The official TypeScript source inspected on 2026-09-02 declared 36 discriminators: 31 current and five deprecated `THINKING_*` events. Older documentation still says 16 and some generated SDK pages omit newer events. Avoid hard-coding a protocol-wide event count.

## Common fields

Every event has `type` and may have `timestamp`, `rawEvent`, and `metadata`. Most events within a run may also carry `subagentRunId`. Top-level run lifecycle events are not attributed; `MESSAGES_SNAPSHOT` carries provenance on each message instead.

`timestamp` is numeric in the core schema, but the documentation does not normatively state its unit. Choose and document a unit in non-wire internal contracts; for wire compatibility, match the target SDK.

## Lifecycle and progress

| Event | Fields beyond the base | Semantics |
| --- | --- | --- |
| `RUN_STARTED` | `threadId`, `runId`, `parentRunId?`, `input?` | First event of a run |
| `RUN_FINISHED` | `threadId`, `runId`, `result?`, `outcome?`, `usage?` | Successful or interrupted terminal event |
| `RUN_ERROR` | `message`, `code?`, `usage?` | Unrecoverable terminal event |
| `STEP_STARTED` | `stepName`, `subagentRunId?` | Opens an optional named progress step |
| `STEP_FINISHED` | `stepName`, `subagentRunId?` | Closes the matching step for the same owner |

`RUN_FINISHED.outcome` is omitted for legacy normal completion, `{ type: "success" }` for explicit success, or `{ type: "interrupt", interrupts: [...] }` for a human-input pause. `result` remains a root field. Current reference schemas permit `result` alongside an outcome, but some SDK versions do not; verify the target.

The current `RUN_ERROR` shape does not carry `threadId` or `runId`; correlate it through the active run/stream.

`usage` is an optional array of numeric token summaries by provider/model. Current fields include `inputTokens`, `outputTokens`, `totalTokens`, `reasoningTokens`, and `cachedInputTokens`. This surface is version-sensitive.

## Text messages

Canonical portable sequence:

```text
TEXT_MESSAGE_START(messageId, role, name?)
TEXT_MESSAGE_CONTENT(messageId, delta)*
TEXT_MESSAGE_END(messageId)
```

Concatenate deltas in arrival order. Older SDKs reject empty content deltas, so omit them. The current TypeScript schema accepts `developer`, `system`, `assistant`, or `user` on start and defaults to `assistant`; older concept and SDK pages disagree. Agent output should normally use `assistant` unless another role has been version-verified.

`TEXT_MESSAGE_CHUNK(messageId?, role?, name?, delta?)` is a convenience form expanded by some clients. The first chunk needs an ID; a switch of ID or stream completion synthesizes the end. Explicit start/content/end is more portable for storage, cross-language consumers, and concurrent streams.

## Tool calls

Canonical proposal sequence:

```text
TOOL_CALL_START(toolCallId, toolCallName, parentMessageId?)
TOOL_CALL_ARGS(toolCallId, delta)*
TOOL_CALL_END(toolCallId)
```

Argument deltas are fragments of a JSON string. Accumulate and parse only after the end event. `TOOL_CALL_END` means proposal/argument streaming finished; it does not mean that an external action succeeded.

`TOOL_CALL_RESULT(messageId, toolCallId, content, role?)` creates the correlated tool-result message. Tool execution failure is represented on a `ToolMessage.error` field in message history; the current result event itself does not define an `error` field.

`TOOL_CALL_CHUNK(toolCallId?, toolCallName?, parentMessageId?, delta?)` is another SDK convenience. Prefer explicit events where compatibility matters.

Tool events can interleave. Track each `toolCallId` independently. If a tool call names a parent message, its subagent owner must agree with or inherit from that assistant message.

## State and transcript

| Event | Fields | Apply rule |
| --- | --- | --- |
| `STATE_SNAPSHOT` | `snapshot`, `subagentRunId?` | Replace the one run-scoped state document |
| `STATE_DELTA` | `delta`, `subagentRunId?` | Apply RFC 6902 JSON Patch operations in order |
| `MESSAGES_SNAPSHOT` | `messages` | Synchronize message history; provenance is on messages |

If a `MESSAGES_SNAPSHOT` contains any activity messages, it is complete for the activity role; omitted prior activity messages are removed. The same rule applies independently to reasoning messages. If the snapshot contains none of a client-side role, it says nothing about that role and the client keeps its current entries.

State attribution is provenance only. A subagent-attributed snapshot still replaces the shared run state.

## Activity

| Event | Fields | Apply rule |
| --- | --- | --- |
| `ACTIVITY_SNAPSHOT` | `messageId`, `activityType`, `content`, `replace?`, `subagentRunId?` | Create/replace structured activity; `replace` defaults to true, false preserves an existing entry |
| `ACTIVITY_DELTA` | `messageId`, `activityType`, `patch`, `subagentRunId?` | Apply ordered RFC 6902 patches |

Activity and text messages share the same ID namespace. Never reuse an activity ID for a text message or vice versa.

## Reasoning

| Event | Fields | Semantics |
| --- | --- | --- |
| `REASONING_START` | `messageId`, `subagentRunId?` | Opens a reasoning phase; it does not create a message |
| `REASONING_MESSAGE_START` | `messageId`, role `reasoning`, `subagentRunId?` | Opens a visible reasoning/summary message |
| `REASONING_MESSAGE_CONTENT` | `messageId`, `delta`, `subagentRunId?` | Appends visible content |
| `REASONING_MESSAGE_END` | `messageId`, `subagentRunId?` | Closes the visible reasoning message |
| `REASONING_MESSAGE_CHUNK` | `messageId?`, `delta?`, `subagentRunId?` | SDK shorthand for the message triad |
| `REASONING_END` | `messageId`, `subagentRunId?` | Closes the reasoning phase |
| `REASONING_ENCRYPTED_VALUE` | `subtype`, `entityId`, `encryptedValue`, `subagentRunId?` | Attaches an opaque value to an existing message or tool call |

`subtype` is `message` or `tool-call`. Do not use the stale reasoning migration example that sets the message-start role to `assistant`; the current schema requires `reasoning`.

## Subagents

| Event | Fields | Semantics |
| --- | --- | --- |
| `SUBAGENT_STARTED` | `subagentRunId`, `name`, `description?`, `parentSubagentRunId?`, `parentToolCallId?`, `parentMessageId?` | Announces one nested invocation |
| `SUBAGENT_FINISHED` | `subagentRunId`, `result?`, `outcome?` | Closes it successfully or as suspended |
| `SUBAGENT_ERROR` | `subagentRunId`, `message`, `code?` | Closes it as failed |

See [interrupts-subagents.md](interrupts-subagents.md) for ownership, concurrency, and suspension rules.

## Special and deprecated events

`RAW(event, source?)` wraps a native external event. `rawEvent` on an otherwise standard event preserves its source material without creating a separate event. `CUSTOM(name, value)` defines application semantics not covered by the standard events. These are different mechanisms.

Five deprecated events remain in some SDKs for compatibility:

| Deprecated | Replacement |
| --- | --- |
| `THINKING_START` | `REASONING_START` |
| `THINKING_END` | `REASONING_END` |
| `THINKING_TEXT_MESSAGE_START` | `REASONING_MESSAGE_START` |
| `THINKING_TEXT_MESSAGE_CONTENT` | `REASONING_MESSAGE_CONTENT` |
| `THINKING_TEXT_MESSAGE_END` | `REASONING_MESSAGE_END` |

New work should use `REASONING_*`.

`META` is a draft proposal, not a current core event.

## Ordering and verification rules

- Process events in arrival order. Recovery may buffer or reject bad delivery, but string fragments and JSON Patch operations are not commutative.
- Correlate by IDs, not adjacency. Multiple streams may be open concurrently.
- A continuation/end event must agree with the owner that opened the entity.
- A snapshot replaces its target; a delta requires an agreed baseline.
- Every normal run begins with `RUN_STARTED` and ends with exactly one terminal event.
- Every started subagent closes before `RUN_FINISHED`; `RUN_ERROR` may abort open subagents.
- Unknown fields are often easier to tolerate than unknown event discriminators. Adding a new event type can break older clients before application code can filter it.
- Chunk shorthands are context-sensitive under concurrency. Repeat the entity ID and `subagentRunId` rather than relying on “the previous chunk.”
