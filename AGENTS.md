[always] Keep one canonical skill tree
Author every distributable skill under `skills/<skill-name>/`. Plugin manifests and marketplaces must point to that tree rather than maintaining provider-specific copies.

[always] Preserve source provenance
Document the authoritative sources and version baseline inside each skill when its guidance is synthesized from upstream documentation. Keep licensing and third-party notices accurate as skills evolve.

[always] Synchronize distribution metadata
Keep Claude and Codex plugin names and semantic versions aligned. Update installation documentation and the changelog when a release changes a public skill contract.

[never] Do not commit installed skill copies
Do not commit agent-local installations, lockfiles, secrets, or generated provider copies. The repository files under `skills/` are the source of truth.

[verify] Validate before committing
Run `scripts/validate` after changing repository structure, manifests, marketplaces, or skills. When skills exist, also confirm that the pinned skills CLI discovers them.
