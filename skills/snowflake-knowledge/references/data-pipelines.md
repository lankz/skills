# Data loading and pipelines

Use this reference for stages, `COPY`, Snowpipe, streams, tasks, dynamic tables, and Iceberg tables. These features have separate state, compute, retention, and SQL restrictions; do not flatten them into a generic ETL abstraction.

## Choose the Snowflake-native state model

| Need | Usually start with | Important contract |
|---|---|---|
| Bulk files already in a stage | `COPY INTO <table>` | Warehouse compute, file/load metadata, restricted transforms |
| Continuous file arrival | Snowpipe | Serverless ingestion around a pipe's `COPY` statement |
| Low-latency row streaming | Snowpipe Streaming | Channel/offset contract, not file-based Snowpipe |
| Consume table change data | Stream + task/DML | Stream is an offset over change history, not stored rows |
| Scheduled or event-triggered SQL/procedure | Task or task graph | User-managed/serverless compute and suspended/run state |
| Managed refreshed result or advanced incremental state | Dynamic table | Snowflake-managed SELECT modes or custom DML refresh logic |
| Open table format in object storage | Iceberg table | Catalog and storage ownership determine features and writes |

Use the current [data loading overview](https://docs.snowflake.com/en/guides-overview-loading-data), [streams and tasks guide](https://docs.snowflake.com/en/user-guide/data-pipelines-intro), and [dynamic tables guide](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview) to confirm feature selection.

## Stages, file formats, and `COPY INTO`

- A stage is a Snowflake object/reference to files; a file format is a parsing contract. Prefer named stages, storage integrations, and named file formats for repeatable production loads instead of embedding credentials and long option lists in generated SQL.
- Internal stage kinds (`@~`, `@%table`, named stage) and external stages have different URL, encryption, privilege, directory-table, and client-command behavior. `PUT` uploads only to internal stages and is not supported by the SQL API. [Stages](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-create-stage), [PUT](https://docs.snowflake.com/en/sql-reference/sql/put)
- `COPY INTO <table>` remembers loaded file metadata and normally skips files already loaded into that target. `FORCE=TRUE` bypasses that protection and can duplicate data. Recreated/cloned tables and expired load history alter what “already loaded” means. [COPY INTO table](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table)
- `PURGE=TRUE` is best-effort. A successful load does not guarantee source-file deletion; verify or lifecycle files independently.
- `PATTERN` is a regular expression, not a glob. Bulk `COPY` applies it to the full storage path, while Snowpipe trims the stage path before matching. Test the exact stage/prefix/pipe combination.
- Avoid huge numbers of tiny files and a few enormous unsplittable files. File sizing, compression, and warehouse size affect parallelism; larger warehouses do not compensate for insufficient file-level concurrency. [Data load considerations](https://docs.snowflake.com/en/user-guide/data-load-considerations-prepare)
- Use load metadata such as `METADATA$FILENAME`, `METADATA$FILE_ROW_NUMBER`, content checksum, and file timestamps when lineage/idempotency needs them. Confirm which metadata columns are available for the source and load path. [Metadata columns](https://docs.snowflake.com/en/user-guide/querying-metadata)

### COPY transforms are deliberately restricted

The transform is a limited projection over staged data, not an arbitrary query. Do not put joins, `FLATTEN`, filtering, grouping, ordering, or limiting into it. `MATCH_BY_COLUMN_NAME` cannot be combined with a transform or validation mode. [Transforming during load](https://docs.snowflake.com/en/user-guide/data-load-transform)

Validation surfaces are not interchangeable:

- `VALIDATION_MODE` on `COPY INTO` validates supported untransformed load shapes without loading.
- `VALIDATE(table, job_id => ...)` reports errors from a prior `COPY` job but does not cover every transform-expression failure.
- `COPY_HISTORY` and load history show recorded load outcomes within their retention/latency windows.

For complex parsing, land raw values first or use a separate set-based transform whose SQL can be compiled and tested independently.

## Snowpipe and Snowpipe Streaming

- Snowpipe uses Snowflake-managed serverless compute to load files described by a pipe's `COPY` statement. It is not a continuously running virtual warehouse and is not controlled by warehouse resource monitors. Monitor pipe/serverless usage separately. [Snowpipe introduction](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro)
- Auto-ingest depends on cloud event notification and integration state. File arrival, notification delivery, pipe queueing, and table visibility are distinct checkpoints; inspect `SYSTEM$PIPE_STATUS`, notification configuration, and copy history before rewriting SQL.
- `VALIDATE_PIPE_LOAD` returns an error for a pipe whose `COPY` statement transforms data, and it only covers its documented recent history. For transformed pipes, use `SYSTEM$PIPE_STATUS`, `COPY_HISTORY`, pipe usage/history, and application-specific file/count evidence. [VALIDATE_PIPE_LOAD](https://docs.snowflake.com/en/sql-reference/functions/validate_pipe_load)
- Pause a pipe before incompatible table/pipe changes and inspect pending files. `CREATE OR REPLACE PIPE` can change ownership/state and is not a transparent edit.
- Snowpipe Streaming has channel and offset-token semantics and dedicated SDK/high-performance architecture. Do not apply file-pipe commands, file deduplication assumptions, or `VALIDATE_PIPE_LOAD` to it. Select the current architecture and client version from the [Snowpipe Streaming guide](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/data-load-snowpipe-streaming-overview).

## Streams: offsets over change history

- A stream stores an offset over a source object's version history; it does not copy change rows into a queue. Metadata columns describe insert/delete/update actions when queried. [Streams introduction](https://docs.snowflake.com/en/user-guide/streams-intro)
- `SELECT` does not advance a stream. A successful committed DML statement that consumes the stream advances its offset; rollback leaves it unchanged. Use one stream per independent consumer.
- A stream can become stale when the source's retention no longer covers its offset. Monitor `STALE_AFTER`, consume within retention, and understand that a `FALSE` `SYSTEM$STREAM_HAS_DATA` check on an empty stream can help preserve it. A stale stream cannot be recovered; recreate it.
- `SYSTEM$STREAM_HAS_DATA` is designed to avoid false negatives but can return false positives. A task can therefore run with no consumable rows. Make the body idempotent and monitor repeated empty runs. [Managing streams](https://docs.snowflake.com/en/user-guide/streams-manage)
- `CREATE OR REPLACE` of a source object can break/change a stream's continuity; a rename generally preserves it. Verify stream state after source-object lifecycle operations.
- Standard streams expose inserts/deletes plus update pairs. Append-only and insert-only streams have different eligibility and semantics. Feature matrices vary by source type; check the exact current source/stream combination.
- Dynamic tables support standard streams only, created with `ON DYNAMIC TABLE`; full-refresh dynamic tables do not support streams. After a dynamic-table reinitialization, the stream can expose a very large delta, and prior updates appear as `DELETE` + `INSERT` pairs with `METADATA$ISUPDATE = FALSE`. Capacity-plan for that delta and consume it with an idempotent `MERGE`; branching on `METADATA$ISUPDATE` alone can lose or duplicate data. [Streams on dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/streams-on-dts)

## Tasks and task graphs

- Tasks run SQL or a stored procedure on a schedule, after predecessors, or when a `WHEN` condition is true. User-managed tasks name a warehouse; serverless tasks let Snowflake size compute and bill it separately. [Tasks introduction](https://docs.snowflake.com/en/user-guide/tasks-intro)
- A created or cloned task starts suspended. In a graph, resume child tasks before the root, or use the documented graph-enablement system function. Verify `state`, schedule, predecessors, and owner after deployment.
- Scheduled runs skip overlaps by default. Use current `OVERLAP_POLICY` grammar and design the body for retries/duplicate triggers; do not assume a scheduler guarantees exactly once.
- `WHEN SYSTEM$STREAM_HAS_DATA('stream')` avoids starting compute for most empty checks, but false positives still start runs. Conditions accumulate cloud-services evaluation cost when triggered too frequently without runs.
- Task sessions have feature restrictions: do not assume interactive session parameters such as `AUTOCOMMIT=FALSE` or `SEARCH_PATH` are available. Fully qualify durable task SQL and set supported task/session parameters explicitly. [CREATE TASK](https://docs.snowflake.com/en/sql-reference/sql/create-task)
- Task graphs have a single root, predecessor/finalizer rules, shared configuration, retry behavior, and graph-version semantics. Replacing or altering tasks while a graph runs does not necessarily affect the in-flight version. [Task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs)
- Capture task history and query IDs. Distinguish skipped schedule, false condition, graph cancellation, warehouse queueing, SQL failure, timeout, and ownership/privilege failure.

## Dynamic tables

A dynamic table maintains state toward a target freshness. Most are SELECT-based and refreshed by Snowflake; `CUSTOM_INCREMENTAL` instead runs one constrained `MERGE INTO SELF` or `INSERT INTO SELF` statement per refresh. It is neither an ordinary view nor a general-purpose task/procedure.

### Choose refresh mode explicitly

- For an `AS SELECT` definition, `AUTO` selects FULL or INCREMENTAL once when the object is created and does not reconsider later. With `REFRESH USING`, it resolves to CUSTOM_INCREMENTAL.
- `INCREMENTAL` requires the entire query and upstream chain to satisfy the current incremental support matrix.
- `FULL` recomputes the result and can make downstream incremental chains invalid or expensive.
- `ADAPTIVE` begins incremental and can reinitialize when Snowflake estimates a rebuild is cheaper; it remains a Snowflake-managed SELECT mode.
- `CUSTOM_INCREMENTAL` runs user-defined constrained DML to maintain state and is not a substitute for ordinary SELECT incrementalization.

Confirm current account/tooling limitations before using `ADAPTIVE` or `CUSTOM_INCREMENTAL`. [Refresh modes](https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes), [CREATE DYNAMIC TABLE](https://docs.snowflake.com/en/sql-reference/sql/create-dynamic-table), [refresh optimization](https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-optimization)

After creation, inspect rather than infer:

```sql
SHOW DYNAMIC TABLES LIKE 'MY_TABLE' IN SCHEMA my_db.my_schema;
-- Inspect refresh_mode, refresh_mode_reason, scheduling_state, and target_lag.
```

### Incremental SQL is a separate eligibility contract

Read the live [supported incremental queries matrix](https://docs.snowflake.com/en/user-guide/dynamic-tables/supported-queries) for every query change. High-value restrictions include:

- Subqueries outside `FROM` are not incrementally supported; that includes common `WHERE EXISTS`, `IN (SELECT ...)`, and `NOT EXISTS` forms.
- Incremental outer joins require supported equality predicates. Rewriting `NOT EXISTS` as a left anti-join is correct only when null semantics match.
- `LATERAL FLATTEN` is supported in documented shapes, but selecting `FLATTEN.SEQ` is not.
- Structured types, sequences, nondeterministic/volatile expressions, table functions, set operations, self-joins, and window constructs each have feature-specific restrictions that change over time. Do not freeze the whole matrix into generated validators.
- Upstream objects need change tracking and sufficient retention. A supported top-level query can still fail because of an upstream view/object contract.

### Target lag and lifecycle

- `TARGET_LAG = DOWNSTREAM` delegates scheduling to downstream refresh demand. Time-based lag is a target, not a guarantee; refresh duration, warehouse contention, and upstream lag contribute.
- Keep target lag inside upstream retention. Suspended or repeatedly failing refreshes can make change history unavailable and require reinitialization.
- `INITIALIZE = ON_CREATE` makes creation wait for the first refresh; `ON_SCHEDULE` creates an initially unpopulated object. Choose based on deployment-time blocking and readiness needs.
- Use refresh history and event tables to diagnose skipped, failed, or slow refreshes. Do not equate successful DDL with populated/fresh data.

### Custom incremental dynamic tables

Use `CUSTOM_INCREMENTAL` only when stateful merge/append logic cannot be expressed efficiently as a supported SELECT-based dynamic table. Read the live [custom incrementalization guide](https://docs.snowflake.com/en/user-guide/dynamic-tables/custom-incrementalization) before designing it.

- Declare an explicit target column list and use `REFRESH USING (<dml_statement>)`. The refresh body is exactly one supported `MERGE INTO SELF` or `INSERT INTO SELF`, not an arbitrary procedure or DDL block.
- Read changed source rows through the documented `CHANGES()` contract. Use `APPEND_ONLY` only when updates/deletes truly cannot occur; otherwise define their propagation.
- Make the `MERGE` source deterministic and unique by target key. The ordinary Snowflake nondeterministic-merge rules still apply.
- Understand initialization/backfill state. `BACKFILL FROM` plus `START AT` can establish the retained target and change-data starting point; source retention must cover every unread change.
- `FROZEN WHERE` and `INSERT ONLY INPUTS` cannot be combined with `REFRESH USING`. `INITIALIZATION_WAREHOUSE` can isolate initialization compute from routine refresh capacity, but it does not relax custom-refresh limitations.
- `SCHEDULER = DISABLE` creates an externally/manual-refreshed isolation boundary; it changes target-lag requirements and upstream refresh behavior.
- Custom incremental mode currently has no dbt or DCM integration. Prefer `CREATE OR ALTER DYNAMIC TABLE` for supported custom-definition changes and verify other reconcilers understand `REFRESH USING` before adopting them.
- An upstream `ALTER` can make the next refresh fail until the custom definition is updated. Upstream `CREATE OR REPLACE` breaks change tracking and requires recreating the downstream custom dynamic table.
- Monitor the custom table's refresh mode/action, source change volume, retained-state correctness, duplicate keys, and backfill boundary—not only freshness lag.

`ADAPTIVE` and `CUSTOM_INCREMENTAL` solve different problems: ADAPTIVE lets Snowflake choose incremental maintenance versus reinitialization for a SELECT definition; CUSTOM_INCREMENTAL makes the developer responsible for correct DML state transitions.

## Iceberg tables

Snowflake Iceberg support is a family of contracts, not one table type. Determine all of the following before writing DDL:

- Who owns the catalog: Snowflake, an external catalog, or an Iceberg REST catalog.
- Who writes data and metadata: Snowflake, another engine, or both under a supported managed mode.
- Which cloud storage, external volume, catalog integration, and credential model apply.
- Whether the table is Snowflake-managed, externally managed/read-only, converted, or synchronized.

Feature support differs from standard tables for DML, schema evolution, Time Travel, cloning, streams, dynamic tables, constraints, clustering, search optimization, replication, and data types such as `VECTOR`. Use the exact current [Iceberg table documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg) and command variant; do not take a `CREATE TABLE` property and assume it applies to `CREATE ICEBERG TABLE`.

External-catalog refresh and Snowflake query visibility are separate from object creation. After DDL or external writes, verify metadata refresh status, snapshots, and the catalog/storage integration rather than diagnosing every stale result as result-cache behavior.

## Pipeline deployment checklist

1. Identify the state owner: load metadata, pipe queue, stream offset, task graph version, dynamic-table refresh, or Iceberg catalog.
2. Identify compute and cost: warehouse, serverless ingestion/task/refresh, cloud services, storage, and downstream service cost.
3. Compile the exact source query and conversion expressions independently.
4. Deploy DDL in dependency order; remember each statement commits independently.
5. Verify object ownership/grants plus pipe/task/stream/refresh state.
6. Prove data movement with bounded file, row-count, offset, or history evidence.
7. Test retry, duplicate input, empty input, late input, and partial failure behavior.
