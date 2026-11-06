# Security, governance, and data lifecycle

Snowflake authorization is object/role based with singular ownership, role hierarchies, primary-role context, database roles, managed-access schemas, and feature-specific owner/default-role execution. Do not import a PostgreSQL superuser or IAM-only mental model.

## Role and ownership model

- Every securable object has exactly one owner role. The primary role creates/owns objects; secondary roles can contribute privileges to many SQL operations but do not become the creator/owner. [Access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- Snowflake has no general superuser bypass. `ACCOUNTADMIN`, security roles, ownership, and `MANAGE GRANTS` have distinct powers and should not be collapsed into “admin.”
- Account roles form account-wide hierarchies and can be activated. Database roles are scoped to one database and must be granted to an account role; they cannot be activated directly or receive account roles.
- Owning a role is not the same as inheriting its privileges. Privilege inheritance follows `GRANT ROLE <child> TO ROLE <parent>`.
- An object privilege normally also requires `USAGE` on its parent database and schema. Diagnose the whole chain rather than repeatedly granting the leaf privilege.
- Direct grants to users interact with secondary-role mode and are harder to reason about. Prefer role-based grants unless the direct-user behavior is intentional.

Before a privilege change, inspect both directions:

```sql
SHOW GRANTS TO ROLE application_role;
SHOW GRANTS OF ROLE application_role;
SHOW FUTURE GRANTS IN SCHEMA app_db.app_schema;
```

## Primary, secondary, default, owner, and caller roles

These are different execution contracts:

- The active primary role controls object creation and some authorization decisions.
- Secondary roles can add privileges in supported session SQL but do not replace the primary role.
- Some APIs/services fall back to a user's default role/warehouse, but supported Snowflake REST APIs can accept `X-Snowflake-Role`/`X-Snowflake-Warehouse` overrides. Headers take precedence when permitted by the user's grants and authentication restrictions.
- Owner-rights procedures/services use object-owner privileges for protected object access, while still depending on caller/session resources such as a warehouse in documented ways.
- Caller-rights procedures use caller privileges and more caller session context.

Record the request headers/defaults and effective role with the failing interface. `CURRENT_ROLE()` in a worksheet does not prove which role a separate REST service used. [REST context](https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/setting-context)

## Managed access, future grants, and ownership transfer

- In a managed-access schema, an object's owner cannot independently grant access to the object; the schema owner or a role with `MANAGE GRANTS` controls grants. [Managed access](https://docs.snowflake.com/en/user-guide/security-access-control-configure)
- Schema-level future grants for an object type take precedence over database-level future grants for that type within the schema; the two levels are not merged.
- Future grants are applied at object creation, not continuously reconciled. Rename/swap/lifecycle operations do not mean they are reapplied.
- Ownership transfer is not an ordinary revoke/grant. Choose `COPY CURRENT GRANTS` or `REVOKE CURRENT GRANTS` deliberately, and inspect outbound grants before/after. [GRANT OWNERSHIP](https://docs.snowflake.com/en/sql-reference/sql/grant-ownership)
- Transferring ownership can suspend tasks, pause pipes, disable automatic refresh, or leave dynamic-table/service refresh unable to access dependencies. Verify both grants and operational state.
- Parent-role ownership does not give authority to re-grant every child role. Inspect role ownership/hierarchy before changing grantors.

## Policies, tags, and governed access

- Masking policies transform column values; row access policies filter rows; aggregation/projection/join policies and tags add separate governance contracts. Confirm supported combinations and evaluation order for the object type. [Governance policies](https://docs.snowflake.com/en/guides-overview-govern)
- A directly assigned policy takes precedence over a tag-based policy of the same type. Tag inheritance and policy references can therefore make the effective policy differ from the nearest visible DDL. [Tag-based policies](https://docs.snowflake.com/en/user-guide/tag-based-policies)
- Policy bodies execute under documented owner/context semantics and can introduce extra object dependencies. Test with representative consumer roles, shared data, and policy context—not only the policy owner.
- `POLICY_CONTEXT` can help simulate/evaluate supported policies without granting the target role ordinary access. Use policy/access history for diagnosis where edition and latency allow.
- Secure views/UDFs reduce information exposure and optimizer leakage but have feature/maintenance restrictions. “Secure” does not make every downstream materialization or sharing path automatically safe.
- Metadata fields can be visible beyond table data paths. Never place secrets, regulated content, or personal data in comments, object names, tags, query tags, service metadata, or request logs.

## Authentication/session restrictions affect authorization

OAuth, programmatic access tokens, WIF, service users, and application/service APIs can constrain role selection differently. A role-restricted token can reject `USE ROLE`; WIF itself does not universally do so. Connect with the intended role and verify the auth mode/session policy instead of encoding a blanket rule. See [tooling-deployment.md](tooling-deployment.md).

## Time Travel and Fail-safe

- Time Travel is automatic version history used by `AT`/`BEFORE`, `UNDROP`, and historical cloning. Retention depends on object type, edition, and configured days. [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel)
- Permanent standard objects normally have one day by default; Enterprise capabilities can allow longer configured retention. Temporary/transient objects support only zero or one day.
- Historical queries use the current object schema and current caller privileges. Column evolution can therefore affect a query over old data.
- Fail-safe is a separate, non-configurable seven-day best-effort recovery service operated by Snowflake after Time Travel. Users cannot query it, and it is not a backup/DR strategy. Temporary and transient tables have no Fail-safe. [Fail-safe](https://docs.snowflake.com/en/user-guide/data-failsafe)
- Retained/deleted micro-partitions consume storage. A short-lived table type can lower Fail-safe cost, but it also lowers recovery protection; make the trade explicit.

## Zero-copy cloning

- A clone initially shares immutable micro-partitions with its source; diverging changes consume additional storage. “Zero copy” is initial storage behavior, not free indefinite duplication. [Cloning](https://docs.snowflake.com/en/user-guide/object-clone)
- A table clone begins with automatic clustering suspended. Inspect/resume intentionally when the clone becomes an active workload.
- Table-only clones can retain foreign-key/sequence references to source objects. Cloning the containing schema/database can redirect references when related objects are cloned together.
- A cloned table does not inherit the source's file load history, so an unchanged staged file can be loaded again.
- Grants, future grants, internal-stage files, tasks, pipes, policies, streams, and child objects have object-specific clone rules. `COPY GRANTS` is not a promise to clone all state.
- Historical clone creation depends on Time Travel retention. Verify the exact `AT`/`BEFORE` point and resulting current object state.

## Sharing and reader accounts

- Secure Data Sharing exposes live read-only provider data without copying it into the consumer account. The provider pays storage; the consumer normally pays its query compute. [Data sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro)
- Only supported secure objects can be shared, and shared-object dependencies/privileges follow sharing-specific rules. Do not expose a normal view and assume its underlying data is share-safe.
- A reader account is provider-created for consumers without Snowflake accounts. It can consume only provider shares, and the provider pays its compute; apply resource monitors and governance accordingly. [Reader accounts](https://docs.snowflake.com/en/user-guide/data-sharing-reader-create)
- Listings, private sharing, cross-region sharing/replication, and clean rooms have different commercial/governance contracts. Choose them intentionally rather than treating them as GRANT variants.

## Replication and failover

- Database replication and account replication cover different object/state sets. Database replication does not reproduce every account-level role, future grant, policy, integration, stage, pipe, or security setting; use account replication/failover groups when the DR scope requires them. [Account replication](https://docs.snowflake.com/en/user-guide/account-replication-intro), [database replication](https://docs.snowflake.com/en/user-guide/db-replication-intro)
- Replication/failover groups have dependency and ordering rules. Replicate policies and shared dependencies before objects that reference them.
- Internal stage files, external integrations, secrets, network policies, task/pipe state, and ownership/grants need explicit support checks and post-refresh verification.
- Replication consumes compute/data transfer even when a refresh fails. Monitor refresh history, progress, bytes, and cost.
- A replicated object being queryable is not proof the environment is failover-ready. Test role access, integrations, tasks/pipes, services, endpoints, and promotion/failback procedures.

## Security change verification

1. Record account, user, primary/default/secondary role, auth mode, and object owner.
2. Inspect current grants in both directions and parent `USAGE`.
3. Identify managed-access, future-grant, policy/tag, share, and owner-rights effects.
4. Apply the smallest grant/ownership/policy change.
5. Re-inspect grants and `GET_DDL`/policy references.
6. Test access as representative consumer/default roles, including a denied path.
7. Verify operational objects (tasks, pipes, dynamic tables, Search) remained runnable.
8. Use access history only with its edition, coverage, and delivery-latency limits in mind.
