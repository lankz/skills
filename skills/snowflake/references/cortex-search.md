# Cortex Search

Cortex Search is a managed materialized source plus lexical/vector indexes plus serving compute. It is not a SQL index and not merely an embedding function. Creation, refresh, serving, querying, access control, and billing are separate contracts.

Use the current [Cortex Search guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview) and [CREATE CORTEX SEARCH SERVICE reference](https://docs.snowflake.com/en/sql-reference/sql/create-cortex-search) for exact syntax.

## Design the service contract

Decide explicitly:

- Single-index `ON <text_column>` or current multi-index `TEXT INDEXES`/`VECTOR INDEXES` syntax.
- Snowflake-managed embeddings, user-provided vectors, or user-provided vectors plus a managed query embedding.
- Searchable text/vector columns, source payload columns potentially returnable by clients, and `ATTRIBUTES` available to the filter DSL.
- A stable text primary key when the data has one; Search primary-key columns must be text and unique.
- Source SQL, refresh warehouse, `TARGET_LAG`, `REFRESH_MODE`, initialization behavior, embedding model, serving auto-suspend, and request logging.
- Production query client, retry policy, result limits, filter/scoring behavior, data authorization, and cost controls.

`ATTRIBUTES` must be present in the source result. An attribute makes a field filterable; it does not add row-level authorization. REST callers choose returned `columns` from the source contract; stopping one client from requesting a field does not remove or revoke that field from the service.

## Creation, initialization, and refresh

- The search index is built as part of creation. `INITIALIZE = ON_CREATE` waits synchronously and fails the DDL if the initial refresh fails. `ON_SCHEDULE` creates an initially empty service whose first scheduled refresh happens later.
- Use a dedicated refresh warehouse unless workload evidence supports sharing. Warehouse size affects source-query/index-build time and cost. Snowflake's current preview-era guidance recommends no larger than `MEDIUM`, but verify the live recommendation and measure the target workload.
- Keep `TARGET_LAG` shorter than source Time Travel retention. Otherwise the service can lose the history it needs to detect changes and may require recreation.
- Incremental refresh requires change tracking and nonzero retention on all underlying objects. Snowflake attempts to enable it, but the creating role needs sufficient ownership/authority. Recreating a base object requires change tracking to be enabled again.

### Current refresh-mode correction

The SQL command reference now supports `REFRESH_MODE = INCREMENTAL | FULL`, with `INCREMENTAL` the default:

- `INCREMENTAL` applies changes and requires the full source/upstream chain to satisfy the current Dynamic Table incremental support matrix. Creation fails when it cannot.
- `FULL` is an explicit escape hatch for unsupported sources, but every source change can recompute embeddings and rebuild the index. Treat it as a consciously costed exception, not an easy compatibility flag.

The Search overview still contains language implying every source must be an incremental candidate. Follow the current DDL reference for grammar, record the documentation discrepancy, and compile-test the target account.

- A source schema change can force a full refresh even on an incremental service. Replacing a frequently updated upstream object can therefore create substantial embedding/index cost; prefer stable contracts and set-based DML such as `MERGE` when appropriate.
- Common anti-joins such as `WHERE NOT EXISTS` use a subquery outside `FROM` and are not incrementally supported. Rewrite to a supported equality left anti-join only when null semantics match, or materialize a curated source table. Do not silently choose `FULL` to hide an unsupported source.
- Row/masking/lookup policy changes can change refresh-role dependencies and trigger reinitialization. Compile the source as the stable owner/refresh role and re-test after policy changes.
- Do not copy the Dynamic Table support matrix into application code. Recheck the live [supported query matrix](https://docs.snowflake.com/en/user-guide/dynamic-tables/supported-queries) whenever source SQL changes.

## Primary keys and service changes

- A valid Search primary key enables an optimized changed-row refresh path. Duplicate primary-key values are not a relational constraint violation; duplicate-key rows can be ignored by the index. Prove uniqueness before declaring it.
- Incremental segments are periodically compacted. `FULL_INDEX_BUILD_INTERVAL_DAYS` is a soft target; Snowflake can rebuild sooner, and compaction does not necessarily re-embed unchanged rows.
- `EMBEDDING_MODEL`, `REFRESH_MODE`, `INITIALIZE`, index declarations, and the source/search contract are creation-time properties. Recreate the service to change them.
- Changing the explicit stored `AS` query or searchable/index/embedding service contract generally requires recreation. Upstream schema changes exposed through a wildcard can instead be absorbed through a costly full refresh; do not rely on that as controlled schema evolution. A client can change its returned subset without DDL only for columns already in the service source, and removing a field from requests does not revoke access to it.
- `ALTER ... SET ATTRIBUTES` can make only an existing source column filterable. It does not add a new source column. Attribute changes become usable after refresh.
- Current `ALTER CORTEX SEARCH SERVICE` grammar supports setting multiple documented properties. One-property statements can still make failure isolation and migration recovery clearer; do not describe them as a parser requirement. [ALTER CORTEX SEARCH SERVICE](https://docs.snowflake.com/en/sql-reference/sql/alter-cortex-search)
- `CREATE OR REPLACE` is atomic only for metadata. The old service data disappears at commit, then the replacement index builds, creating a serving gap. Use a parallel service/cutover when availability matters.

## Query through the right interface

- Use REST or the supported Python API for production serving. `SNOWFLAKE.CORTEX.SEARCH_PREVIEW` is an interactive validation helper with literal-only input, higher latency, no batch input, and a smaller response ceiling. [Query Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/query-cortex-search-service)
- For Snowflake REST APIs, send an explicit `X-Snowflake-Role` when supported; otherwise the user's default role applies. The role must be granted to the user and allowed by its PAT/OAuth/authentication restrictions. Record effective REST context, not an unrelated worksheet role. [REST context](https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/setting-context)
- Search filters are a JSON DSL over declared attributes, not SQL predicates. Operators include current documented forms such as `@eq`, `@contains`, `@gte`, `@lte`, `@primarykey`, `@and`, `@or`, and `@not`.
- Timestamp/date/number filtering has representation limits: unzoned timestamps are treated as UTC, date time portions can be truncated, and very large fixed-point numbers are not supported by every numeric operator. Normalize filter fields deliberately.
- Default retrieval is hybrid keyword/vector search with semantic reranking. Disable reranking or retrieval instruction prefixing only after measuring relevance and latency.
- A named `scoring_profile` takes precedence over inline scoring configuration. Named profiles are drop/recreate rather than mutable. Treat score components as ranking diagnostics, not calibrated probabilities; text-match scores are not comparable across queries.
- For multi-index Search, specify intended indexes to limit cost and ambiguity. Current matching and preview/GA details have changed quickly; verify the target account/client rather than relying on an old SDK example.
- User-provided document vectors and query vectors must share the same model/vector space, not just dimension. With managed query embeddings, use a supported matching model contract.

## Access control is a data grant

Cortex Search executes with owner’s rights. A role with `USAGE` on a service can retrieve indexed rows visible to the owner even when that caller could not select those source rows or would be filtered/masked when querying the source directly.

Choose the isolation boundary deliberately:

- Treat service `USAGE` as direct access to every indexed/returned value.
- Do not expect source row access or masking policies to be reevaluated per Search caller.
- For Snowflake-enforced tenant isolation, build separate services per tenant or identical authorization cohort under owners restricted to those corpora; account for per-service storage/serving cost.
- A shared service is safe only when a trusted application gateway is the authorization boundary: grant `USAGE` only to its backend role, derive tenant filters from authenticated identity, allowlist columns/filters/limits, and never trust a caller-supplied tenant attribute. Search filters alone are not authorization.
- Review sensitive content in searchable text, attributes, returned columns, request logs, and query text.

Create under a stable least-privilege owner role with parent database/schema `USAGE`, `CREATE CORTEX SEARCH SERVICE` on the schema, source `SELECT`, refresh-warehouse `USAGE`, and preferably `SNOWFLAKE.CORTEX_EMBED_USER` when managed embedding is its only Cortex capability. Avoid casual ownership transfer because it can break refresh dependencies. Query clients need database/schema/service `USAGE` plus their interface/authentication contract.

## Serving and indexing are independent states

- Suspending serving stops serving availability/compute but indexing can continue.
- Suspending indexing can leave stale but queryable content while serving remains running.
- Serving `AUTO_SUSPEND` is currently Preview. When available, it has a documented minimum and adds cold-start behavior: the first request waits for resume, while concurrent requests during resume can receive `429` with `Retry-After`. Verify current availability/semantics before relying on it.
- Five consecutive refresh failures can automatically suspend indexing. Inspect `DESCRIBE CORTEX SEARCH SERVICE`, Information Schema state/error fields, and refresh/query history; fix the source before resuming.
- A stale service whose source history is no longer available may need recreation rather than resume.
- Handle ordinary overload/rate-limit `429` responses with bounded exponential backoff and respect `Retry-After`.

## Cost model

Cortex Search can charge across all of these:

1. Warehouse compute for evaluating/materializing the source and refreshing.
2. Embedding tokens for indexed text and re-embedding.
3. Serving compute, including an idle running service.
4. Storage for materialized data and indexes.
5. Cloud services and request/reranking activity.

`FULL` refresh, upstream `CREATE OR REPLACE`, frequent schema changes, overly aggressive target lag, unused indexes, no primary key on change-heavy data, and permanently running serving compute can multiply cost. Preloading possible future source columns can avoid a rebuild but increases materialized/serving size and expands the direct data grant; make that security-versus-rebuild trade-off explicitly. Use the live [Search cost guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-costs).

Resource budgets are monitoring/enforcement workflows with delayed measurement; spend can overshoot. A true stop requires an authorized custom action that suspends/revokes the relevant service access, not an assumption that a budget is a synchronous cap. [Search resource budgets](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-resource-budgets)

## Request logging and observability

- Request logging is opt-in. When enabled, it can record the complete query/request body plus response code, latency, user, role, and session. Treat that telemetry as sensitive stored data with retention/storage cost. [Monitor Search requests](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-monitor)
- Track refresh/indexing state and serving/request state separately. A healthy index does not prove serving works, and a successful query does not prove the index is fresh.
- Preserve the request ID, caller/default role, service state, source refresh error, selected indexes/profile, filter JSON, response status, and usage/cost window when diagnosing.

## Deployment verification

1. Compile the source query under the service owner and refresh warehouse.
2. Prove declared primary-key uniqueness and validate attribute types.
3. Confirm model, region, roles, source grants, warehouse grant, change tracking, and retention.
4. Create with deliberate refresh/initialization properties; allow for a long initial build.
5. Inspect `DESCRIBE CORTEX SEARCH SERVICE` and Information Schema state/error fields.
6. Query through the intended production API with filters, retries, and authorization tests—not only `SEARCH_PREVIEW`.
7. Test a source insert/update/delete and observe freshness/cost.
8. Test serving suspension/resume and an indexing failure path where feasible.
9. Measure relevance, latency, embedding/index size, refresh credits, and idle serving cost before widening use.
