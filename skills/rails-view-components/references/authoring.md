# Authoring components

Use this how-to guide for component contracts, content, rendering strategies, lifecycle, conditional output, helpers, routes, forms, and translations.

## Conventions and basic rendering

A normal application defines:

```ruby
class ApplicationComponent < ViewComponent::Base
end
```

Components normally live in `app/components`, end with `Component`, use plural namespaces, and are named for rendered output:

```ruby
class Users::AvatarComponent < ApplicationComponent
  def initialize(user:, size: :medium)
    @user = user
    @size = size
  end
end
```

Render through Rails:

```erb
<%= render Users::AvatarComponent.new(user: @user, size: :small) %>
```

ViewComponent instances are single-use. Never store and render the same instance twice; create a new object for each render.

## Initializer contract

The initializer is the component's public data API.

- Prefer keywords for clarity.
- Store only state used to render.
- Normalize and validate finite options once.
- Avoid helpers, `request`, `controller`, translation lookup, and caller-provided slots in `initialize`; render context and slots do not exist yet.
- Avoid queries and authorization decisions. Pass prepared, authorized data.
- Avoid public attribute readers unless callers need them. Template-only readers and predicates can be private.
- Do not use initializer parameter names that collide with ViewComponent public methods; the framework raises `ReservedParameterError`.

## Main content

Content passed in a render block is exposed as `content`; `content?` reports whether it exists:

```erb
<%= render CardComponent.new do %>
  <p>Caller-owned body</p>
<% end %>
```

String content can be assigned before rendering:

```erb
<%= render CardComponent.new.with_content("Plain content") %>
```

Use exactly one mechanism. A block plus `with_content` raises `DuplicateContentError`; `with_content(nil)` raises `NilWithContentError`.

Do not declare a slot named `content`. Use the built-in body or choose a meaningful named slot.

## Choose a rendering strategy

### Sibling template

The common layout is:

```text
app/components/message_component.rb
app/components/message_component.html.erb
```

Use it for readable markup with a small number of owned files.

### Sidecar directory

```text
app/components/message_component.rb
app/components/message_component/message_component.html.erb
```

Use a sidecar directory when a component owns several related templates, locale files, JavaScript, styles, or other assets. Generate it with `--sidecar` or configure the generator default.

### Inline template

ViewComponent 3+ supports handler-specific class macros:

```ruby
class GreetingComponent < ApplicationComponent
  erb_template <<~ERB
    <p>Hello, <%= @name %>!</p>
  ERB

  def initialize(name:)
    @name = name
  end
end
```

`TEMPLATE_HANDLER_template` in upstream prose is a placeholder; call a real installed-handler macro such as `erb_template` or `slim_template`.

Ruby heredoc interpolation happens while the class is defined. In an inline Slim template, escape `\#{...}` when Slim/component evaluation—not Ruby class-definition interpolation—is intended.

Only one inline template may be defined per component.

### Public `call`

For concise helper-generated output, define a public `call` method:

```ruby
class CancelLinkComponent < ApplicationComponent
  def call
    link_to "Cancel", cancel_path
  end
end
```

Variant methods use `call_VARIANT` and must also be public:

```ruby
def call_phone
  link_to "Cancel", mobile_cancel_path
end
```

Prefer a template when `call` would become a long string-building program. Choose either an inline template or `call`; do not combine alternative no-file generator modes.

## Variants and inherited templates

Rails request variants select variant templates or `call_VARIANT` methods. Test every supported variant with `with_variant`.

A subclass without its own template inherits its parent's template. If a subclass template intentionally wraps the parent:

- use `render_parent` inside a template; it emits once and respects the active variant;
- use `render_parent_to_string` inside `call` when a returned string is required;
- do not emit `<%= super %>` in ERB, which double-renders;
- prefer composition unless inheritance expresses a real subtype/template relationship.

## Trailing whitespace

An editor's final newline can add unwanted inline HTML spacing. Opt a component class in or out before compilation:

```ruby
strip_trailing_whitespace
strip_trailing_whitespace(false)
```

Use this only when output adjacency makes trailing whitespace observable.

## Lifecycle

For ViewComponent 4.15, the documented and implemented render flow is:

1. `render_in` receives the `ActionView::Context` and the caller block.
2. `before_render` runs.
3. `render?` decides whether output is produced.
4. If rendering continues, `around_render` wraps template/`call` execution.
5. Optional output preamble and postamble surround the rendered template.

### `before_render`

Use it for derived state that genuinely needs the view context or caller-populated slots:

```ruby
def before_render
  @icon = helpers.icon(icon_name)
  @has_media = media?
end
```

Do not move ordinary initializer work here. Remember that it runs even when `render?` later returns false in 4.15.

### `render?`

Use an intrinsic visibility rule to keep callers simple:

```ruby
def render?
  @user.requires_confirmation?
end
```

Use caller-level conditions for orchestration that does not belong to the component. Test conditional output with `assert_component_rendered` and `refute_component_rendered`.

### `around_render`

Use this for a true cross-cutting wrapper such as instrumentation and always yield:

```ruby
def around_render
  MyInstrumenter.instrument(self.class.name) { yield }
end
```

Do not use it as a hidden second template. ViewComponent escapes an unsafe replacement returned by `around_render`; preserve normal safe-buffer behavior.

## Helpers and Rails context

### Included or delegated helpers

Include a helper module when its methods are part of the component implementation:

```ruby
class UserIconComponent < ApplicationComponent
  include IconHelper
end
```

Or use the render-time proxy:

```ruby
helpers.icon(:user)
```

Narrow delegation keeps usage concise and visible:

```ruby
delegate :icon, to: :helpers
```

Do not call `helpers`, `controller`, `request`, or component translation methods before rendering. Their dedicated errors usually mean the work belongs in `before_render` or the value should be passed explicitly.

### Route helpers

Nested URL helpers may infer values from the current request. Prefer explicit route parameters:

```ruby
edit_user_path(user: @user)
```

Calling `helpers.edit_user_path` opts into request-context behavior; use it only when that coupling is intentional and test it with `with_request_url`.

### Form builders

ViewComponent intentionally does not apply a globally configured default form builder. Pass the intended builder explicitly:

```erb
<%= form_with model: @record, builder: CustomFormBuilder do |form| %>
  <%= form.text_field :name %>
<% end %>
```

For Action Text's missing `rich_textarea_tag` helper, the documented workaround is:

```ruby
delegate :rich_textarea_tag, to: :helpers
```

Follow the application's shared form-component and accessibility rules rather than creating component-local control styling.

## Translations

Component-owned translations can live in one sidecar file:

```text
app/components/example_component.yml
```

```yaml
en:
  greeting: "Hello"
```

or separate locale files:

```text
app/components/example_component.en.yml
app/components/example_component.fr.yml
```

Use leading-dot lookup for component-local keys:

```erb
<%= t(".greeting") %>
```

Global Rails translations remain available through `t("shared.key")`, `helpers.t`, or `I18n.t`. In global locale files, component-local lookup follows the component namespace, for example `my_module.example_component.greeting`.

Child components inherit parent component translations and can override individual keys in their own sidecar files. Prefer composition over inheritance even though translation inheritance exists.

Generate locale files with `--locale`; `generate.distinct_locale_files` creates one file for each configured `I18n.available_locales`, falling back to `en` when none are configured.

## Rendering outside a normal view

### Controller response

```ruby
render ExampleComponent.new(title: "Title")
```

Controller rendering cannot supply caller content as a block; use `with_content`. Turbo-frame responses may need `content_type: "text/html"`.

### Reusable string inside a controller

Use the component entry point to avoid consuming the controller's one response render:

```ruby
html = IconComponent.new(name: "close").render_in(view_context)
```

For Turbo broadcasts, current official docs also allow `render_to_string(component)` or `view_context.render(component)`; follow the locally working Rails/ViewComponent form.

### Outside a request

Construct a view context explicitly:

```ruby
ApplicationController.new.view_context.render(MyComponent.new)
```

This context has no originating browser request. Pass any tenant, host, locale, route, or policy state explicitly. For asynchronous Turbo rendering, use the serialization workflow in `advanced-operations.md` instead of capturing a request-bound instance.
