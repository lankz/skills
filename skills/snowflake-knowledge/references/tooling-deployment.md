# Clients, authentication, procedures, and deployment

The same SQL can behave differently because Snowflake clients own session context, bindings, templating, statement boundaries, retries, and result fetching. Establish the client/version/authentication contract before diagnosing only the SQL text.

## Prefer Snowflake CLI for new command-line work

Snowflake CLI uses the `snow` command and is the current CLI for SQL, connections, Snowpark, Streamlit, Native Apps, services, and deployment workflows. SnowSQL is legacy; migrate rather than adding new SnowSQL-only automation. [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction), [SnowSQL migration](https://docs.snowflake.com/en/user-guide/snowsql-migrate)

Useful baseline:

```sh
snow connection test -c deployment
snow sql -c deployment --enhanced-exit-codes -f migration.sql
snow sql -c deployment -q 'SELECT SYSTEM$CLIENT_VERSION_INFO()'
```

- Use named connections in the supported TOML configuration and owner-only file permissions. Prefer `snow connection add/list/test/set-default` over hand-maintained secret blobs. [Configure connections](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-connections)
- Connection values have a precedence order across flags, connection-specific environment, config, and generic environment. Inspect the resolved connection when account/role/warehouse context is surprising.
- Use `--enhanced-exit-codes` in automation so SQL failures differ from usage/config failures.
- Use `-f` for complex SQL/Snowflake Scripting and shell-sensitive `$`/`$$` content. Avoid shell interpolation accidents in `-q`.
- CLI `-D` variables with `<% variable %>` are client-side text templating, not SQL bindings. Do not place untrusted values into templates. Bind data in the executing driver/API or safely materialize a controlled SQL file. [SQL variables in CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/project-definitions/use-sql-variables)
- `--local-only` prevents supported source/load commands from fetching remote URLs. Use it when executing untrusted or review-bound scripts.
- `JSON_EXT` output returns parsed JSON values rather than JSON-encoded strings; choose output mode as an API contract.
- `--single-transaction` can wrap compatible DML, but Snowflake DDL still implicitly commits. It cannot make a DDL migration atomic. [snow sql](https://docs.snowflake.com/en/developer-guide/snowflake-cli/command-reference/sql-commands/sql)

## SQL API

The SQL API endpoint `/api/v2/statements` is an asynchronous-capable request/result protocol, not a stateless “run SQL string” shortcut. [SQL API](https://docs.snowflake.com/en/developer-guide/sql-api/intro)

- One statement is the safest default. Multiple statements require `MULTI_STATEMENT_COUNT` equal to the exact count or `0`; bind variables are unsupported for a multi-statement request. Fetch every returned statement handle separately. [Multiple statements](https://docs.snowflake.com/en/developer-guide/sql-api/submitting-multiple-statements)
- The API can return `202` even when asynchronous execution was not explicitly requested. Poll the statement handle and fetch all result partitions before declaring completion.
- Handle `429` and transient failures with bounded retry/backoff. For idempotent API retry, preserve the same UUID `requestId` and use the documented retry flag; generating a new request ID can execute a mutation twice.
- Warehouse, role, database, and schema request values are case-sensitive identifiers. Bound values use API-specific string encodings for numbers/times; follow the binding contract rather than sending native JSON values by intuition.
- Earlier statements can commit before a later statement fails. Explicit transactions must start and finish in the same multi-statement request, and DDL still auto-commits. SQL API requires compatible autocommit behavior. [SQL API transactions](https://docs.snowflake.com/en/developer-guide/sql-api/using-transactions)
- `PUT`/`GET` are not SQL API operations. Use supported stage/file clients.
- Preserve request ID, statement handles/query IDs, status/HTTP response, role/context, and partition-fetch state.

## Snowflake REST resource APIs

Do not conflate the SQL API, Cortex inference endpoints, Cortex Agent/Search endpoints, and object-management REST APIs; each has its own path, body, results, and retry contract. Supported Snowflake REST APIs accept explicit request context:

- `X-Snowflake-Role` selects an existing role granted to the user and allowed by the authentication method/token restriction.
- `X-Snowflake-Warehouse` selects a warehouse on which the effective role has `USAGE`.
- Headers take precedence over user defaults; defaults apply when headers are absent, and a warehouse-dependent call fails if neither supplies one.

Send these per request instead of mutating user defaults, and log the non-secret effective context. [REST request context](https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/setting-context)

## Drivers and connection/session scope

- A driver connection is a stateful Snowflake session: primary role, secondary-role mode, warehouse, database/schema, parameters, query tag, transactions, last query ID, retry state, and temporary objects live there.
- Do not concurrently share one connection across threads. Context changes, commits, `LAST_QUERY_ID()`, and driver retry/query context can race. Use a connection per logical operation/thread or the driver's documented pool behavior. [Driver connections](https://docs.snowflake.com/en/developer-guide/driver-connections)
- Bind values with the driver's supported parameter style. Use `IDENTIFIER(?)` where Snowflake supports a bound object identifier. Never bind by string formatting.
- Connector binding modes and supported data types differ. Native `VECTOR`, semi-structured values, large results, arrays, timestamps, and async results need version-specific handling.
- Pin connector/Snowpark versions and verify signatures against the versioned API reference. Do not write to the newest docs while deploying an older runtime.

## Authentication choice and role constraints

Prefer non-password workload identity appropriate to the environment:

1. Workload Identity Federation (WIF) for supported cloud/OIDC workloads.
2. OAuth for delegated/federated access.
3. Named key-pair authentication when federation is unavailable.
4. Scoped, expiring programmatic access tokens (PATs) for supported programmatic cases.

[Authentication overview](https://docs.snowflake.com/en/user-guide/security-authentication-overview)

- Use preferred `<organization>-<account>` identifiers in new configuration. Legacy locator/host forms still exist but are easier to misroute across organizations/regions. [Account identifiers](https://docs.snowflake.com/en/user-guide/admin-account-identifier)
- Service/service-agent users cannot use every human authentication method. Choose the correct `TYPE` and current supported auth mechanisms.
- WIF audience and subject mappings are security boundaries. A shared audience can enable unintended cross-account token reuse; scope custom OIDC/SPIFFE audiences to the account/workload contract. [WIF](https://docs.snowflake.com/en/user-guide/workload-identity-federation)
- Current named key-pair management supports restrictions, expiry, and rotation grace. Prefer it over teaching only the legacy two raw RSA public-key properties. [Key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- PATs are expiring credentials subject to role, authentication, and network policies. A role-restricted PAT does not inherit arbitrary secondary-role behavior. [Programmatic access tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- OAuth sessions are often single-role and may reject `USE ROLE` unless the integration/token grants supported role selection. WIF does not universally forbid role switching. Connect with the intended role and diagnose the actual auth/session policy. [OAuth](https://docs.snowflake.com/en/user-guide/oauth-intro)
- Never print private keys, tokens, connection secrets, or decrypted credentials while verifying configuration. Query only key names/metadata when comparing secret sets.

## UDFs, stored procedures, and Snowflake Scripting

Choose by execution contract:

- A UDF is used in an expression and must be side-effect-free under its language/runtime rules.
- A stored procedure is invoked with `CALL` and can orchestrate statements/side effects.
- Snowflake Scripting provides SQL-language blocks, variables, cursors, exceptions, and async child jobs with its own delimiter/client requirements.

[Procedures versus UDFs](https://docs.snowflake.com/en/developer-guide/stored-procedures-vs-udfs), [Snowflake Scripting](https://docs.snowflake.com/en/sql-reference-snowflake-scripting)

Important differences:

- SQL UDF declared `NUMBER` precision/scale and `VARCHAR` length are not enforced as return-contract refinements in the way an agent may expect.
- SQL UDFs cannot perform DML/DDL and cannot use `IDENTIFIER(argument)` to dynamically select arbitrary objects. Use a suitable stored procedure/reference mechanism instead. [SQL UDF limitations](https://docs.snowflake.com/en/developer-guide/udf/sql/udf-sql-limitations)
- Owner-rights procedures use owner privileges but caller/session resources and a documented restricted session context; caller-rights procedures use caller privileges. References can safely delegate selected object access without string-built dynamic SQL. [Procedure rights](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-rights)
- Procedures are not automatically atomic. Explicit transactions must respect scoped-transaction rules, and DDL still commits independently.
- Handler languages have package, runtime version, memory, network, stage/import, logging, and concurrency restrictions. Resolve package/runtime support in the target account, not a public package registry alone.
- Delimit scripting bodies correctly for the client. A block that works in Snowsight may need `$$` delimiters or file execution in CLI/connector contexts. [Running scripting examples](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/running-examples)

## Migration and desired-state semantics

- Design DDL migrations to fix forward. Snowflake cannot roll a DDL batch back as one transaction.
- `CREATE OR REPLACE` atomically replaces metadata by dropping/recreating. Review grants (`COPY GRANTS` where supported), streams/change tracking, load history, task/pipe/service state, policies, and dependent objects.
- `CREATE OR ALTER` is declarative for supported objects and can preserve data/grants/policies better than replacement, but it is not magic migration inference. Omitting a column in a full desired-state table can drop it; a rename can appear as drop/add; some changes can partially apply before failure. Review the exact diff and re-inspect state. [CREATE OR ALTER](https://docs.snowflake.com/en/sql-reference/sql/create-or-alter)
- Use explicit `ALTER ... RENAME` for intended renames. Do not expect Terraform/DCM/another reconciler to infer identity from similar definitions.
- DCM Projects offer a Snowflake-native plan/deploy/test workflow. Terraform and Snowflake's object APIs are valid alternatives; pin provider/library versions and review migration notes. [DevOps with Snowflake](https://docs.snowflake.com/en/developer-guide/builders/devops-with-snowflake), [DCM Projects](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-overview)
- `EXECUTE IMMEDIATE FROM` and Git repository clones can run reviewed staged repository SQL, but templating, file inclusion, privileges, and transaction behavior still need explicit control.
- Keep environment differences in configuration and secrets, not divergent hand-edited SQL artifacts.

## Deployment shape

1. Plan target state and identify destructive/replacing operations.
2. Set a structured deployment `QUERY_TAG` and capture the execution context.
3. Compile/read-only validate expressions/source queries first.
4. Execute one independently recoverable DDL step at a time unless the client/transaction contract is intentionally tested.
5. Preserve every query ID/statement handle and stop on an unexpected partial state.
6. Verify with the narrowest `SHOW`, `DESCRIBE`, `GET_DDL`, grant, history, or service-state query.
7. Exercise the deployed object through the real client/default role, not only an owner worksheet.
8. Check warehouse/serverless/service cost and error telemetry after the first real run.
