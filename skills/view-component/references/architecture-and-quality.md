# Architecture, refactoring, and UI quality

Use this explanation when deciding whether to create a component, drawing boundaries, reviewing an existing component, or improving interface quality.

## What ViewComponent changes

A ViewComponent is a Ruby object that encapsulates markup behind an explicit initializer. It gives view code:

- a named responsibility;
- an inspectable data contract;
- ordinary Ruby methods and linting;
- isolated rendered-output tests;
- a reusable place for design, behavior, and accessibility improvements.

At boot, ViewComponent compiles templates into component instance methods. Instantiation runs only the component initializer. At render time Rails passes an `ActionView::Context` to `render_in`; this is when helpers, request, controller, and rendering facilities become available. Treat compiler-generated `_call_*` methods as internals.

Version 4 is described as Long-Term Support and feature-complete. Prefer established supported composition patterns to framework-level cleverness.

## When a component earns its existence

Strong candidates are:

- markup reused across locations;
- an existing partial with significant Ruby or conditional behavior;
- a UI state machine with enough permutations to deserve focused tests;
- a design-system primitive whose semantics, styling, or behavior must remain consistent;
- an application-specific presenter that maps domain state into one or more primitives.

Weak candidates are:

- trivial, page-specific markup with no meaningful logic or testing value;
- a speculative abstraction designed before a repeated pattern exists;
- an entire route extracted only to replace one conventional template;
- a component whose initializer becomes a bag of unrelated page state.

A whole-route component can be justified when many user-visible permutations benefit from unit tests. Migrate such routes bottom-up: extract coherent regions first, then decide whether the remaining route shell has value as a component.

Componentization often exposes an existing view's hidden dependencies through a large initializer. Treat that as diagnostic evidence. Reduce responsibility, compose smaller components, or create a presentation object rather than hiding the complexity again.

## Two component roles

### General-purpose components

These represent reusable visual or interaction patterns such as buttons, alerts, form controls, menus, tables, modals, and avatars. Their contract should use presentation concepts rather than application models.

### Application-specific components

These accept domain data such as an Active Record object, API response, or PORO and translate it into general-purpose components. For example, `Users::AvatarComponent` might accept a user and render `DesignSystem::AvatarComponent` with explicit `src`, `alt`, and size values.

Keep the direction one-way:

```text
domain data → application-specific component → general-purpose components → semantic HTML
```

Do not make a general-purpose primitive query or understand application models.

## Extract from evidence

The upstream best-practice sequence is:

1. Implement one concrete use case cleanly.
2. Adapt it after multiple application locations demonstrate a shared pattern.
3. Extract the stable general-purpose primitive into a shared library or gem only when that boundary is proven.

The documentation suggests normal DRY pressure at roughly three similar instances. This is a heuristic, not a quota. Accessibility or correctness may justify centralization earlier; superficial similarity may never justify it.

Every component adds an API and maintenance surface. Avoid one-offs that do not buy cohesion, consistency, or testing value.

## Name and namespace by output

- End class names with `Component`.
- Store normal application components under `app/components` unless project configuration says otherwise.
- Use plural module namespaces, like controllers and jobs: `Users::AvatarComponent`.
- Name the component for what it renders, not the object it happens to accept: prefer `AvatarComponent` to `UserComponent`.
- Let the initializer describe data dependencies; do not encode all possible inputs into the class name.

## Prefer composition

Avoid ViewComponent template inheritance as a routine reuse mechanism. Parent and child templates make control flow and variants harder to understand. Compose components and slots instead.

Template inheritance and `render_parent` are supported, but use them only when the subtype relationship and shared template contract are real. Do not build a deep hierarchy to share utilities; put shared non-rendering behavior in narrowly scoped modules or plain Ruby collaborators, while remembering that included modules are not automatically part of experimental cache digests.

## Explicit data flow

- Use keyword arguments for nontrivial contracts.
- Pass data rather than reaching into `params`, `request`, current URL, or controller state.
- Normalize arrays, booleans, enums, and optional values once at the boundary.
- Reject invalid closed-set options early rather than silently generating broken classes or ARIA states.
- Avoid passing pre-rendered HTML strings. Use main content or slots so Rails' capture and escaping rules apply.
- Preload associations and perform authorization outside the component. A render should not trigger data-access surprises.
- Keep request-dependent values explicit when a component must work in controllers, previews, background jobs, mailers, or Turbo broadcasts.

Use `helpers`, `controller`, and `request` sparingly. Access to them is available for integration, not a substitute for a clear contract.

## Keep templates readable

Templates should expose structure and content order. Move these concerns to private methods when they obscure that structure:

- class selection and state mappings;
- display formatting;
- nontrivial predicates;
- safe attribute construction;
- selection of child components.

Do not remove all conditionals mechanically. Small markup-local decisions are often clearest in the template. The test is whether a reader can understand the rendered structure without mentally executing a program.

Most methods used only by the component template can be private; ViewComponent templates can still call them. Keep public methods for the actual caller/framework contract, including `call` and `call_VARIANT`.

## UI quality is a separate contract

ViewComponent supplies encapsulation and rendering mechanics; it does not choose accessible semantics or good product design. Apply the application's design system and verify the following as relevant.

### Semantics and accessibility

- Use native elements before ARIA emulation: button, link, heading, list, table, dialog, input, label, and fieldset semantics should match the interaction.
- Give icon-only controls an accessible name and hide decorative icons from assistive technology.
- Connect labels, hints, validation errors, headings, controls, and panels with stable IDs and the correct `for`, `aria-describedby`, `aria-labelledby`, or control relationships.
- Expose state such as expanded, selected, pressed, checked, current, invalid, busy, or disabled accurately.
- Keep DOM order meaningful and heading levels coherent.
- Do not communicate status through color or icon shape alone.
- Preserve escaping. Never turn arbitrary caller values into `html_safe` markup.

### Interaction

- Use the expected keyboard model for the pattern.
- Make focus visible and intentionally place/restore it when overlays or dynamic regions open and close.
- Distinguish disabled behavior from merely muted styling.
- Ensure loading states prevent duplicate actions without trapping users.
- Respect reduced-motion preferences and avoid motion that carries essential meaning by itself.
- Use browser/system tests for JavaScript, focus, and keyboard behavior rather than pretending a fragment test proves them.

### Content and layout

- Exercise empty, short, long, localized, multiline, and overflow content.
- Verify narrow and wide containers rather than only one viewport.
- Check light/dark and high-contrast themes supported by the app.
- Use local tokens and shared component classes, not isolated magic values.
- Preserve server-rendered usefulness and progressive enhancement where the application's interaction model allows it.

### State modelling

Prefer a small, valid state space. Boolean option growth produces invalid permutations. Use:

- one enum for mutually exclusive variants;
- a slot for caller-owned content;
- a polymorphic slot for one region with several renderer types;
- separate components when behavior or semantics genuinely diverge.

Previews should make meaningful states visible. Tests should assert stable user-observable contracts, not every utility class.

## Resolve common design conflicts

| Conflict | Better boundary |
|---|---|
| Component reads `current_user`, `params`, or helpers in `initialize` | Pass prepared data explicitly; use `before_render` only for unavoidable render-context work |
| Caller passes `html_safe` markup through an initializer | Use main content, a slot, or a child component |
| Component needs caller content and also declares `cache_on` | Remove self-caching, use an external fragment cache, or split out a fully component-owned cacheable child |
| One component instance is rendered in multiple places | Construct a fresh instance at every render site |
| Many booleans represent mutually exclusive visual states | Use a finite variant or polymorphic slot, or split divergent components |
| A list of ordinary links is implemented as an ARIA menu | Prefer a native disclosure/details pattern; reserve `role="menu"` for application-style commands with the full menu keyboard model |

A disclosure containing links normally keeps native link keyboard behavior. A true ARIA menu requires managed focus, arrow-key navigation, Home/End behavior, Escape handling, correct `menuitem` roles, and focus return. Choose from the interaction users expect, not from the visual appearance of an overflow panel.

## Refactor an existing view safely

1. Capture the current output and behavior with focused tests or screenshots where appropriate.
2. Identify the smallest coherent region with repeated or stateful behavior.
3. Move its explicit data dependencies into a component initializer.
4. Move template calculations and conditionals into private methods without redesigning everything at once.
5. Introduce child/general-purpose components only where repetition or a strong semantic boundary is now visible.
6. Add previews for the important states and rendered-output tests for the public contract.
7. Replace callers incrementally.
8. Remove the old helper/partial only after all callers have moved.

This preserves the useful lesson from the upstream Jellyswitch case study: a component can be a refactoring seam before it becomes an elegant abstraction. Do not copy that historical Bootstrap/UJS switch example as modern UI; it lacks current semantic switch behavior, accessible naming, keyboard/focus guidance, and clean markup.

## Review checklist

- Does this component have one responsibility and a name based on its output?
- Is it general-purpose or application-specific, and is that boundary clear?
- Are inputs explicit, minimal, normalized, and valid?
- Does the component avoid queries, implicit global state, and controller coupling?
- Is caller markup represented by content or slots?
- Is composition used instead of inheritance and boolean permutations?
- Is the template readable, with supporting methods private?
- Are semantics, accessible names, relationships, states, keyboard behavior, and focus correct?
- Do preview scenarios expose realistic edge states?
- Do component tests assert rendered behavior and system tests cover interaction?
- Does the change reuse and update the local design system and its documentation?
