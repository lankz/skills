# Interrupts and subagents

## Interrupts terminate a run

An interrupt is a terminal outcome for the current run. Resumption starts a new run:

```text
run 1: RUN_STARTED
       tool/message/state events
       required resume state and transcript snapshots
       RUN_FINISHED { outcome: { type: "interrupt", interrupts: [...] } }

input: same threadId, new runId, resume: [...]

run 2: RUN_STARTED
       continuation and any TOOL_CALL_RESULT against original IDs
       RUN_FINISHED or another interrupt/error
```

Framework checkpointing is an implementation optimization. Replay-style and checkpoint-style implementations should have the same observable protocol behavior.

## Interrupt shape

| Field | Meaning |
| --- | --- |
| `id` | Correlation, idempotency, and audit key |
| `reason` | Required routing category |
| `message` | Optional human-readable fallback prompt |
| `toolCallId` | Optional link to the proposed tool call; required by the core `tool_call` reason |
| `responseSchema` | Optional JSON Schema for the resume payload |
| `expiresAt` | Optional ISO-8601 expiry |
| `metadata` | Optional framework/application data |
| `subagentRunId` | Optional provenance for the subagent that raised it |

Core reasons are `tool_call`, `input_required`, and `confirmation`. Unknown strings are valid extensions. Namespace custom reasons as `<framework>:<name>` and reserve `core:`. Clients must render an unknown reason from its message/schema/metadata instead of failing.

## Resume entries

Each entry contains:

- `interruptId`
- status `resolved` or `cancelled`
- optional `payload`
- optional envelope `metadata`

`resolved` means the user answered. A denial is still resolved, for example `{ approved: false }`. `cancelled` means the user abandoned the request and should omit meaningful payload. Metadata can carry signatures or routing evidence; the answer itself belongs in `payload`.

### Contract rules

1. Resume on the same `threadId` with a new `runId`.
2. Every `interruptId` must belong to the interrupted run.
3. One resume array addresses every open interrupt; partial resume is unsupported.
4. Pending interrupts block unrelated new input on that thread.
5. Replaying the same `(threadId, interruptId, status, payload)` must be safe.
6. Clients should validate payload against `responseSchema` before submission; agents may validate it and emit `RUN_ERROR` on mismatch.
7. Reject expired, unknown, incomplete, or invalid resumes with `RUN_ERROR` rather than guessing.
8. Emit state/message snapshots needed for resume before the interrupting `RUN_FINISHED`.

### Tool-bound approval

The audit trail spans runs:

```text
original TOOL_CALL_ARGS -> resume decision/editedArgs -> TOOL_CALL_RESULT
```

Do not re-emit the original tool-call start/args/end after resume. Return the result against its original `toolCallId`. If approve-with-edits is supported, `editedArgs` is a full replacement, not a partial merge. Its presence in `responseSchema` is the direct client signal; a capability declaration is optional discovery.

Interrupt support remains version-sensitive despite its normative concept page and implementations. Verify the target producer and consumer schemas.

## Subagent scope

AG-UI subagent support provides lifecycle visibility and provenance. It does not schedule, orchestrate, cancel, or define child agents.

`subagentRunId` identifies one invocation. `name` identifies the reusable kind of subagent. Do not persist an invocation ID as a stable agent definition.

Most event families can carry optional subagent provenance. An untagged event belongs to the parent agent. Attribution without `SUBAGENT_STARTED`/`FINISHED` is valid, so consumers must accept unannounced IDs and fall back to displaying the ID when no name is known.

## Ownership and concurrency

- Track open text, reasoning, tool, and step streams per entity and owner. Several can be open simultaneously.
- A lifecycle start cannot duplicate an active invocation ID; lifecycle finish/error must name an active invocation. Attribution alone may name an unannounced or already-finished invocation.
- Continuation and end events must agree with the owner that opened the entity.
- An untagged tool call with `parentMessageId` inherits the assistant message's owner; an explicit conflicting owner is invalid.
- Tool results carry independent provenance because requester and executor can differ.
- `parentSubagentRunId` models nesting. A parent may finish before its child.
- A subagent finish closes only that subagent's open streams, not sibling or parent streams.
- Every started subagent closes before normal `RUN_FINISHED`. A failed top-level run may leave them open/aborted.
- Under concurrent chunk shorthand, repeat both entity ID and `subagentRunId`; never ask a client to guess which lane “the previous chunk” refers to.

State remains shared. Attribution on `STATE_SNAPSHOT` or `STATE_DELTA` says who produced the update, not who owns a separate document.

## Suspension across runs

Suspension is the exception to ordinary invocation-ID lifetime. A subagent waiting on an interrupt closes with:

```json
{ "type": "suspended", "interruptIds": ["..."] }
```

`interruptIds` names interrupts owned directly by that subagent and may be empty or omitted for an ancestor suspended by a descendant. If the producer can correlate resumed work, it should reuse the suspended `subagentRunId`; the client treats a later start as continuation, not a duplicate. A producer that cannot correlate may mint a new ID. The answered interrupt IDs still let the client resolve the old waiting state.

## Compatibility

Older clients may ignore an unknown `subagentRunId` field but reject unknown subagent lifecycle event types during decoding. Producer-side opt-in or capability/version gating is therefore safer than relying on client filtering. Attribution-only mode is a lower-risk intermediate step.
