# API and error reference

This is a task-oriented index of the public API documented for ViewComponent 4.15. Confirm availability in the installed version. Detailed usage and tradeoffs live in the topic references.

## `ViewComponent::Base` class methods

| Method | Contract |
|---|---|
| `.after_compile` | Extension hook called after compilation; no-op by default. Override only for compile-dependent extension work such as helper generation or metadata registration. |
| `.config` | Current `ActiveSupport::OrderedOptions` configuration. Application code normally configures through Rails `config.view_component`. |
| `.identifier` | Path of the component Ruby source file. |
| `.sidecar_files(extensions)` | Find sidecar files for dotless extension names such as `["erb", "haml"]`. |
| `.strip_trailing_whitespace(value = true)` | Enable or disable template trailing-whitespace stripping before compilation. |
| `.strip_trailing_whitespace?` | Query the effective whitespace setting. |
| `.with_collection(collection, spacer_component: nil, **args)` | Build one component per array-like item, optionally with a spacer and shared initializer arguments. |
| `.with_collection_parameter(parameter)` | Set the initializer keyword used for each collection item. |

Extension hooks and compiler paths are advanced API. Do not depend on compiler-generated `_call_*` methods.

## `ViewComponent::Base` instance methods

| Method | Contract and boundary |
|---|---|
| `#initialize` | Explicit component input contract. ViewComponent's default is empty; do not use render context here. |
| `#render_in(view_context, **, &block)` | Rails renderable entry point. Captures an optional caller block in the calling view context and returns handler-escaped output. A component instance may enter it only once. |
| `#before_render` | Hook after context/slots are available and before `render?`. |
| `#render?` | Return false to emit an empty result. |
| `#around_render` | Wrap template/`call` rendering; yield to render. |
| `#content` | Captured main render-block content. |
| `#content?` | Whether main content was supplied. |
| `#controller` | Current `ActionController::Base`; render-time only and intentionally discouraged as implicit coupling. |
| `#request` | Current `ActionDispatch::Request`; render-time only and intentionally discouraged as implicit coupling. |
| `#helpers` | Current `ActionView::Base` helper proxy; render-time only. |
| `#current_template` | Current template metadata used by rendering/caching. |
| `#format` | Renderable format contract; actual format is determined at runtime. |
| `#render_parent` | Emit the current-variant parent template once from a subclass template. |
| `#render_parent_to_string` | Return parent-template output as a string, normally inside `call`. |
| `#output_preamble` | Optional output before the rendered body. Unsafe strings are escaped. |
| `#output_postamble` | Optional output after the rendered body. Unsafe strings are escaped. |
| `#set_original_view_context(view_context)` | Set the original Action View context for nested renderables that need correct helper behavior. This is an integration hook, not normal component authoring. |

Public `call` and `call_VARIANT` are alternative rendering methods even though the generated API page does not list them in its Base table.

## Content and template DSL

| API | Effect |
|---|---|
| `component.with_content(value)` | Assign main content before render. Mutually exclusive with a render block; value cannot be nil. |
| `erb_template(source)` / handler equivalent | Define one inline template in the component class. |
| `strip_trailing_whitespace(value = true)` | Remove the final template whitespace before compilation. |
| `call` | Public template-free rendering method. |
| `call_VARIANT` | Public variant-specific rendering method. |
| `render_parent` | Emit a parent template from a child template. |
| `render_parent_to_string` | Return parent output for use in Ruby rendering. |

Template resolution supports sibling files, same-named sidecar directories, variants, inherited templates, inline handler templates, and `call` methods.

## Slot DSL

### Singular

```ruby
renders_one :header
```

Generates:

- `header`
- `header?`
- `with_header(*args, **kwargs, &block)`
- `with_header_content(value)`
- optional component-defined `default_header`

### Multiple

```ruby
renders_many :items
```

Generates:

- `items`
- `items?`
- singular appender `with_item(*args, **kwargs, &block)`
- singular direct-content appender `with_item_content(value)`
- plural bulk setter `with_items(collection)`

The declaration's second argument may be a component class, nested class-name string, or callable. A callable may return content or another component.

### Polymorphic

```ruby
renders_one :visual, types: {
  icon: IconComponent,
  avatar: { renders: AvatarComponent, as: :avatar_visual }
}
```

Default type setter: `with_visual_icon`. Custom setter above: `with_avatar_visual`. Getter/predicate remain `visual` and `visual?`.

## Collection API

```ruby
ProductComponent.with_collection(products, compact: true)
```

The component initializer accepts the derived/configured item keyword and every shared argument. It may also accept:

- `PARAMETER_counter`
- `PARAMETER_iteration`, exposing `size`, `index`, `first?`, and `last?`

Pass an instantiated `spacer_component:` to render between items. The collection must respond to `to_ary`.

## Experimental cache API

Available in the reviewed 4.15 source and introduced in 4.14:

```ruby
include ViewComponent::ExperimentallyCacheable
cache_on :record, if: :cacheable?
```

| API | Contract |
|---|---|
| `include ViewComponent::ExperimentallyCacheable` | Register the component with Rails template-digest dependency handling. |
| `cache_on(*methods, if: ..., unless: ...)` | Self-cache complete output using method values. Forbids all caller content/slots. |
| `.cache_digest` | Digest of tracked component source/dependencies; available outside a request. |
| `# Template Dependency: TARGET` | Declare a dynamic partial/component dependency static analysis cannot see. |

Treat the whole API as experimental and read `advanced-operations.md` before use.

## Deferred-render API

```ruby
include ViewComponent::Serializable
proxy = MyComponent.render_later(record: record)
```

| API | Contract |
|---|---|
| `.render_later(*args, **kwargs)` | Return a serializable proxy; do not instantiate now. |
| Proxy `with_SLOT(...)` | Record non-block slot calls for replay. |
| `ViewComponent::ActiveJobSerializer` | Automatically registered with Active Job when loaded. |

All arguments must be Active Job serializable. Blocks and anonymous/unloadable classes raise `ViewComponent::Serializable::UnserializableError`.

## Rails configuration

Configure through `config.view_component`.

### Generator namespace

| Key | Default |
|---|---:|
| `generate.path` | `"app/components"` |
| `generate.sidecar` | `false` |
| `generate.stimulus_controller` | `false` |
| `generate.typescript` | `false` |
| `generate.locale` | `false` |
| `generate.distinct_locale_files` | `false` |
| `generate.preview` | `false` |
| `generate.preview_path` | `""` |
| `generate.use_component_path_for_rspec_tests` | `false` |
| `generate.parent_class` | `nil` |

### Preview namespace

| Key | Default |
|---|---:|
| `previews.controller` | `"ViewComponentsController"` |
| `previews.route` | `"/rails/view_components"` |
| `previews.enabled` | true in development and test |
| `previews.default_layout` | `nil` |
| `previews.paths` | discovered test/engine preview roots |

### Instrumentation

`instrumentation_enabled` defaults to false and gates `render.view_component`. It does not gate eager-load `compile.view_component`.

`ViewComponent::Config.current` holds defaults early in framework loading. Do not use the generated page's private `Config#config` reader as an application API.

## `ViewComponent::TestHelpers`

| Helper | Contract |
|---|---|
| `render_inline(component, **args, &block)` | Render into the test view context, return parsed Nokogiri output, and make Capybara assertions available when installed. |
| `render_in_view_context(...) { ... }` | Execute a block with forwarded arguments through `instance_exec` in the test view context. |
| `render_preview(name, from: ..., params: {})` | Render a named preview inline. The preview class is inferred unless `from:` is supplied. |
| `rendered_content` | Latest `ActionView::OutputBuffer`. |
| `rendered_json` | `JSON.parse` of latest rendered content. |
| `vc_test_controller` | Current test controller instance. |
| `vc_test_controller_class` | Override/inspect the controller class used by `render_inline`. |
| `vc_test_request` | Current `ActionDispatch::TestRequest`. |
| `vc_test_view_context` | Current `ActionView::Base`; reset after each inline render. |
| `with_controller_class(klass) { ... }` | Scope a controller class to a block. |
| `with_format(*formats) { ... }` | Scope request/template formats. |
| `with_request_url(full_path, host: nil, method: nil, protocol: nil) { ... }` | Scope path, query, host, method, and protocol. |
| `with_variant(*variants) { ... }` | Scope Action Pack variants. |

The test helpers also expose `assert_component_rendered` and `refute_component_rendered`, though the generated API page omits them.

## Preview API

| API | Contract |
|---|---|
| `class XPreview < ViewComponent::Preview` | Public instance methods become scenarios. |
| `render(component) { ... }` | Return component output for a scenario. |
| Preview method keyword arguments | Become URL/query parameters with defaults. |
| `layout "name"` | Select a layout for one preview class. |
| `render_with_template(template: ..., locals: ...)` | Use a wrapper template relative to preview roots. |
| `include ViewComponent::PreviewActions` | Turn a custom controller into a preview controller. |

`ViewComponent::Preview` includes Rails tag helpers (`tag` and `content_tag`).

## Error diagnosis

### Lifecycle and reuse

| Error | Cause and correction |
|---|---|
| `ControllerCalledBeforeRenderError` | `controller` was used before a view context existed. Pass the needed value or defer to `before_render`. |
| `HelpersCalledBeforeRenderError` | `helpers` was used before render. Pass/delegate explicitly or defer to `before_render`. |
| `TranslateCalledBeforeRenderError` | Component translation lookup ran before render. Defer it or use context-independent `I18n` only when appropriate. |
| `ReusedInstanceError` | The same component object was rendered twice. Instantiate a fresh component; reuse can leak request/helper/slot/content state and is a security issue. |

### Main and slot content

| Error | Cause and correction |
|---|---|
| `DuplicateContentError` | Both top-level `with_content` and a render block were supplied. Choose one. |
| `DuplicateSlotContentError` | A slot received conflicting block/content mechanisms. Choose one. |
| `NilWithContentError` | `with_content` received nil. Pass a value or omit content. |
| `ContentSlotNameError` | A slot was named reserved `content`. Use main content or rename it. |
| `RedefinedSlotError` | The same slot name was declared more than once. Consolidate or rename. |
| `ReservedSingularSlotNameError` | Singular slot name conflicts with framework API. Rename it. |
| `ReservedPluralSlotNameError` | Generated plural slot name conflicts with framework API. Rename it. |
| `SlotPredicateNameError` | Slot name ends in `?`; predicates are generated automatically. Remove the suffix. |
| `UncountableSlotNameError` | Singular/plural API cannot be derived from an uncountable word. Choose an explicit countable name. |
| `InvalidSlotDefinitionError` | Slot renderer is not a class, class-name string, or callable. Supply a supported definition. |
| `AlreadyDefinedPolymorphicSlotSetterError` | A generated/custom type setter would overwrite an existing method. Choose another `as:` name. |
| `ContentAlreadySetForPolymorphicSlotError` | More than one type/content was assigned to a singular polymorphic slot. Set it once. |

### Collections and initializers

| Error | Cause and correction |
|---|---|
| `InvalidCollectionArgumentError` | `.with_collection` input does not respond to `to_ary`. Materialize or pass an array-like collection. |
| `MissingCollectionArgumentError` | Initializer does not accept the derived/configured item keyword. Add it or use `with_collection_parameter`. |
| `ReservedParameterError` | Initializer keyword shadows public ViewComponent API. Rename it. |

### Templates and previews

| Error | Cause and correction |
|---|---|
| `MissingTemplateError` | No template matches requested locale/format/variant/handler. Add or rename a valid template/`call` method. |
| `MissingPreviewTemplateError` | A template-backed preview method has no matching preview template. Add it under a configured preview root or call `render`. |
| `MultipleInlineTemplatesError` | More than one inline template macro was defined on a component. Keep one rendering template. |
| `SystemTestControllerNefariousPathError` | System-test rendering attempted to resolve outside the expected directory. Treat it as a path-boundary/security failure; do not bypass validation. |

### Caching

| Error | Cause and correction |
|---|---|
| `ContentPassedToCachedComponentError` | A self-caching `cache_on` component received caller content/slots not represented in its key. Remove `cache_on` or make/key all content internally. |
| `UndefinedCacheKeyMethodError` | A method named by `cache_on` does not exist. Define it or remove it. |
| `CacheDigestTemplateError` | Internal synthetic digest template was rendered. Render the component itself. |

### Deferred rendering

`ViewComponent::Serializable::UnserializableError` is raised for blocks, anonymous/unloadable component classes, or unsupported proxy operations. Replace caller blocks with component-backed slots and pass only Active Job serializable arguments.

## Version landmarks

Useful minimum-version labels from the official guides:

| Version | Feature |
|---|---|
| 1.8.0 | `render?` |
| 1.16.0 | `call` |
| 2.1.0 | `.with_collection` |
| 2.5.0 | Collection counter |
| 2.7.0 | Sidecar subdirectory |
| 2.8.0 | `before_render` |
| 2.12.0 | Slots |
| 2.19.0 | Inherited templates |
| 2.23.0 | Bulk `renders_many` setter |
| 2.31.0 | `with_content` |
| 2.33.0 | Collection iteration |
| 2.42.0 | Polymorphic slots |
| 2.50.0 | Slot predicates |
| 2.55.0 | `render_parent` |
| 2.56.0 | `render_preview` in tests |
| 3.0.0 | Inline templates and `with_SLOT_content` |
| 3.1.0 | Custom polymorphic setters |
| 3.20.0 | `spacer_component` |
| 4.0.0 | Default slots; `around_render` stabilized around the 4.0 prerelease |
| 4.8.0 | Compile instrumentation |
| 4.14.0 | Experimental cache API |
