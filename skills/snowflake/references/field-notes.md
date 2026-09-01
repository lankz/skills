# Historical field notes

These historical implementation observations are retained because they can shorten diagnosis, but current official documentation does not establish them as universal Snowflake behavior. Apply them only after the documented contract, exact SQL, role, account, client, and object state have been checked.

Do not cite a field note as a platform restriction in new documentation or code comments. When one reproduces, capture the minimal SQL, query ID, account/region/edition, client version, role, object definitions, and current official source.

## Correlated subquery around `LATERAL FLATTEN`

An analytics insert failed when `LATERAL FLATTEN` was wrapped in a correlated-subquery shape and succeeded after a set-based aggregation rewrite. Current Snowflake documentation supports lateral subqueries and `FLATTEN` generally, so there is no basis for a blanket ban.

If a similar shape fails:

1. Reduce it to the smallest query preserving correlation and table-function placement.
2. Check the [LATERAL](https://docs.snowflake.com/en/sql-reference/constructs/join-lateral) and [FLATTEN](https://docs.snowflake.com/en/sql-reference/functions/flatten) restrictions for the exact join syntax.
3. Try a direct lateral/comma join or materialized set-based intermediate result.
4. Keep the rewrite only when it preserves row multiplicity and null semantics.

## Change tracking on secure views

A rollout could not enable change tracking on secure views containing an equality outer join or `LATERAL FLATTEN`; enabling change tracking on base tables and placing the supported operations directly in incremental dynamic tables worked.

The current dynamic-table support matrix is the authority and does not justify a universal secure-view prohibition. When this reappears, inspect the precise upstream object kind, secure/view definition, change-tracking state, retention, refresh mode/reason, and current [incremental query support](https://docs.snowflake.com/en/user-guide/dynamic-tables/supported-queries).

## Cortex Search over a view that unions dynamic tables

A Cortex Search service failed when its source was a view that unioned dynamic tables, while placing the equivalent `UNION ALL` directly in the Search source succeeded. Official docs permit supported tables/views and current refresh behavior has changed.

Use this as a debugging simplification: inline one view layer to expose the exact materialized source query, then verify incremental eligibility/change tracking—or deliberately select current `FULL` refresh and its cost. Do not make “no view sources” a generated rule.

## Multi-property Cortex Search alteration

Historical generated multiline/multi-property `ALTER CORTEX SEARCH SERVICE` statements hit parsing or reconciliation failures. The current [ALTER reference](https://docs.snowflake.com/en/sql-reference/sql/alter-cortex-search) explicitly supports multiple documented assignments.

One-property statements remain useful for query-ID attribution, retryability, and partial-failure isolation, but are a deployment preference rather than grammar law.

## Single-cluster warehouse scaling policy

An account without multi-cluster support rejected an explicit `SCALING_POLICY = STANDARD` even when cluster counts were one. Current semantics define scaling policy for multi-cluster auto-scaling.

Portable generators should omit multi-cluster-only properties for single-cluster warehouses and check edition/account capability before multi-cluster DDL. Do not infer that the property is universally invalid.

## Role switching in a restricted programmatic session

A restricted workload session rejected `USE ROLE`. Current documentation makes role switching dependent on OAuth/PAT/integration/session policy; WIF alone is not a universal prohibition.

Connect using the intended role, inspect token/integration restrictions, and test role selection through the actual client. Do not rewrite this observation as “workload identity cannot switch roles.”

## Trial-account Cortex availability

Earlier work observed missing embedding functions in a trial. Current Snowflake guidance treats Cortex availability as a broader account enablement/payment, model, region, privilege, and feature issue.

When a documented AI function is unknown, triage canonical versus legacy name, `USE AI FUNCTION(S)`, Snowflake database role, model RBAC, region/cross-region, model lifecycle, and account/trial enablement before changing SQL.
