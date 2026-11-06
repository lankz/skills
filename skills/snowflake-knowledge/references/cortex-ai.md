# Cortex AI, documents, vectors, and semantic services

Use this reference when AI models, files, vectors, semantic views, Analyst, or Agents are involved. Cortex names, models, privileges, regions, return envelopes, and lifecycle states change quickly; resolve them from the live [Cortex documentation index](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llms.txt).

## Choose the surface before choosing syntax

| Need | Surface | Key contract |
|---|---|---|
| Set-based/batch AI over table rows | Cortex AI SQL functions | SQL execution plus per-token/page charges |
| Interactive streaming inference or tool calling | Cortex REST inference | REST/client contract, default-role behavior, model/region controls |
| Managed hybrid retrieval | Cortex Search | Materialized source, index/embedding refresh, separate serving state |
| Governed business semantics and SQL generation | Semantic view + Cortex Analyst | Semantic object; generated SQL is executed separately |
| Managed orchestration across Analyst, Search, procedures, MCP, and code | Cortex Agents | Agent object, threads/runs, default role, per-tool privileges |
| Traditional forecasting/anomaly/classification | Snowflake ML Functions | SQL class/instance lifecycle, not LLM inference |
| Custom training and MLOps | Snowflake ML | Versioned Snowpark ML APIs, feature store/model registry |

Do not force every AI use case through `AI_COMPLETE`. Prefer a task-specific `AI_*` function for fixed classification, filtering, translation, extraction, sentiment, aggregation, or embedding; use REST/Agents when interaction, tools, streaming, or server-managed conversation state is the real requirement. [AI functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql), [Cortex REST](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api), [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)

## Use current names, models, and availability

- For new SQL, use the canonical `AI_*` family. Older `SNOWFLAKE.CORTEX.COMPLETE`, `TRY_COMPLETE`, `CLASSIFY_TEXT`, `EMBED_TEXT_*`, `PARSE_DOCUMENT`, and similar namespace-era functions are compatibility surfaces on a deprecation path. Do not teach both families as equivalent choices.
- Never hard-code a model from memory. Models differ by function/surface, cloud and region, routing policy, context window, modality, price, lifecycle, and preview state. Inspect current regional availability and, when possible, `SHOW CORTEX BASE MODELS` including lifecycle/legacy/EOL fields. [Models and regional availability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-regional-availability)
- Preview models/features can change or disappear faster than GA contracts. Treat model output shape and model behavior as versioned external dependencies; evaluate migrations rather than silently accepting a replacement.
- Cross-region inference is a governance and latency choice, not a transparent fallback. Prompt/response data is processed transiently in another region, routing can cross clouds, and only authorized account administration should change the routing parameter. [Cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference)
- Self-service trial and other account types can restrict Cortex availability. Diagnose account capability and payment/enablement state before renaming a documented function.

## Authorization has independent gates

A valid call can require all of these:

1. Account-level `USE AI FUNCTIONS` or a per-function `USE AI FUNCTION <name>` privilege.
2. `SNOWFLAKE.CORTEX_USER` or a narrower applicable Snowflake database role.
3. Model RBAC/application-role access (or a still-applicable legacy allowlist during migration).
4. Model/function availability in the account region or permitted cross-region route.
5. `USAGE`, `SELECT`, stage/file, warehouse, service, semantic-view, or tool privileges.

The blanket and per-function account privileges are alternative authorization paths: revoking one per-function privilege does not block it while blanket `USE AI FUNCTIONS` remains. Snowflake database roles must be granted into an account role before a user can exercise them. [AI privileges and model access](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-privileges-and-access)

Audit inherited defaults before adding or declaring restrictions. Common accounts expose three independent paths that must be evaluated separately: blanket `USE AI FUNCTIONS` granted to account role `PUBLIC`; `SNOWFLAKE.CORTEX_USER` granted to `PUBLIC`; and the `SNOWFLAKE.PUBLIC` application-role model bootstrap. Restrict them with their distinct current privilege/database-role revokes and `SNOWFLAKE.LOCAL.REVOKE_FROM_PUBLIC_APPLICATION_ROLE` procedure as applicable. Revoking generic `IMPORTED PRIVILEGES` from `PUBLIC` is a separate, broad option that can also remove unrelated shared-database access such as `ACCOUNT_USAGE`; do not use it as a substitute.

Model RBAC is replacing the legacy model allowlist. Distinguish the `SNOWFLAKE.PUBLIC` application role used for model access from the account role `PUBLIC`; follow the current migration/revocation procedure rather than guessing a `REVOKE` statement.

## AI SQL execution and errors

- AI SQL calls consume warehouse compute as well as model token/page charges. Increasing a warehouse beyond the documented recommendation does not make remote model inference faster. Size the warehouse for feeding/collecting rows, and size model concurrency through the supported service controls. [AI function costs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-cost)
- Most canonical scalar AI functions now use row-level tolerant behavior: an invalid row can return `NULL` while other rows complete. During development or auditable pipelines, request `return_error_details => TRUE` where supported and inspect the `{value,error}` envelope; use `AI_THROW_IF_ERROR` for intentional fail-fast behavior. Aggregates, embeddings, extraction, and legacy functions have separate contracts. [Multirow error handling](https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_02/bcr-2184)
- Test null input, oversized input, unsupported language/modality, unavailable model, content filtering, rate limiting, and partial-row failure. A query completing is not proof that every AI row succeeded.
- `AI_COUNT_TOKENS` estimates supported input tokens, not total billable tokens. Managed prompts, structured-output scaffolding, guardrails, generated output, and unsupported/legacy/fine-tuned models can make billed tokens differ. [AI_COUNT_TOKENS](https://docs.snowflake.com/en/sql-reference/functions/ai_count_tokens)

## `AI_COMPLETE` and structured output

- Use the single-string form for ordinary text generation and supported structured output. The prompt-object/multimodal form has a different signature and does not accept `response_format`. [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete)
- Structured output supports only a documented JSON Schema subset or a supported SQL `TYPE OBJECT(...)` shape. A SQL type response must have `OBJECT` at the top; do not assume `VARIANT`, `MAP`, datetime, or every JSON Schema keyword is accepted.
- For OpenAI-family models, object schemas require `additionalProperties: false` and every property in `required`. Property names and schema complexity have Snowflake-specific limits, and the schema contributes to tokens. [Structured outputs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/complete-structured-outputs)
- `show_details => TRUE` changes the return envelope and adds model/usage details. `guardrails => TRUE` invokes Cortex Guard and adds cost; it is distinct from account-level guardrail controls for Agents/other products.
- `AI_COMPLETE` is stateless. Carry conversation history explicitly, or use Agent threads when the service must own state.

## Prefer specialized functions when they fit

- `AI_AGG(expression, instruction)` and `AI_SUMMARIZE_AGG(expression)` are aggregate functions that work with `GROUP BY` and can process datasets beyond one model context. Do not concatenate a large group into one prompt as a substitute. [AI_AGG](https://docs.snowflake.com/en/sql-reference/functions/ai_agg), [AI_SUMMARIZE_AGG](https://docs.snowflake.com/en/sql-reference/functions/ai_summarize_agg)
- `AI_CLASSIFY` uses case-sensitive categories and benefits from descriptions/examples, but every example/prompt token is charged for every input row. Large category sets reduce quality; document classification has its own restrictions. [AI_CLASSIFY](https://docs.snowflake.com/en/sql-reference/functions/ai_classify)
- `AI_FILTER` returns SQL `BOOLEAN` and can participate in `SELECT`, `WHERE`, or join predicates. Treat automatic optimization as opportunistic, not guaranteed, and handle null input deliberately. [AI_FILTER](https://docs.snowflake.com/en/sql-reference/functions/ai_filter)
- `AI_SENTIMENT` returns an object, not a scalar score, with an overall label and optional aspect results. [AI_SENTIMENT](https://docs.snowflake.com/en/sql-reference/functions/ai_sentiment)
- `AI_TRANSLATE` supports source auto-detection with an empty source-language argument in its documented form. Check current supported languages and input limits. [AI_TRANSLATE](https://docs.snowflake.com/en/sql-reference/functions/ai_translate)
- Specialized functions contain managed prompts, so raw input length alone underestimates cost.

## Embeddings and native `VECTOR`

- `AI_EMBED` returns a native `VECTOR`; model and modality determine element type and dimension. `AI_MULTI_EMBED` returns an object containing arrays/metadata that may need an explicit cast before vector functions. `AI_SIMILARITY` embeds internally and returns cosine similarity, with documented modality restrictions. [Vector embeddings](https://docs.snowflake.com/en/user-guide/snowflake-cortex/vector-embeddings)
- Embeddings are compatible only when produced in the same vector space/model contract. Equal dimensions do not make vectors comparable.
- Native syntax is `VECTOR(INT|FLOAT, dimension)` with a current maximum dimension of 4096. Here `INT` and `FLOAT` are vector element types (32-bit), not the ordinary SQL aliases' storage semantics. [VECTOR type](https://docs.snowflake.com/en/sql-reference/data-types-vector)
- Ordinary vector ordering/comparison is byte-wise lexicographic, not similarity. Use `VECTOR_COSINE_SIMILARITY`, `VECTOR_INNER_PRODUCT`, `VECTOR_L1_DISTANCE`, or `VECTOR_L2_DISTANCE` with equal element type and dimension. [Vector functions](https://docs.snowflake.com/en/sql-reference/functions-vector)
- `VECTOR` has important exclusions: it cannot be nested in `VARIANT`, used as a clustering key, server-side bound like an ordinary scalar, directly loaded/unloaded, or used by every Snowflake table/pipeline feature. Current docs exclude combinations including Snowpipe, Iceberg, Snowflake Scripting, and Search Optimization. Stage as arrays and cast when necessary.

## Files and document intelligence

Do not assume every AI function accepts the same `FILE` source, stage kind, quoted stage name, encryption mode, or file size. Validate the exact function's stage/encryption matrix and use scoped file URLs where the interface requires them.

### `AI_PARSE_DOCUMENT`

- This is parsing/OCR/layout, not schema extraction. `OCR` returns text; `LAYOUT` preserves structural content and is required for embedded-image extraction. [AI_PARSE_DOCUMENT](https://docs.snowflake.com/en/sql-reference/functions/ai_parse_document)
- The default result is a JSON-formatted string. Use `PARSE_JSON` before SQL traversal. `page_split` changes the result from a single `content` field to `pages[]`; page indexes are zero-based. `page_filter` uses start-inclusive/end-exclusive ranges and implies page splitting.
- Limits and billing are page/file-format dependent. Check the live [parse-document guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/parse-document) instead of copying limits into application assumptions.

### `AI_EXTRACT`

- This is question/schema-driven extraction from text or files. Its schema dialect is narrower than `AI_COMPLETE` structured output: top-level object, supported string/list/table extraction shapes, and table-specific ordering requirements. [AI_EXTRACT](https://docs.snowflake.com/en/sql-reference/functions/ai_extract)
- Page, entity-question, and table-question limits interact; OCR scale can improve difficult documents while increasing tokens and reducing effective page capacity. Split workloads intentionally and retain source/page provenance.

## Semantic views

A semantic view is a governed schema object, not an ordinary relational view and not merely a YAML prompt. It models logical tables, facts, dimensions, metrics, relationships, synonyms, instructions, and verified queries. Native semantic views are the preferred current contract; stage-based semantic-model YAML remains a compatibility surface. [Semantic view overview](https://docs.snowflake.com/en/user-guide/views-semantic/overview)

- Querying requires `SELECT` on the semantic view rather than its base tables. Metrics in SQL use the documented `AGG(metric)` semantics or the `SEMANTIC_VIEW(...)` construct. [Querying semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/querying)
- Define every relationship Agents/Analyst may use; they do not invent joins. Model many-to-many relationships through an appropriate bridge/shared dimension because direct many-to-many relationships are unsupported.
- Verified queries must use logical names. Use them to reinforce a sound semantic model, not conceal missing relationships or incorrect metric definitions. [Modeling guidance](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-modeling)

## Cortex Analyst and Agents

### Analyst

- Analyst returns SQL, text, suggestions, and warnings; the caller executes returned SQL separately on warehouse compute. It does not remember prior result rows, and multi-turn requests resend history and add cost. [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- The service chooses its model path. Region, model RBAC, and cross-region policy can change behavior. Snowflake currently recommends Cortex Agents for new orchestrated experiences that include Analyst capabilities.

### Agents

- An Agent is a schema object with model/orchestration configuration and tools. Threads hold conversation state; runs execute requests. `USAGE` on the Agent does not grant access to its tools. [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- Agent REST requests use the user's default role/warehouse when request context is absent. Supported Snowflake REST calls can override them with `X-Snowflake-Role` and `X-Snowflake-Warehouse`, subject to user grants and PAT/OAuth/authentication restrictions. The effective request role needs the Search, semantic-view/base-object, procedure/UDF, warehouse, MCP, or referenced-Agent privileges for every tool. Record the headers/defaults rather than inferring them from a worksheet session. [Agent access control](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-setup), [REST context](https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/setting-context)
- The default inaccessible-tool behavior can continue with accessible tools and warnings. Inspect warnings/tool traces rather than interpreting an answer as proof every configured tool ran.
- A tool-less Agent answers from model knowledge. Agent costs stack across orchestration tokens, Analyst, Search, AI functions, warehouses, code, MCP/web calls, and evaluation.

## Cost and observability routing

There is no universal Cortex event log. Use the surface-specific source:

| Surface | Primary usage/trace direction |
|---|---|
| AI SQL functions | `CORTEX_AI_FUNCTIONS_USAGE_HISTORY`; row-level envelopes in query output |
| Cortex REST inference | `CORTEX_REST_API_USAGE_HISTORY` and client request IDs |
| Cortex Search | Search usage views; request details only when request logging is enabled |
| Direct Analyst | Analyst request/usage history |
| Cortex Agents | Agent usage history plus `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` |

Account Usage is the authoritative cost/reporting surface but is delayed. Event/tracing delivery can be best-effort and undercount. Preserve request/query IDs, model, function/surface, role, region, input size, return envelope, and error details when diagnosing. [AI observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability), [AI cost management](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-func-cost-management)
