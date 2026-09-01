# Advanced operations

Use this reference for installation compatibility, generators, configuration, instrumentation, experimental caching, and Turbo Stream/background rendering. Confirm the installed version before applying recently added APIs.

## Compatibility baseline for 4.15

The reviewed documentation declares support for actively maintained versions of:

- Ruby 3.2 or newer;
- Rails 7.1 or newer.

Minimums are changed only in major ViewComponent releases. The tested template engines are ERB, Haml, and Slim. Other Rails template handlers are expected to work but are not part of the stated tested matrix.

Bridgetown support comes from the separate experimental `bridgetown-view-component` shim. Do not treat it as built-in Rails integration.

Action Text's `rich_textarea` may raise `undefined method "rich_textarea_tag"`; delegate that helper to the render-time helper proxy:

```ruby
delegate :rich_textarea_tag, to: :helpers
```

The application's locked gem and test suite override this general baseline.

## Generator

Basic and namespaced generation:

```console
bin/rails generate view_component:component Example title content
bin/rails generate view_component:component Sections::Example title content
```

The normal generator creates a class, a test/spec using the configured framework, and a template using the configured handler. Prefer it to manual scaffolding.

One-off options:

| Option | Effect |
|---|---|
| `--template-engine slim` | Override the configured template engine; built-in generators exist for ERB, Haml, and Slim |
| `--test-framework rspec` | Override `config.generators.test_framework` |
| `--preview` | Add a preview |
| `--stimulus` | Add a sidecar Stimulus controller |
| `--typescript` | Use TypeScript for the generated Stimulus controller |
| `--locale` | Add component locale file(s) |
| `--sidecar` | Put the template in a same-named sidecar directory |
| `--inline` | Put an inline handler template in the class; no template file |
| `--call` | Generate a public `call`; no template file |
| `--parent MyBaseComponent` | Select a parent class |
| `--skip-collision-check` / `--force` | Bypass naming collision protection |

Choose one rendering strategy; do not combine `--inline` and `--call`. Treat force/collision bypass as an overwrite-risk operation: inspect the exact existing targets first and use it only when replacing them is intended.

By default the generator selects `ApplicationComponent` when defined, otherwise `ViewComponent::Base`.

## Rails configuration

Set options in application or environment configuration:

```ruby
MyApplication.configure do
  config.view_component.instrumentation_enabled = true
  config.view_component.generate.path = "app/components"
  config.view_component.generate.preview = true
  config.view_component.previews.default_layout = "component_preview"
end
```

### Generator settings

All boolean generator options default to `false` unless noted.

| Setting | Default | Meaning |
|---|---:|---|
| `generate.path` | `"app/components"` | Generated component root |
| `generate.sidecar` | `false` | Always use sidecar directories |
| `generate.stimulus_controller` | `false` | Always generate a Stimulus controller |
| `generate.typescript` | `false` | Generate TypeScript rather than JavaScript |
| `generate.locale` | `false` | Always generate locale files |
| `generate.distinct_locale_files` | `false` | One locale sidecar per `I18n.available_locales` |
| `generate.preview` | `false` | Always generate a preview |
| `generate.preview_path` | `""` | Explicit destination when multiple preview roots exist |
| `generate.use_component_path_for_rspec_tests` | `false` | Mirror custom component path under `spec/` |
| `generate.parent_class` | `nil` | Project-wide generated superclass |

The upstream generator guide incorrectly omits the `generate` namespace from `parent_class`; current 4.15 source uses:

```ruby
config.view_component.generate.parent_class = "MyBaseComponent"
```

If `generate.path` moves outside an existing eager-load root, add it explicitly:

```ruby
config.view_component.generate.path = "app/views/components"
config.eager_load_paths << Rails.root.join("app/views/components")
```

With `generate.use_component_path_for_rspec_tests = true`, `app/views/components` maps to `spec/views/components`; otherwise specs normally go under `spec/components`.

### Preview settings

| Setting | Default | Meaning |
|---|---:|---|
| `previews.controller` | `"ViewComponentsController"` | Preview controller |
| `previews.route` | `"/rails/view_components"` | Preview route root |
| `previews.enabled` | true in development/test | Enable routes and discovery |
| `previews.default_layout` | `nil` | Layout for index and examples |
| `previews.paths` | discovered `test/components/previews` roots | Preview class/template search paths |

Append rather than replace roots unless replacement is intentional:

```ruby
config.view_component.previews.paths << Rails.root.join("spec/components/previews").to_s
```

The generated API page omits `previews.paths`, but current source and preview guides use it.

## Instrumentation

### Render notifications

Enable deliberately:

```ruby
config.view_component.instrumentation_enabled = true
```

Subscribe to the current event name:

```ruby
ActiveSupport::Notifications.subscribe("render.view_component") do |event|
  event.payload[:name]
  event.payload[:identifier]
  event.payload[:view_identifier]
end
```

Do not subscribe to the stale `!render.view_component` name shown in one upstream comment. Render instrumentation has a documented performance cost; measure before enabling it broadly in production.

With Rails server timing enabled, browsers can show aggregate `render.view_component` time in Network timing data. `Rack::MiniProfilerRails.subscribe("render.view_component")` can expose per-component breakdowns using event start, finish, and `payload[:identifier]`.

### Compile notification

ViewComponent 4.8+ always emits `compile.view_component` during eager compilation when `config.eager_load` is true:

```ruby
ActiveSupport::Notifications.subscribe("compile.view_component") do |event|
  Rails.logger.info("ViewComponent compile: #{event.duration}ms")
end
```

This event is independent of `instrumentation_enabled`.

## Experimental caching

Introduced in ViewComponent 4.14 and explicitly experimental: it may change or disappear in a non-major release. Check the locked version and write focused cache-invalidation tests before adopting it.

### Why opt in

Rails fragment-cache digests normally follow template/partial dependencies but do not automatically see ViewComponent source. Without integration, changing a component can leave stale surrounding fragment caches.

Include the experimental module on each participating component:

```ruby
class PostComponent < ApplicationComponent
  include ViewComponent::ExperimentallyCacheable

  def initialize(post:)
    @post = post
  end
end
```

An external fragment cache can now incorporate the component dependency:

```erb
<% cache @post do %>
  <%= render PostComponent.new(post: @post) %>
<% end %>
```

Documented digest inputs include the component template, Ruby class, sidecar files, superclasses, literal child components, and rendered partials.

### Self-caching

Declare component methods that form its cache key:

```ruby
class PostComponent < ApplicationComponent
  include ViewComponent::ExperimentallyCacheable

  cache_on :post, unless: -> { post.draft? }

  def initialize(post:)
    @post = post
  end

  private

  attr_reader :post
end
```

The effective key combines:

- component virtual path;
- `ActionView::Digestor` digest;
- requested format and variant;
- current `I18n.locale`;
- values returned by all `cache_on` methods.

Caching is skipped unless the controller enables `perform_caching`. `if:` and `unless:` accept a method name or a proc evaluated on the component. A key method returning `nil` or `false` still contributes that value; use the condition option to disable caching.

### Caller-content prohibition

A component declaring `cache_on` cannot accept any caller-owned content:

- render block;
- top-level `with_content`;
- slots populated by the caller.

Such content is absent from the cache key, so accepting it could serve one caller's markup to another. ViewComponent raises `ContentPassedToCachedComponentError` even when runtime caching is disabled.

Component-owned `default_SLOT_NAME` output is allowed. To cache a composable component, remove `cache_on` and use an external fragment cache around an `ExperimentallyCacheable` component, or move all output inside the component and derive it from explicit `cache_on` values.

`cache_on` is inherited. Never place it on `ApplicationComponent` unless every subclass is deliberately self-caching and forbids caller content.

### Digest access

Read a digest outside a request:

```ruby
PostComponent.cache_digest
```

Use it in a non-render cache key when output depends on component source:

```ruby
Rails.cache.fetch(["post-summary", post, PostComponent.cache_digest]) do
  build_summary(post)
end
```

### Dynamic dependencies

Static analysis cannot discover interpolated or runtime render targets. Declare every possible dependency with exact Rails directives:

```ruby
# Template Dependency: posts/byline
# Template Dependency: PostSummaryComponent
# Template Dependency: PostDetailComponent
```

Partials use paths; components use class names. Directives may live in Ruby or template source. A declared child component must also include `ViewComponent::ExperimentallyCacheable` so it has a digest.

Included modules are not tracked, while superclasses are. Add an explicit dependency where possible and test invalidation for behavior mixed in through modules.

### Cache key boundary

`cache_on` methods run before rendering. They cannot use `helpers` or view context. If a request, tenant, locale beyond `I18n.locale`, permission, or feature state changes output, pass it explicitly and include it in the key—or do not self-cache.

## Turbo Streams

### Immediate broadcast

Render a fresh component to HTML in the controller context:

```ruby
html = view_context.render(MessageComponent.new(message: @message))

Turbo::StreamsChannel.broadcast_append_to(
  "messages",
  target: "messages",
  html: html
)
```

The official guide also shows `render_to_string(component)`. Use the form supported by the local Rails/ViewComponent versions and do not reuse the instance.

### Deferred Active Job broadcast

Make a component serializable and enqueue a proxy rather than an instance:

```ruby
class MessageComponent < ApplicationComponent
  include ViewComponent::Serializable

  def initialize(message:)
    @message = message
  end
end
```

```ruby
proxy = MessageComponent.render_later(message: message)

Turbo::StreamsChannel.broadcast_action_later_to(
  "messages",
  action: :append,
  target: "messages",
  renderable: proxy,
  layout: false
)
```

`.render_later(*args, **kwargs)` returns `ViewComponent::Serializable::Proxy`, storing the class and arguments without instantiating the component. `ViewComponent::ActiveJobSerializer` is registered when Active Job loads. The job resolves the class, instantiates it, renders through `ApplicationController.render`, and broadcasts the HTML. Active Record arguments use GlobalID; all other arguments must satisfy Active Job serialization.

### Serializable slots

Component-backed slot calls without blocks are recorded and replayed:

```ruby
class CardComponent < ApplicationComponent
  include ViewComponent::Serializable
  renders_many :bodies, BodyComponent
end

proxy = CardComponent.render_later
proxy.with_body(text: "First")
proxy.with_body(text: "Second")
```

Blocks cannot be serialized. A block passed to `render_later`, the proxy's `render_in`, or a proxy slot call raises `ViewComponent::Serializable::UnserializableError` immediately. Use component slots with serializable arguments.

The component class must be named and loadable; anonymous classes cannot be resolved with `safe_constantize` and are rejected.

Deferred rendering has no originating request context. Pass host, locale, tenant, policy result, and route inputs explicitly as needed. Do not serialize request-bound helpers or a pre-rendered component instance.

## Operational verification

- Generator/configuration change: run a representative generator in a disposable location or inspect generated paths, then run app boot/eager load.
- Instrumentation change: subscribe in a test and assert the exact current event and payload used.
- Cache change: enable caching in a focused test, prove hit/miss behavior, source/dependency invalidation, variant/locale separation, and content restrictions.
- Deferred render change: exercise Active Job serialization/deserialization, GlobalID reload, slots, and the final broadcast/rendered HTML.
- Compatibility upgrade: run component unit tests, previews, system tests, eager compilation, and production-like asset/template loading.
