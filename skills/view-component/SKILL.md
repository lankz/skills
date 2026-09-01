---
name: view-component
description: Create, migrate to, refactor, review, test, preview, and troubleshoot Rails interfaces built with the ViewComponent gem. Use for ViewComponent::Base, component templates, slots, collections, lifecycle hooks, previews, caching, Turbo Streams, generators, configuration, component architecture, or ViewComponent adoption.
---

# Rails ViewComponent

Build cohesive, accessible Rails UI with explicit component contracts and rendered-output verification. Apply the installed ViewComponent version and the application's design system rather than assuming that every renderable Ruby object implements ViewComponent's API.

## Start with the actual contract

1. Read every applicable `AGENTS.md` and nearby component or design-system documentation.
2. Identify the implementation before proposing or editing anything:
   - Search dependency manifests and lockfiles for `view_component`.
   - Inspect the component's superclass and base class.
   - Inspect existing generators, configuration, neighboring components, previews, and tests.
   - Record the installed gem version. Do not use a newer API without confirming it exists locally.
3. For adoption or conversion work, read [references/migration.md](references/migration.md) before designing the target contract.
4. Define the component's responsibility, inputs, caller-provided regions, output states, interaction states, and accessibility contract before choosing APIs.

## Route to the relevant guidance

Read only the references the task needs:

- First implementation or unfamiliar codebase: [references/tutorial.md](references/tutorial.md)
- Migration from partials, helpers, presenters, or custom renderables: [references/migration.md](references/migration.md)
- Selection, boundaries, architecture, refactoring, and UI quality: [references/architecture-and-quality.md](references/architecture-and-quality.md)
- Initializers, content, templates, lifecycle, conditional rendering, helpers, translations, and render contexts: [references/authoring.md](references/authoring.md)
- Slots, component composition, polymorphism, and collections: [references/composition.md](references/composition.md)
- Unit tests, request context, previews, interaction tests, and state coverage: [references/testing-and-previews.md](references/testing-and-previews.md)
- Generators, configuration, compatibility, instrumentation, caching, and Turbo Streams: [references/advanced-operations.md](references/advanced-operations.md)
- Exact public methods, test helpers, configuration keys, and error diagnoses: [references/api-reference.md](references/api-reference.md)
- Source version, official-document coverage, upstream errata, and optional ecosystem links: [references/upstream-source-map.md](references/upstream-source-map.md)

## Implementation posture

- Prefer a component when markup is reused, has meaningful permutations, or benefits from isolated tests. Do not create a speculative one-off abstraction merely because markup exists.
- Use explicit keyword inputs. Normalize and validate at the initializer boundary; do not hide required data in `params`, controller state, or ambient helpers.
- Keep initialization independent of the view context. Use `before_render` only for work that truly needs helpers, request, or controller context.
- Separate general-purpose design-system primitives from application-specific adapters. Let domain-facing components compose primitives.
- Prefer composition to component inheritance. Use slots for caller-owned markup instead of `html_safe` strings.
- Keep templates declarative: semantic markup and straightforward rendering belong there; branching, formatting, and class decisions usually belong in private component methods.
- Never reuse a rendered component instance. Instantiate a new component for every render.
- During migration, preserve output and caller behavior first, convert leaf components before shared shells, and remove the old abstraction only after every caller has moved.
- Prepare collections outside the view, preload associations, and use `with_collection` for repeated rendering. A component must not create N+1 queries or perform row-by-row data access.
- Treat previews as a state catalogue and tests as the executable contract. Assert rendered behavior, not mostly-private implementation methods.
- Treat experimental caching and asynchronous serialization as opt-in, version-sensitive features. A component declaring `cache_on` cannot accept a render block, `with_content`, or caller-populated slots; remove self-caching, use an external fragment cache, or split the component rather than weakening that boundary.

## High-quality UI completion standard

A mechanically valid component is not automatically a good interface. Before finishing:

- Reuse local design-system components, tokens, icons, form controls, and interaction conventions.
- Use the correct semantic element and preserve accessible names, labels, descriptions, roles, relationships, and state attributes.
- Verify keyboard operation, focus behavior, disabled and loading behavior, error communication, reduced motion, localization expansion, responsive layout, and dark/high-contrast themes when applicable.
- Cover meaningful states such as default, empty, long content, overflow, selected, disabled, loading, success, validation error, and permission-restricted states. Do not invent irrelevant permutations.
- Unit-test stable structure and visible behavior; use a browser/system test for JavaScript or focus behavior; visually inspect representative preview states when layout changed.
- Update the smallest relevant component/design documentation if the public render contract changed.

## Version baseline

The bundled references synthesize the complete in-scope official documentation for ViewComponent 4.15.0 at upstream commit `2e6e02d516b645c545eeecb021367047b69a6201` (2026-08-25). They correct several obvious documentation defects but do not override the installed gem. When local behavior or a later official release differs, prefer the local locked version and its source/tests, then update this skill deliberately.
