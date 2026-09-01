# Migrate to ViewComponent

Use this guide when replacing partials, HTML-generating helpers, presenters, or a custom Rails-renderable component system with `ViewComponent::Base`.

## Migration outcome

A successful migration leaves:

- one explicit `ApplicationComponent < ViewComponent::Base` foundation;
- generator, preview, test, and component paths aligned with the application;
- public component contracts expressed through initializers, main content, and named slots;
- rendered output and behavior preserved or deliberately improved;
- fast component tests and representative previews;
- no caller still depending on the retired partial/helper/custom base before it is removed.

Do not imitate a previous component DSL with compatibility shims unless a staged migration genuinely requires them. Prefer a clear temporary adapter with an explicit removal condition to a permanent hybrid API.

## 1. Establish the baseline

Before adding the gem or changing callers, inventory only the contracts relevant to the migration slice:

- current render call shape;
- class/partial/template locations;
- initializer or partial locals;
- block/captured-content behavior;
- named or repeated regions;
- helper, request, controller, and global-state dependencies;
- tests, previews/catalogues, JavaScript controllers, styles, locale files, and design documentation;
- all call sites for the component being migrated.

Capture meaningful output and interaction behavior with focused tests. For risky visual work, keep representative screenshots or preview states as comparison evidence.

Avoid a whole-codebase abstraction audit unless the migration itself is repository-wide.

## 2. Add and configure ViewComponent deliberately

Confirm Ruby/Rails compatibility, add the intended locked gem version, and define a base class:

```ruby
class ApplicationComponent < ViewComponent::Base
end
```

Choose generator defaults once:

- component path and eager-load behavior;
- test framework;
- template handler;
- sibling or sidecar layout;
- preview path/layout;
- optional locale and Stimulus sidecars;
- `generate.parent_class = "ApplicationComponent"` when explicit configuration is useful.

Verify application boot, eager compilation, autoloading, and a generated disposable component before converting production UI.

Keep the base class small. Do not move every view helper or global context dependency into it; that recreates the implicit coupling migration is meant to remove.

## 3. Pick a migration slice

Start with a leaf component or repeated partial whose dependencies and callers are easy to enumerate. Good first slices have:

- a stable visual responsibility;
- existing tests or easy output assertions;
- limited request/controller coupling;
- no large nested component tree;
- enough reuse or state complexity to demonstrate value.

For a route or large composite view, migrate bottom-up. Convert leaf controls and repeated regions before the page shell.

## 4. Translate the public contract

Map old mechanisms to native ViewComponent APIs:

| Existing mechanism | ViewComponent target |
|---|---|
| Partial locals or presenter constructor | Explicit keyword initializer |
| Main render block | `content` / top-level `with_content` |
| One optional captured region | `renders_one` |
| Repeated captures | `renders_many` |
| Captured child with its own contract | Component slot |
| Mutually exclusive captured types | Polymorphic slot |
| Component-owned fallback region | `default_SLOT_NAME` |
| Manual uniform render loop | `.with_collection` |
| Caller/template visibility condition intrinsic to component | `render?` |
| Helper/slot-dependent setup performed too early | `before_render` |
| HTML-generating helper | A small component template or public `call` |

Do not preserve accidental API shape. A custom `capture_for(:header)` call, for example, normally becomes the generated `with_header` setter rather than a compatibility method with the old name.

Named slots and main content can coexist in one caller block:

```ruby
class MenuComponent < ApplicationComponent
  renders_one :trigger

  def initialize(label:, position:)
    @label = label
    @position = position
  end
end
```

```erb
<%= render MenuComponent.new(label: "Account actions", position: :end) do |menu| %>
  <% menu.with_trigger do %>
    <span aria-hidden="true">•••</span>
  <% end %>

  <% actions.each do |action| %>
    <li><%= link_to action.label, action.path %></li>
  <% end %>
<% end %>
```

Use a non-output ERB tag (`<% ... %>`, not `<%= ... %>`) around the `with_trigger` call because the component template emits the slot later. The remaining captured output becomes the component's main `content`. Repeated DOM children do not automatically require `renders_many`; use a repeating slot only when the component should own each child's contract or the legacy API already captured items individually.

ViewComponent does not make `renders_one` required by declaration. If absence is invalid, check its generated predicate after caller slots exist—normally in `before_render`—and raise a clear contract error, or provide an intentional `default_SLOT_NAME`.

Use explicit route/model/policy inputs instead of porting reads from `params`, current URL, or controller state. Preload data before rendering.

Normalize and validate the target contract, but preserve the legacy accepted values during a parity migration. Narrowing previously valid inputs is a separate behavior change and should be deliberate and tested.

## 5. Move rendering without redesigning everything

First reproduce valid, accessible behavior with the new class/template boundary:

1. Generate or create the component through project conventions.
2. Move inputs into the initializer.
3. Move existing markup to a sibling or sidecar template.
4. Move nontrivial presentation calculations into private methods.
5. Replace caller markup arguments with content or slots.
6. Preserve stable IDs, Turbo targets, Stimulus data attributes, form names, and accessible relationships.
7. Render the new component from one caller.

Make broad visual or interaction improvements in the same slice only when they are requested or necessary for correctness. Separating mechanical migration from redesign makes regressions easier to identify.

For Stimulus-backed components, preserve token-valued `data-controller` and `data-action` attributes, target/value class names, initial DOM state, and controller registration/import behavior. Do not generate or register a duplicate sidecar controller merely because the migrated template already references one.

## 6. Convert tests and previews

Translate partial/helper/custom-renderable tests into `ViewComponent::TestCase` or the project's RSpec component type:

- call `render_inline`;
- populate content and slots through their real public API;
- assert semantic rendered output and visible states;
- use `with_request_url`, `with_controller_class`, `with_variant`, or `with_format` only for context the component still intentionally consumes;
- use `assert_component_rendered` / `refute_component_rendered` for `render?` behavior.

Create preview scenarios for representative states. Reuse them with `render_preview` where that makes tests clearer. Keep browser/system coverage for JavaScript, keyboard, focus, and layout-dependent behavior.

Do not mechanically port tests of old internal readers or capture storage. Test the new public render contract.

## 7. Migrate callers incrementally

Search all call sites and convert them in small batches. For every batch:

- preserve argument and content semantics;
- check HTML escaping and safe-buffer behavior;
- check collection ordering and separators;
- check Turbo/Stimulus targets and DOM IDs;
- run focused component and caller tests;
- inspect previews or pages for representative states.

If a temporary adapter is required, keep it one-directional: old call shape delegates to the new component. Document its remaining callers and removal trigger. Do not make the new component depend on the legacy base.

## 8. Remove legacy code only at zero callers

Before deleting a partial, helper, presenter, custom base method, or compatibility adapter:

1. Search for every static and dynamic call shape.
2. Confirm tests/previews no longer load it.
3. Confirm mailers, Turbo broadcasts, background jobs, and alternate formats/variants are covered.
4. Remove the old files and dead helper methods.
5. Run autoload/eager-load checks so stale constant references fail before deployment.

Update component/design documentation when the supported render contract or examples changed.

## Common migration traps

- Assuming similarly named slot methods from a custom DSL have ViewComponent semantics.
- Using slots in `initialize` even though callers populate them afterward.
- Moving global helper access into `ApplicationComponent` instead of making inputs explicit.
- Reusing one component instance because a previous renderable was reusable.
- Replacing a partial collection with a manual component loop instead of `.with_collection`.
- Adding `cache_on` during migration before proving the component has no caller-owned content.
- Breaking DOM IDs, form field names, Turbo targets, or Stimulus controllers while markup appears visually similar.
- Converting the entire route first and creating a huge initializer.
- Keeping old and new component systems indefinitely without a caller inventory and removal condition.
- Treating preview parity as proof of keyboard/focus behavior.

## Migration verification matrix

| Concern | Verification |
|---|---|
| Contract | Invalid/required inputs and slot combinations have focused tests |
| Output | Semantic selectors and representative content match intended behavior |
| Escaping | Untrusted values remain escaped; caller markup uses capture/slots |
| Data | Queries are preloaded/batched and tenant/authorization scope stays outside rendering |
| Interaction | Browser test covers keyboard, focus, and JavaScript state |
| Visual states | Previews cover meaningful variants and edge content |
| Context | Routes, locale, variant, format, host, and controller dependencies are explicit or tested |
| Loading | Development reload and production eager compilation pass |
| Callers | Search confirms every intended caller migrated before deletion |
| Documentation | Public component/design references match the new API |
