---
name: snowflake-knowledge
description: Work with Snowflake-specific SQL and platform features, including data pipelines, Cortex AI and Search, security, cost and performance, Snowflake CLI, APIs, and deployment. Use whenever a task targets Snowflake; do not apply these dialect rules to Snowflake Postgres or an unrelated database.
---

# Snowflake

Treat Snowflake as a distinct cloud data platform, not PostgreSQL with different hosting. Focus on behavior that a capable SQL user or coding agent is likely to guess incorrectly; do not teach generic SQL or data-modeling basics.

## Start with the live contract

Snowflake syntax and feature contracts change frequently. Start at the official [LLM documentation index](https://docs.snowflake.com/llms.txt), then prefer the current SQL command/function reference over remembered syntax, examples in training data, or a historical workaround. Verify versioned client and Snowpark APIs against the version actually in use.

The bundled guidance was checked against official Snowflake documentation on 2026-09-02. Treat that date as a provenance baseline, not a frozen platform version: current official documentation and the target account's live capabilities take precedence.

Inspect the repository's existing Snowflake migrations, helpers, query builders, deployment tooling, and tests before introducing a new query shape. Establish which interface executes the work: worksheet, `snow sql`, driver, SQL API, Snowpark, task, dynamic table, Cortex REST API, or another service.

## Load only the references the task needs

| Work | Read |
|---|---|
| SQL, identifiers, types, functions, DML, transactions, constraints, Time Travel | [sql-dialect.md](references/sql-dialect.md) |
| Loading, stages, COPY, Snowpipe, streams, tasks, dynamic tables, Iceberg | [data-pipelines.md](references/data-pipelines.md) |
| AI functions, documents, vectors, semantic views, Analyst, Agents | [cortex-ai.md](references/cortex-ai.md) |
| Cortex Search creation, querying, refresh, security, cost, and operations | [cortex-search.md](references/cortex-search.md) |
| Architecture, warehouses, caching, performance, observability, and cost | [platform-performance-cost.md](references/platform-performance-cost.md) |
| Roles, grants, policies, Time Travel retention, cloning, sharing, replication | [security-data-lifecycle.md](references/security-data-lifecycle.md) |
| Snowflake CLI, SQL API, drivers, authentication, procedures, IaC, migrations | [tooling-deployment.md](references/tooling-deployment.md) |
| A current rule does not explain a failure that resembles a known historical observation | [field-notes.md](references/field-notes.md) |

Read multiple references only when the operation genuinely crosses those boundaries. Follow links to official documentation for exact grammar, current support matrices, region/model availability, preview state, and prices rather than copying volatile tables into a plan.

## Establish the execution contract

Before privileged, mutating, scheduled, or costly work, determine the target account and environment, primary and secondary roles, database, schema, warehouse or serverless service, client and version, and relevant region/edition/feature state. When a live session is available, verify rather than infer:

```sql
SELECT
  CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME(), CURRENT_USER(),
  CURRENT_ROLE(), CURRENT_SECONDARY_ROLES(),
  CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE();
```

Use the preferred `<organization>-<account>` account identifier in new configuration unless the target system requires another form. Remember that primary-role, default-role, active-role, and owner-rights behavior differ by interface and feature.

## Author for Snowflake

- Confirm every material function, data type, clause, DDL property, privilege, and feature restriction in current Snowflake documentation. Similar-looking syntax from another SQL dialect is not evidence.
- Bind data values. For dynamic object names, use `IDENTIFIER(?)`, `IDENTIFIER($variable)`, or the client's documented identifier mechanism; do not turn text templating into a substitute for bindings.
- Make conversions explicit at semi-structured, timestamp, vector, file, and API boundaries. Know the input and output type before choosing `AS_*`, `TO_*`, `TRY_TO_*`, parsing, or casting.
- Make DML sources deterministic before `MERGE` or `UPDATE ... FROM`. Do not let duplicate source matches choose target results.
- Treat each DDL statement as an independently recoverable deployment step. Snowflake DDL implicitly commits and does not become rollbackable merely because a client wraps the file in a transaction.
- Treat privileges, ownership, object state, region, edition, model lifecycle, and account parameters as inputs to correctness. A syntax-looking error can be a capability or authorization failure.
- Identify every compute surface before estimating performance or cost: user-managed warehouse, serverless feature, cloud services, Cortex tokens/pages, serving compute, storage, and transfer are controlled and billed differently.

## Prove the result narrowly

Compile or execute the smallest faithful statement in the intended account, role, client, and object context when execution is authorized. A read-only request does not authorize DDL, writes, warehouse resume, serverless service creation, cross-region processing, or an unbounded/costly query.

After a change, use the narrowest useful evidence: `SHOW`, `DESCRIBE`, `GET_DDL`, Information Schema, service state, task/pipe/dynamic-table history, query history, or the relevant usage view. Preserve the Snowflake error, query ID, role, client, and minimal failing SQL. For generated SQL families, test the emitted Snowflake SQL rather than only the generator's intermediate representation.

Classify failures before rewriting SQL:

1. Grammar or type contract.
2. Primary/default role, ownership, grants, or parent-object `USAGE`.
3. Region, edition, account parameter, preview, model lifecycle, or feature availability.
4. Object state, refresh state, retention, staleness, or dependency ordering.
5. Client behavior: statement count, bindings, templating, transactions, retries, or session reuse.
6. Performance or cost: pruning, queueing, spill, refresh mode, serverless maintenance, or service state.

When official pages disagree, use the current command/function reference as the syntax authority, note the discrepancy, and compile-test the exact target account. Keep a historical workaround only as a labeled field observation, never as universal Snowflake law.
