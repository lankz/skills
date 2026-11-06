# Snowflake SQL dialect

Use this reference for SQL that Snowflake compiles. It records high-value differences, not general SQL syntax. Check the live [SQL reference index](https://docs.snowflake.com/en/sql-reference) for exact grammar.

## Identifiers and resolution

- Unquoted identifiers are stored and resolved in uppercase. Double-quoted identifiers preserve exact characters and case and must subsequently be quoted exactly. A dot inside quotes belongs to the identifier; it is not a qualification separator. [Identifier requirements](https://docs.snowflake.com/en/sql-reference/identifiers-syntax)
- Avoid introducing quoted mixed-case identifiers unless interoperability requires them. Changing `QUOTED_IDENTIFIERS_IGNORE_CASE` after such objects exist can make them unresolvable.
- Fully qualified object names are `database.schema.object`. Unqualified work depends on session context and, in some query contexts, `SEARCH_PATH`. `CREATE DATABASE` and `CREATE SCHEMA` also change current context; switching databases resets the current schema to `PUBLIC`. Avoid the shorthand `database..object`. [Name resolution](https://docs.snowflake.com/en/sql-reference/name-resolution)
- Bind values and identify objects separately. `IDENTIFIER(?)`, `IDENTIFIER($session_variable)`, and `TABLE(?)` let values supplied through supported bind/session mechanisms stand for object names. Do not quote the placeholder into a string or concatenate untrusted input. [Identifier literals](https://docs.snowflake.com/en/sql-reference/identifier-literal), [bind variables](https://docs.snowflake.com/en/sql-reference/bind-variables)
- `SHOW` and `DESCRIBE` output column names are lowercase. Quote them when consuming the result through `RESULT_SCAN` or the pipe operator.

## Numeric, string, Boolean, and binary types

- `NUMBER`, `DECIMAL`, and `NUMERIC` are fixed-point synonyms. Integer aliases such as `INT` are implemented as `NUMBER(38,0)`. Choose precision/scale for the data contract, not storage tuning. [Numeric types](https://docs.snowflake.com/en/sql-reference/data-types-numeric)
- `FLOAT`, `REAL`, and `DOUBLE` are floating-point aliases; requested precision is not preserved as a distinct floating type. Do not use binary floating point for exact money or equality-sensitive values.
- `VARCHAR`, `STRING`, and `TEXT` are synonyms. A declared maximum length is a contract, not a performance optimization; length is in characters while storage limits are byte-based. [Text types](https://docs.snowflake.com/en/sql-reference/data-types-text)
- Snowflake `BOOLEAN` accepts documented string and numeric conversions, but implicit conversions are narrower. Make application boundaries explicit with `TO_BOOLEAN`/`TRY_TO_BOOLEAN`.
- Binary values are not strings. Use binary conversion functions and format arguments (`HEX`, `BASE64`, `UTF-8`) deliberately rather than relying on a display representation.

## Semi-structured and structured data

- `VARIANT`, `OBJECT`, and `ARRAY` can hold semi-structured values; structured `OBJECT(...)`, `ARRAY(...)`, and `MAP(...)` carry element/field types and have different cast and mutation rules. Confirm which family an expression returns. [Semi-structured types](https://docs.snowflake.com/en/sql-reference/data-types-semistructured), [structured types](https://docs.snowflake.com/en/sql-reference/data-types-structured)
- SQL `NULL` and JSON `null` are different. `PARSE_JSON('null')` produces a `VARIANT` value with type `NULL_VALUE`; test it with `IS_NULL_VALUE` or `TYPEOF`. `OBJECT_CONSTRUCT` omits pairs containing SQL `NULL` but retains JSON null. [PARSE_JSON](https://docs.snowflake.com/en/sql-reference/functions/parse_json), [IS_NULL_VALUE](https://docs.snowflake.com/en/sql-reference/functions/is_null_value)
- `TO_VARIANT('{"a":1}')` stores a string; it does not parse JSON. Use `PARSE_JSON`/`TRY_PARSE_JSON` for JSON text and `TO_VARIANT` when wrapping an already typed scalar.
- Path traversal such as `payload:key` returns `VARIANT`. Cast at the boundary: `payload:key::STRING`, `AS_NUMBER(payload:key)`, and so on. JSON keys are case-sensitive even when the SQL column identifier is not. [Querying semi-structured data](https://docs.snowflake.com/en/user-guide/querying-semistructured)
- `AS_<type>` extracts only when the `VARIANT` already contains that compatible type and otherwise returns `NULL`; `TO_<type>` converts/coerces; `TRY_TO_<type>` catches conversion errors only for the documented conversion family. There is no reliable rule that every `TO_*` has a `TRY_TO_*`. The conversion catalog does not document `TRY_TO_VARCHAR`; prefer `AS_VARCHAR` for a known string variant or `TO_VARCHAR` for general stringification and compile-test if existing code uses the undocumented spelling. [Conversion functions](https://docs.snowflake.com/en/sql-reference/functions-conversion)
- `FLATTEN` is a table function returning `SEQ`, `KEY`, `PATH`, `INDEX`, `VALUE`, and `THIS`. Its `SEQ` is not ordered or gap-free. Use a lateral/comma form when correlating to the left-hand row; built-in table functions restrict `ON`, `USING`, and `NATURAL` join syntax. [FLATTEN](https://docs.snowflake.com/en/sql-reference/functions/flatten), [LATERAL](https://docs.snowflake.com/en/sql-reference/constructs/join-lateral)

## Dates, times, and timestamps

- Use explicit timestamp variants in durable schemas. `TIMESTAMP` maps according to `TIMESTAMP_TYPE_MAPPING` and defaults to `TIMESTAMP_NTZ`; assuming it means UTC or local time is unsafe. [Date/time types](https://docs.snowflake.com/en/sql-reference/data-types-datetime)
- `TIMESTAMP_LTZ` stores a UTC instant and displays in the session time zone. `TIMESTAMP_NTZ` is wall-clock data without zone semantics. `TIMESTAMP_TZ` stores an instant plus numeric offset, not an IANA zone identity; later date arithmetic can retain an offset that is wrong after a DST transition.
- For numeric epochs, specify scale: `TO_TIMESTAMP(value, 0|3|6|9)` for seconds, milliseconds, microseconds, or nanoseconds. Integer strings use a magnitude heuristic and can interpret rows in different units. An integer inside `VARIANT` can also take an indirect time-zone-sensitive conversion path; cast it to integer before timestamp conversion. [TO_TIMESTAMP](https://docs.snowflake.com/en/sql-reference/functions/to_timestamp)
- `DATEDIFF(part, start, end)` returns `end - start` in the requested unit and compares only the relevant fields. The minus operator works only for dates and returns days. Week behavior depends on session parameters. [Date/time functions](https://docs.snowflake.com/en/sql-reference/functions-date-time)
- `CONVERT_TIMEZONE` has distinct two-argument and three-argument forms. Use IANA zone names exactly as documented; most abbreviations are unsupported or ambiguous. [CONVERT_TIMEZONE](https://docs.snowflake.com/en/sql-reference/functions/convert_timezone)
- Input/output formats and `TIMEZONE` are session parameters. Pin formats at external boundaries rather than depending on account/session defaults.

## Function names and predicate semantics

Do not manufacture a Snowflake function because another dialect has a plausible name. High-value spellings and behaviors include:

| Need | Snowflake contract |
|---|---|
| Suffix test | `ENDSWITH(expr, suffix)`, not `ENDS_WITH` |
| String length | `LENGTH(expr)` or `LEN(expr)`; do not rely on `CHAR_LENGTH` |
| Null-safe equality | `IS [NOT] DISTINCT FROM` or `EQUAL_NULL` |
| Conditional expression | `IFF(condition, true_value, false_value)` for two branches; `CASE` for general branching |
| Safe division | `DIV0` returns zero on a zero divisor; `DIV0NULL` also treats a null divisor as zero |
| Conditional count | `COUNT_IF(condition)` |
| Null/zero transforms | `ZEROIFNULL`, `NULLIFZERO`, `NVL`/`IFNULL`, and `COALESCE` have documented coercion behavior |
| Cancel query | `SYSTEM$CANCEL_QUERY('<query-id>')` |
| Inspect type | `TYPEOF`, `IS_<type>`, and `AS_<type>` for semi-structured values |

Sources: [string functions](https://docs.snowflake.com/en/sql-reference/functions-string), [conditional expressions](https://docs.snowflake.com/en/sql-reference/expressions-conditional), [system functions](https://docs.snowflake.com/en/sql-reference/functions-system).

- `ILIKE` and `RLIKE`/`REGEXP` match the entire subject. Use `%...%` for an `ILIKE` substring and `.*...*` for a regex substring. Backslashes in single-quoted SQL regex strings must be doubled. [ILIKE](https://docs.snowflake.com/en/sql-reference/functions/ilike), [RLIKE](https://docs.snowflake.com/en/sql-reference/functions/rlike)
- Collation support is function- and expression-specific. Do not assume every comparison, regex, semi-structured function, or search feature accepts the same collation.

## Snowflake query constructs worth choosing deliberately

- `QUALIFY` filters after window functions and before `DISTINCT`, `ORDER BY`, and `LIMIT`. It can reference a SELECT alias and requires a window function in the SELECT list or predicate. It is a reserved, non-ANSI keyword. [QUALIFY](https://docs.snowflake.com/en/sql-reference/constructs/qualify)
- `SELECT * EXCLUDE (...) REPLACE (...) RENAME (...)`, `GROUP BY ALL`, `UNION BY NAME`, `PIVOT ... ANY`, `ASOF JOIN`, `MATCH_RECOGNIZE`, and the pipe operator (`->>`) can replace verbose generated SQL, but each has ordering and eligibility rules. Confirm the current [query syntax](https://docs.snowflake.com/en/sql-reference/constructs) before generating them.
- Mixed set operations need parentheses. `INTERSECT` binds before `UNION` and `EXCEPT`/`MINUS`; the latter operators share precedence. `UNION BY NAME` matches unquoted names case-insensitively and quoted names case-sensitively and fills missing columns with `NULL`. [Set operators](https://docs.snowflake.com/en/sql-reference/operators-query)
- `GENERATOR` requires constant `ROWCOUNT`/`TIMELIMIT`. A time-limited generator is machine-speed-dependent, and `SEQ*` can have gaps. Use `ROW_NUMBER` when a stable gap-free sequence within a result is required. [GENERATOR](https://docs.snowflake.com/en/sql-reference/functions/generator)
- Sampling a joined result occurs after the join and does not reduce join work. Seeded repeatability applies to `SYSTEM`/`BLOCK` sampling on an unchanged table; even a clone can produce a different sample. [SAMPLE](https://docs.snowflake.com/en/sql-reference/constructs/sample)

## `VALUES`, DML, and deterministic writes

- A query `VALUES` clause accepts constants and compile-time constant expressions, not arbitrary function calls. Parse or convert in an outer projection:

```sql
INSERT INTO events (id, payload)
SELECT column1, PARSE_JSON(column2)
FROM VALUES (1, '{"status":"ready"}'), (2, '{"status":"done"}');
```

Rows are coerced to common column types and can overflow when mixed numeric scales/ranges are inferred. [VALUES](https://docs.snowflake.com/en/sql-reference/constructs/values)

- Multiple source rows matching one target row make `MERGE` nondeterministic. `ERROR_ON_NONDETERMINISTIC_MERGE` defaults to `TRUE`, so ambiguous updates/deletes normally error. Deduplicate or aggregate the source to one row per target key. [MERGE](https://docs.snowflake.com/en/sql-reference/sql/merge)
- `UPDATE ... FROM` has the same multiple-match hazard, but `ERROR_ON_NONDETERMINISTIC_UPDATE` defaults to `FALSE`; Snowflake may silently choose one source row. Make the source unique or enable the error while validating. [UPDATE](https://docs.snowflake.com/en/sql-reference/sql/update)
- `CREATE OR REPLACE` drops and recreates an object atomically at the metadata level; it is not an in-place update. Review effects on grants, streams, change tracking, load history, service availability, and dependent objects. Prefer supported explicit `ALTER` or `CREATE OR ALTER` operations when their reconciliation semantics are acceptable.
- Inline column comments use `<type> COMMENT 'text'`, not `COMMENT = 'text'`. Change an existing column comment with `COMMENT ON COLUMN ... IS ...`. [COMMENT](https://docs.snowflake.com/en/sql-reference/sql/comment)

## Transactions and constraints

- DML obeys explicit transactions and `AUTOCOMMIT`. DDL does not: every DDL statement implicitly commits an active transaction before running and executes in its own transaction. CTAS is DDL. Snowflake has no nested transactions. [Transactions](https://docs.snowflake.com/en/sql-reference/transactions)
- Threads sharing a connection share one session and transaction state. A commit, rollback, context change, or query-ID lookup from one thread can affect another.
- Stored procedures are not automatically atomic. Explicit transaction scope must remain within the same procedure/transaction owner; do not start a transaction in one scope and finish it in another.
- On standard tables, `PRIMARY KEY`, `FOREIGN KEY`, and `UNIQUE` constraints are informational; `NOT NULL` is enforced. Current documentation states that `CHECK` constraints are enforced on standard and Snowflake-managed Iceberg tables. Hybrid tables enforce PK/FK/UNIQUE and require a primary key. Confirm table kind before trusting a constraint. [Constraint overview](https://docs.snowflake.com/en/sql-reference/constraints-overview)

## Sequences

- Snowflake sequences have no `CURRVAL`. Every textual occurrence of `sequence.NEXTVAL` can generate a different value, including two occurrences in the same row.
- Alias a generated value in a nested query or use `TABLE(GETNEXTVAL(sequence))` when the same value must feed multiple columns. Sequences can have gaps and are not reliable ordering mechanisms. [Sequence semantics](https://docs.snowflake.com/en/user-guide/querying-sequences)

## Time Travel and persisted results

- `AT` includes changes made by the specified statement/transaction; `BEFORE` means the instant immediately before it completed. Historical queries use the object's current schema and the caller's current privileges. Put `AT`/`BEFORE` on base objects, not a CTE result. [AT | BEFORE](https://docs.snowflake.com/en/sql-reference/constructs/at-before)
- Persisted result reuse (up to 24 hours) is separate from warehouse-local cache. Reuse requires effectively identical query text plus unchanged data, configuration, privileges, and deterministic behavior; it is never guaranteed. Even case or alias changes can prevent reuse. [Persisted results](https://docs.snowflake.com/en/user-guide/querying-persisted-results)
- `RESULT_SCAN` can consume a previous result but does not guarantee row order and does not retain all table metadata. Prefer the pipe operator when it expresses a direct post-processing chain, and apply a final `ORDER BY` when order matters. [RESULT_SCAN](https://docs.snowflake.com/en/sql-reference/functions/result_scan)
