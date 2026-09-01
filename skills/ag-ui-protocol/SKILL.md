---
name: ag-ui-protocol
description: Apply AG-UI protocol concepts, vocabulary, and event semantics when designing, implementing, reviewing, or debugging agent-to-user event streams, agent loops, channel gateways, renderers, and transport adapters. Use for AG-UI runs, messages, tools, state, activity, reasoning, interrupts, subagents, metadata, capabilities, serialization, or partial conceptual alignment in Ruby or other stacks; do not assume full wire compliance or require a JavaScript client.
---

# AG-UI protocol

Use AG-UI as a semantic reference for the boundary between an agent runtime and a user-facing application. A user-facing application can be a web UI, mobile app, terminal, Slack, Teams, or another channel. AG-UI does not require React, CopilotKit, Assistant UI, RxJS, HTTP SSE, or any particular agent framework.

## Start with the adoption level

Name the level before recommending changes:

1. **Conceptual alignment** — reuse AG-UI vocabulary, identifiers, lifecycle patterns, and separation of concerns inside an existing system.
2. **Semantic compatibility** — maintain an internal event contract that can map to AG-UI without losing meaning, while retaining the existing transport and renderers.
3. **Wire compatibility** — accept the current `RunAgentInput` shape and emit events that validate against a specific AG-UI version and transport.

Similar names do not establish compatibility. Do not describe a system as AG-UI-compatible unless its input, event shapes, ordering, and selected transport have been verified against the target version.

For ordinary architecture work, prefer the smallest useful alignment. Do not introduce the Ruby AG-UI gem, Sorbet, an AG-UI endpoint, or a new frontend runtime unless the task specifically calls for it.

## Work from semantics outward

1. Identify the agent-to-user boundary. Keep provider callbacks, agent-loop semantics, delivery transport, and channel rendering as distinct concerns.
2. Model stable identities and lifecycles before payload details: thread, run, message, tool call, interrupt, and subagent invocation.
3. Normalize provider/framework output into explicit semantic events once. Let each gateway render or degrade that contract for its channel.
4. Preserve start/content/end, snapshot/delta, and terminal-run invariants even when a channel buffers or coalesces updates.
5. Define unknown-event, retry, disconnect, and unsupported-rendering behavior. Never let an approval or tool failure silently degrade into success.
6. Test the contract independently from transport delivery and channel presentation.

## Read only the references the task needs

- Read [references/protocol-model.md](references/protocol-model.md) for the protocol boundary, adoption levels, identifiers, run input, and source-of-truth rules.
- Read [references/events.md](references/events.md) when naming, producing, consuming, validating, or replaying events.
- Read [references/messages-tools-state.md](references/messages-tools-state.md) for message roles, multimodal input, tool ownership/results, state, activity, and capabilities.
- Read [references/interrupts-subagents.md](references/interrupts-subagents.md) for human-in-the-loop resume contracts, nested/concurrent work, and cross-run suspension.
- Read [references/metadata-transport-extensions.md](references/metadata-transport-extensions.md) for metadata, reasoning, serialization, middleware, transports, protobuf limitations, custom events, and generative UI.
- Read [references/ruby-and-gateways.md](references/ruby-and-gateways.md) when applying the model to a Ruby agent loop or multi-channel gateways without a full AG-UI implementation.
- Read [references/sources-and-drift.md](references/sources-and-drift.md) before exact wire work, SDK adoption, dependency changes, or any claim about what the current protocol supports.

## Non-negotiable distinctions

- AG-UI standardizes agent↔user-application interaction. MCP covers agent↔tools/context; A2A covers agent↔agent communication.
- Transport moves events; renderers present them. Action Cable, WebSockets, SSE, and channel APIs do not determine event meaning.
- `RunAgentInput.tools` contains client-provided tools for that run, not every backend tool.
- Tool proposal, approval, execution, and result are distinct facts. Filtering emitted tool events is not authorization and does not prevent upstream execution.
- State is run-scoped shared state. Subagent attribution records provenance, not ownership; AG-UI defines no per-subagent state.
- Visible reasoning should be a user-safe summary or progress signal. Never expose hidden chain-of-thought merely because the protocol has reasoning events.
- Drafts, product-roadmap language, SDK conveniences, and framework adapters are not protocol law.

## Exactness and freshness

The bundled references are a curated orientation derived from the full official documentation snapshot fetched on 2026-09-02. AG-UI is evolving and the snapshot contains contradictions. For version-sensitive work, inspect the current official concept page and the concrete schema/source for the target SDK, then state which version or commit the answer relies on. Prefer typed schemas over overview prose when they disagree.
