# Testing and previews

Use component tests for rendered contracts, previews for discoverable state examples, and browser/system tests for real interaction. Do not make one layer imitate another.

## Testing boundary

- **Component/unit tests:** structural semantics, visible copy, attributes, states, slots, variants, formats, and conditional rendering.
- **Preview scenarios:** named, deterministic examples of meaningful visual states; useful to humans and reusable by tests.
- **System/browser tests:** JavaScript, keyboard operation, focus, overlays, layout-provided assets, and actual visibility changes.
- **Integration tests:** the feature works end to end with routing, persistence, authorization, and surrounding page behavior.

Prefer assertions on output a user or assistive technology observes. Test a private helper directly only when it contains independently meaningful logic that rendered assertions cannot express economically.

## Minitest component test

```ruby
require "test_helper"

class LabelComponentTest < ViewComponent::TestCase
  test "renders the label" do
    render_inline(LabelComponent.new(tone: :success)) { "Saved" }

    assert_component_rendered
    assert_selector ".label.label--success", text: "Saved"
  end
end
```

`render_inline` returns a Nokogiri fragment and, when Capybara is installed, assigns a `Capybara::Node::Simple` to `page`. `assert_selector` matches visible elements by default; pass `visible: false` when a hidden element is intentionally part of the contract.

`rendered_content` exposes the latest HTML output for debugging. Avoid snapshotting entire documents when a few semantic selectors express the contract more clearly.

Without Capybara, query the `render_inline` result through Nokogiri:

```ruby
result = render_inline(LabelComponent.new) { "Saved" }

assert_equal "Saved", result.at_css(".label").text
```

## Test content and slots

Configure a component before rendering:

```ruby
component = CardComponent.new.tap do |card|
  card.with_header { "Account" }
  card.with_action { "Edit" }
end

render_inline(component)

assert_selector "header", text: "Account"
assert_selector ".actions", text: "Edit"
```

Or populate slots through the render block:

```ruby
render_inline(CardComponent.new) do |card|
  card.with_header { "Account" }
end
```

Assert the slot's meaningful wrapper, semantics, order, or absence—not only that an internal slot getter returns a value. Avoid `html_safe` fixture strings; use capture blocks or actual child components.

## Conditional rendering

```ruby
render_inline(ConfirmEmailComponent.new(user: unconfirmed_user))
assert_component_rendered

render_inline(ConfirmEmailComponent.new(user: confirmed_user))
refute_component_rendered
```

Also assert the visible condition when it matters; a render assertion alone does not prove correct content.

## Variants and formats

```ruby
with_variant :phone do
  render_inline(NavigationComponent.new)
  assert_selector "nav[data-layout='compact']"
end
```

```ruby
with_format :json do
  render_inline(StatusComponent.new)
  assert_equal "ok", rendered_json.fetch("status")
end
```

`rendered_json` parses the latest content with `JSON.parse`. Test every supported template variant/format that changes output.

## Controller and request context

The default test controller is `ApplicationController` when it exists, otherwise `ActionController::Base`.

Override for a test class:

```ruby
def vc_test_controller_class
  PublicController
end
```

Or scope one scenario:

```ruby
with_controller_class AuthenticatedController do
  render_inline(AccountMenuComponent.new)
  assert_link "Sign out"
end
```

Accessors:

- `vc_test_controller`: current controller instance.
- `vc_test_request`: current `ActionDispatch::TestRequest`.
- `vc_test_view_context`: current `ActionView::Base`; it resets after each `render_inline`.

For request-dependent URL generation:

```ruby
with_request_url "/products/42?locale=en",
  host: "app.example.com",
  method: "GET",
  protocol: :https do
  render_inline(LanguageLinkComponent.new(locale: :fr))
  assert_link "French"
end
```

Use only the context the component really consumes. If most tests require complex controller/request setup, simplify the component contract by passing values explicitly.

To set an environment header directly, use the documented accessor:

```ruby
vc_test_request.env["HTTP_USER_AGENT"] = "Mozilla/5.0"
```

`render_in_view_context(*args, **kwargs) { ... }` executes a block through `instance_exec` in the test view context and enables the same Capybara assertions. Use it when testing rendering that must occur from inside that context rather than a single component instance.

## RSpec setup

For ordinary component specs:

```ruby
require "view_component/test_helpers"
require "capybara/rspec"

RSpec.configure do |config|
  config.include ViewComponent::TestHelpers, type: :component
  config.include Capybara::RSpecMatchers, type: :component
end
```

The upstream docs show two different system helper modules for different jobs:

- `ViewComponent::SystemSpecHelpers` integrates RSpec feature/system specs.
- `ViewComponent::SystemTestHelpers` provides rendered-component-path helpers when a component spec needs them.

Require `view_component/system_test_helpers` and include only the module used by the local suite; do not merge both snippets blindly.

Generated component specs normally have `render_inline` available:

```ruby
RSpec.describe LabelComponent, type: :component do
  it "renders" do
    render_inline(described_class.new) { "Saved" }
    expect(page).to have_css ".label", text: "Saved"
  end
end
```

For Devise-dependent component specs, upstream guidance includes `Devise::Test::ControllerHelpers` and assigns `@request = vc_test_controller.request` before each component example. Add that only when the component genuinely depends on Devise controller helpers.

## Built-in previews

A preview class inherits `ViewComponent::Preview`; each public method is a scenario:

```ruby
class BannerComponentPreview < ViewComponent::Preview
  def default
    render BannerComponent.new(tone: :info) do
      "Scheduled maintenance starts tonight."
    end
  end

  def dynamic(message: "Preview message", tone: "info")
    render BannerComponent.new(tone: tone.to_sym) do
      message
    end
  end
end
```

Built-in routes default to:

```text
/rails/view_components/banner_component/default
/rails/view_components/banner_component/dynamic?message=Custom
```

Preview method keyword arguments accept URL parameters. Use safe deterministic defaults; validate or constrain values before feeding them into closed-set component inputs.

`ViewComponent::Preview` includes `ActionView::Helpers::TagHelper`, so `tag` and `content_tag` are available.

Optional catalogue tools such as Lookbook and ViewComponent::Storybook are not core APIs. Use them only when installed.

## Preview layouts, paths, and routes

Set a layout for one preview class:

```ruby
class BannerComponentPreview < ViewComponent::Preview
  layout "admin"
end
```

Global configuration:

```ruby
config.view_component.previews.default_layout = "component_preview"
config.view_component.previews.paths << Rails.root.join("lib/component_previews").to_s
config.view_component.previews.route = "/previews"
config.view_component.previews.enabled = true
```

Previews default to enabled in development and test, and their conventional class path is `test/components/previews`. For RSpec, add `spec/components/previews` explicitly. Do not expose previews in production by default; if a project intentionally does, use a custom authenticated/authorized controller and safe data.

A custom controller must include preview actions:

```ruby
class MyPreviewController < ActionController::Base
  include ViewComponent::PreviewActions
end
```

```ruby
config.view_component.previews.controller = "MyPreviewController"
```

## Preview templates

Use a preview template when the component requires surrounding structure, such as a table row:

```text
test/components/previews/cell_component_preview.rb
test/components/previews/cell_component_preview/default.html.erb
```

An empty `default` method can resolve the matching template. Select another path relative to configured preview roots:

```ruby
render_with_template(
  template: "custom_cell_component_preview/example",
  locals: { title: title }
)
```

Keep the wrapper markup valid and use the real layout when assets or interaction controllers are required.

## Test a preview

```ruby
render_preview(:default)
assert_text "Scheduled maintenance"
```

Pass parameters or select the preview class explicitly:

```ruby
render_preview(
  :dynamic,
  from: BannerComponentPreview,
  params: { message: "Custom message", tone: "warning" }
)
```

By default, ViewComponent infers the preview class from the component test's name. Keep the preview and component naming aligned or use `from:`.

## System-test behavior

Visit a preview route from a normal system test, or render a component to a temporary system-test path:

```ruby
class DialogComponentSystemTest < ViewComponent::SystemTestCase
  test "opens and returns focus" do
    html = render_inline(DialogComponent.new)

    with_rendered_component_path(html, layout: "application") do |path|
      visit path
      click_on "Open dialog"
      assert_text "Dialog content"
    end
  end
end
```

Omit `layout` when the component is self-contained. Include it when JavaScript, CSS, import maps, or shared landmarks come from the application layout.

Assert the behavior that requires a browser: keyboard activation, focus movement/return, expanded state, hidden/visible transitions, and escape/click-away handling. Keep noninteractive permutations in fast component tests.

## State coverage

Select states from the actual contract. Commonly valuable scenarios include:

- default and alternate variants;
- with and without optional slots;
- empty and populated collections;
- short, long, localized, multiline, and overflow content;
- loading, success, validation error, disabled, selected, expanded, and permission-limited behavior;
- mobile/narrow and wide containers;
- light/dark themes when supported.

Do not multiply previews for cosmetic combinations no one needs. Cover invalid combinations through initializer validation tests when the contract rejects them.

## Avoid brittle assertions

- Prefer semantic element, role, accessible name, visible text, state attributes, and stable component hooks.
- Assert utility classes only when a class is itself a public styling/state contract.
- Do not assert private method values instead of output.
- Do not make a unit test depend on JavaScript execution.
- Do not make every system test traverse the entire application just to reach a component state; previews or rendered paths keep interaction tests focused.
