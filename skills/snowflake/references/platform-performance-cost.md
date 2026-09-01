# Platform, performance, observability, and cost

Snowflake separates persisted storage, independently sized compute, and cloud services. Standard-table storage is columnar, compressed, and automatically divided into immutable micro-partitions; virtual warehouses do not own the data they query. Start with the [key concepts](https://docs.snowflake.com/en/user-guide/intro-key-concepts), then identify every compute/storage surface in the workload.

## Platform capability map

Use this as routing, not a product catalog:

| Requirement | Snowflake capability to evaluate | Distinctive decision |
|---|---|---|
| SQL analytics and batch transforms | Virtual warehouse | Size up for a query; multi-cluster scales concurrency |
| Low-latency keyed OLTP-style access | Hybrid tables / Unistore | Enforced keys/indexes and different limits/costs from standard tables |
| Managed pipeline freshness/state | Dynamic tables | SELECT refresh modes plus custom incremental DML |
| CDC processing | Streams + tasks | Offset-based changes and committed consumption |
| Open table format | Iceberg tables | Catalog/storage/writer ownership controls feature set |
| Python/Java/Scala data processing | Snowpark | Code is planned/executed in Snowflake; APIs are versioned |
| Custom functions/procedures | UDFs / stored procedures | Handler runtime, owner/caller rights, package/network limits |
| Container workloads | Snowpark Container Services | Compute pools, services/jobs, image repositories, networking |
| Data app distribution | Native App Framework | Application packages/roles, provider-consumer security contract |
| Interactive data applications | Streamlit in Snowflake | Warehouse or container runtime and Snowflake access model |
| Live cross-account data | Secure Data Sharing / listings | Provider storage, consumer compute, read-only shared objects |
| Privacy-safe multi-party analysis | Data Clean Rooms | Governed collaboration contract rather than ordinary shared tables |
| LLM/retrieval/semantic orchestration | Cortex surfaces | Model/region/role plus token, indexing, and serving costs |

When one of these is central, open its current section through [Snowflake's documentation index](https://docs.snowflake.com/llms.txt); do not extend a nearby feature by analogy.

## Virtual warehouses and concurrency

- A virtual warehouse is isolated MPP compute. Suspending it does not make table data unavailable, but it discards its local data cache. Another warehouse can query the same storage with independent compute and cache. [Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-overview)
- Billing is per second with a 60-second minimum each time a warehouse starts/resumes. Frequent suspend/resume can therefore increase minimum charges and destroy useful local cache; leaving an idle warehouse running also costs credits. Tune from workload cadence.
- Resizing affects new/queued work, not a query already executing. Scale up when one query needs more parallelism/memory; use multi-cluster scale-out when concurrent queries queue. A larger warehouse is not automatically faster for small queries or insufficiently parallel file loads.
- Multi-cluster `STANDARD` prioritizes reducing queues; `ECONOMY` permits more queueing to save credits. `SCALING_POLICY` is a multi-cluster property; omit it from portable single-cluster warehouse definitions. [Multi-cluster warehouses](https://docs.snowflake.com/en/user-guide/warehouses-multicluster)
- Warehouse generation/default availability can differ across accounts/regions. Inspect the target account and `SHOW WAREHOUSES` rather than assuming a default from an example.
- Query Acceleration Service, serverless tasks, Snowpipe, automatic clustering, Search Optimization, Cortex serving, and similar features are not “the warehouse.” They select/bill compute through their own contracts.

## Three caches agents confuse

1. Metadata enables micro-partition pruning without a running warehouse cache.
2. Warehouse-local data cache accelerates repeated scans on the same running warehouse and is lost on suspend.
3. Persisted query results can be reused for up to 24 hours independently of warehouse state, but only for effectively identical deterministic SQL with unchanged inputs, configuration, and privileges.

Do not attribute a fast rerun to a warehouse resize without determining which cache answered it. Disable/use cache only through documented session parameters when benchmarking. [Warehouse cache](https://docs.snowflake.com/en/user-guide/performance-query-warehouse-cache), [persisted results](https://docs.snowflake.com/en/user-guide/querying-persisted-results)

## Performance starts with micro-partition pruning

Standard Snowflake tables do not use conventional user-created indexes. Snowflake records micro-partition metadata such as value ranges and distinctness and prunes partitions when predicates remain sargable against that metadata. [Micro-partitions](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions)

Diagnose before adding a service:

- Poor pruning: filters miss clustering metadata, wrap table columns in casts/functions, use weakly selective values, or hide constants behind unsupported subquery shapes.
- Queueing: concurrency exceeds warehouse clusters/capacity.
- Local/remote spill: working set exceeds memory; query shape or warehouse size may need change.
- Intermediate-row explosion and repeated scans: confirm Snowflake operator row counts rather than guessing from final output size.
- Tiny metadata-heavy queries and single-row DML can shift cost toward cloud services and transaction overhead.

Use Query Profile/Query Insights and, for supported completed queries, operator stats:

```sql
SELECT *
FROM TABLE(GET_QUERY_OPERATOR_STATS('<query-id>'));
```

[Query performance exploration](https://docs.snowflake.com/en/user-guide/performance-query-exploring), [operator stats](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)

## Add optimization services from evidence

### Clustering

- Natural ingestion order can already cluster a table sufficiently. A clustering key is usually justified only for large tables whose selective filters repeatedly scan too many partitions.
- Automatic clustering adds serverless maintenance credits and storage churn. Choose expressions supported by pruning and monitor clustering depth plus maintenance cost. [Clustering keys](https://docs.snowflake.com/en/user-guide/tables-clustering-keys)

### Search Optimization Service

- Search optimization builds persistent access paths for supported selective point, substring/regex, semi-structured, geospatial, and join lookup shapes. It is unrelated to Cortex Search.
- A cast/function on the table-side search expression can prevent its use. Build and maintenance happen asynchronously and incur serverless/storage costs; no benefit appears until the build is ready. [Search Optimization](https://docs.snowflake.com/en/user-guide/search-optimization-service)

### Materialized views

- Snowflake materialized views have far stricter definitions than ordinary views: one base table and substantial restrictions on joins, subqueries, window functions, nondeterminism, and constructs. Check the current eligibility matrix. [Materialized views](https://docs.snowflake.com/en/user-guide/views-materialized)
- Snowflake can rewrite a base-table query to use a suitable materialized view without the query naming it. Maintenance is serverless and can compound with clustering/search optimization on frequently changing data.

### Query Acceleration and top-K pruning

- Query Acceleration offloads eligible portions of outlier scans; it is not a generic replacement for warehouse sizing/query fixes.
- Top-K pruning can stop scans early for eligible `ORDER BY ... LIMIT` queries, but expression types, casts, and null ordering affect eligibility. [Top-K pruning](https://docs.snowflake.com/en/user-guide/querying-top-k-pruning-optimization)

Estimate build/maintenance/storage and validate realized query savings before retaining any optimization service.

## Cost surfaces

Snowflake cost is not a single warehouse number. Account for:

- User-managed warehouse credits while running.
- Serverless feature credits.
- Compute pools and service compute.
- Cortex tokens/pages, embeddings, indexing, and serving.
- Database and stage storage, including retained historical micro-partitions.
- Cross-region/cross-cloud data transfer.
- Cloud-services usage above Snowflake's daily adjustment threshold.

[Understanding compute cost](https://docs.snowflake.com/en/user-guide/cost-understanding-compute), [storage cost](https://docs.snowflake.com/en/user-guide/cost-understanding-data-storage), [transfer cost](https://docs.snowflake.com/en/user-guide/cost-understanding-data-transfer)

Cloud-services consumption can grow through frequent metadata calls, repeated DDL/clones, very small queries/inserts, file-listing patterns, and excessive object counts. Optimize orchestration/chatty clients as well as SQL. [Cloud-services optimization](https://docs.snowflake.com/en/user-guide/cost-optimize-cloud-services)

## Resource monitors versus budgets

- Resource monitors track user-managed warehouse credits and related cloud-services usage. Only `ACCOUNTADMIN` can create one and assign warehouses. They do not control serverless features. [Resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- `SUSPEND` waits for running queries; `SUSPEND_IMMEDIATE` cancels them. Enforcement can lag and exceed a threshold, so a monitor is not an exact transactional cap.
- Create a monitor before attaching it to a warehouse and verify the assignment separately. Do not emit multi-cluster-only warehouse properties into a single-cluster definition.
- Budgets monitor/forecast a broader set of supported objects and serverless features. Measurement is delayed, and budgets do not stop spend without an authorized custom action. Low-latency monitoring has its own cost. [Budgets](https://docs.snowflake.com/en/user-guide/budgets)

Choose visibility, notification, and suspension actions according to workload criticality. A production warehouse should not inherit a destructive suspension action from an ad hoc workload without explicit intent.

## Observability scopes and latency

Use the narrowest suitable surface:

| Scope | Best use | Caveat |
|---|---|---|
| `INFORMATION_SCHEMA` table functions/views | Recent operational checks | Shorter windows and function-specific privileges/limits |
| `SNOWFLAKE.ACCOUNT_USAGE` | Longer account history, cost, governance | Delayed; view-specific latency |
| `ORGANIZATION_USAGE` | Cross-account reporting/billing | Organization privileges and longer delays |
| Snowsight Query History/Profile | Interactive query diagnosis | UI window and access limits |
| `GET_QUERY_OPERATOR_STATS` | Operator-level completed-query evidence | Supported history/privileges only |
| Service-specific history/state | Pipes, tasks, dynamic tables, Cortex | No universal state/trace table |

`ACCOUNT_USAGE` latency varies: query history can be much fresher than warehouse load or access history, but none should be treated as synchronous. Information Schema is often fresher and shorter-lived. Check the view's current latency/retention contract. [Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage)

Set a structured `QUERY_TAG` for deployments/jobs and retain query IDs. Query tags appear in history but are session state, so connection reuse can leak a stale tag unless it is reset.

## Cost/performance workflow

1. Define latency, freshness, concurrency, and cost objectives.
2. Identify the warehouse, serverless, service, storage, transfer, and model surfaces.
3. Capture representative query IDs and query/profile/operator evidence.
4. Separate pruning, queueing, spill, join shape, refresh maintenance, and cache effects.
5. Change one lever: SQL shape, warehouse size, multi-cluster policy, clustering, optimization service, refresh/target lag, or serving state.
6. Re-run without confusing persisted/local cache effects.
7. Compare both latency and all relevant usage views over a representative window.
