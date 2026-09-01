# Messages, tools, state, activity, and capabilities

## Messages

Every message has a unique `id`, a role, optional `metadata`, and optional subagent provenance where supported. Concrete roles are:

| Role | Content and fields | Direction/ownership |
| --- | --- | --- |
| `developer` | Required string, optional `name` | Instruction/history |
| `system` | Required string, optional `name` | Instruction/history |
| `user` | String or ordered multimodal parts, optional `name` | User to agent |
| `assistant` | Optional string, optional `name`, optional `toolCalls` | Agent to user/application |
| `tool` | String, `toolCallId`, optional `error`, optional `encryptedValue` | Result of an execution |
| `activity` | `activityType` plus structured object content | Frontend-only progress/UI state |
| `reasoning` | Visible string plus optional `encryptedValue` | User-safe reasoning signal and opaque continuity |

The generic `encryptedContent` shown in an older concept snippet is stale. Current concrete schemas use `encryptedValue` on reasoning messages, tool calls, tool messages, and some assistant-message implementations.

### Multimodal user input

User content can be plain text or an ordered array of:

- `{ type: "text", text }`
- `{ type: "image", source, metadata? }`
- `{ type: "audio", source, metadata? }`
- `{ type: "video", source, metadata? }`
- `{ type: "document", source, metadata? }`

A non-text `source` is either `{ type: "data", value, mimeType }` for inline data or `{ type: "url", value, mimeType? }`. The older generic `binary` shape is a compatibility path in some SDKs; do not use it for new portable contracts.

### Message reconstruction

- Append text/reasoning deltas in arrival order.
- Build assistant tool calls from start/args/end using the correlated ID.
- Tool-call arguments remain a JSON-encoded string in the durable `ToolCall.function.arguments` field.
- A tool result is a separate `tool` message linked by `toolCallId`.
- Activity messages never return to the agent in normal run input. Reasoning messages may return to preserve continuity.
- Preserve message and tool-call metadata when snapshotting or replaying.

## Tools

The tool declaration is a name, description, JSON Schema parameters, and, in current source, optional metadata.

Distinguish two tool sets:

- **Backend-defined tools** live in the agent/runtime and execute under backend authorization.
- **Client-provided tools** are supplied through `RunAgentInput.tools` for this run and let the agent request application/channel behavior.

The frontend does not become a security boundary merely because it supplied a schema. Authorize execution at the component that owns the side effect. An event filter can alter visibility but cannot stop an upstream runtime that already executed a tool.

Keep these facts separate:

1. the agent proposed a tool name and arguments;
2. a human or policy approved, rejected, cancelled, or edited the proposal;
3. an executor attempted the side effect;
4. a result or error was returned.

For failures, set `ToolMessage.error`; otherwise arbitrary failure-looking text is indistinguishable from successful content.

## State

Protocol state is arbitrary JSON with an application-defined schema. There is one run-scoped shared document:

- `STATE_SNAPSHOT.snapshot` replaces it completely.
- `STATE_DELTA.delta` applies ordered RFC 6902 JSON Patch operations.
- `RunAgentInput.state` supplies the current state at run start.

AG-UI does not define conflict resolution, locking, persistence, or access control. A particular SDK may apply patches atomically or immutably, but that is an implementation property. On divergence, recover from a fresh snapshot.

Design patch-friendly state, but do not use shared state as a dumping ground for transcript, secrets, or provider-native events. Treat state crossing into a user-facing client as discloseable unless a separate contract says otherwise.

## Activity versus other progress

Use the most specific concept:

| Need | Prefer |
| --- | --- |
| Coarse run or named phase status | Run/step lifecycle |
| Structured, updateable UI progress such as a plan or search | Activity snapshot/delta |
| Final or conversational prose | Text message |
| User-safe model reasoning summary | Reasoning message |
| Provider/framework diagnostics | Metadata or raw material |

Activity is useful for multi-channel systems even when only the web client has a rich renderer. Other gateways can produce a concise textual or status-card fallback while retaining the same `messageId` and `activityType` internally.

## Capabilities

The declaration categories and important questions are:

| Category | Examples |
| --- | --- |
| identity | name, type, description, version, provider, documentation URL |
| transport | streaming, WebSocket, binary HTTP, push notifications, resumability |
| tools | supported, backend-provided items, parallel calls, client-provided tools |
| output | structured output and MIME types |
| state | snapshots, deltas, memory, persistence across runs |
| multi-agent | delegation, handoffs, known subagent types |
| reasoning | supported, streaming, encrypted |
| multimodal | accepted input and produced output modalities |
| execution | code execution, sandboxing, iteration/time limits |
| human-in-the-loop | approvals, interventions, feedback, interrupts, approve-with-edits |
| custom | integration-specific declarations |

Capabilities are discovery only. Do not infer undeclared features, and do not use a capability claim as a replacement for runtime validation, authorization, or graceful error handling.
