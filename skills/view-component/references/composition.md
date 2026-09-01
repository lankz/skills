# Composition, slots, and collections

Use this guide when a component accepts caller markup, renders child components, has mutually exclusive regions, repeats items, or is accumulating boolean options.

## Choose the smallest valid composition API

| Need | Use |
|---|---|
| One unconstrained caller-owned body | Main `content` |
| One optional named region | `renders_one` |
| Repeating named children | `renders_many` |
| Arbitrary caller markup in a named region | Passthrough slot |
| Stable child semantics/behavior | Component slot |
| Tiny parent-aware wrapper or default | Lambda slot |
| One region with mutually exclusive renderer types | Polymorphic slot |
| Component-owned fallback | `default_SLOT_NAME` |
| Same outer component repeated for records | `.with_collection` |

Do not replace a simple body with slots without a concrete need. Do not represent mutually exclusive states with independent slots that callers can combine invalidly.

## Basic slots

Declare named regions:

```ruby
class CardComponent < ApplicationComponent
  renders_one :header
  renders_many :actions
end
```

With no second declaration argument, these are passthrough slots that capture unrestricted caller output.

Generated API:

| Declaration | Getter | Setter | Predicate | Other setter |
|---|---|---|---|---|
| `renders_one :header` | `header` | `with_header` | `header?` | `with_header_content(value)` |
| `renders_many :actions` | `actions` | `with_action` | `actions?` | `with_actions(collection)` |

A repeating slot also generates `with_action_content(value)` for appending one content-only item without slot arguments.

Fill and render them:

```erb
<%= render CardComponent.new do |card| %>
  <% card.with_header do %>
    <h2>Account</h2>
  <% end %>

  <% card.with_action do %>
    <%= link_to "Edit", edit_account_path %>
  <% end %>
<% end %>
```

```erb
<% if header? %>
  <header><%= header %></header>
<% end %>

<% if actions? %>
  <div class="actions">
    <% actions.each do |action| %>
      <%= action %>
    <% end %>
  </div>
<% end %>
```

Use the generated predicate when deciding whether a slot exists. Caller slots are registered after `initialize`; inspect them in `before_render` or the template, never in the initializer.

Slot names cannot be reserved framework words, end in `?`, or use an uncountable word where singular/plural method generation is ambiguous.

## Component slots

Use a child class when a slot needs a stable contract:

```ruby
class ListComponent < ApplicationComponent
  renders_many :items, ItemComponent
end
```

Arguments to `with_item` initialize `ItemComponent`; a block becomes its main content:

```erb
<% list.with_item(icon: :check) do %>
  Complete
<% end %>
```

For a component class nested inside the parent, upstream examples use a string name so constant lookup occurs correctly:

```ruby
class CardComponent < ApplicationComponent
  renders_one :header, "HeaderComponent"

  class HeaderComponent < ApplicationComponent
  end
end
```

Use component slots for semantic enforcement, reusable behavior, independent tests, or a child that is meaningful outside one template expression.

## Lambda slots

A lambda can return captured markup or a component:

```ruby
class PanelComponent < ApplicationComponent
  renders_one :heading, ->(level: 2, &block) do
    content_tag("h#{level}", class: "panel__heading", &block)
  end

  renders_many :rows, ->(record:) do
    RowComponent.new(record: record, compact: @compact)
  end

  def initialize(compact: false)
    @compact = compact
  end
end
```

Lambda slots can access parent instance state. They run when the caller invokes the slot setter; a component returned by the lambda is rendered lazily on first use. To consume a caller block, accept `&block` and call it or pass it to a capture-aware helper.

Use a lambda for small, local adaptation. Extract a child component when it acquires its own states, semantics, behavior, or testing value.

## Direct slot content

When the slot takes no arguments:

```ruby
CardComponent.new.with_header_content("Account")
```

A slot object returned by its setter also accepts content:

```erb
<% card.with_header(level: 2).with_content("Account") %>
```

This `with_content` belongs to the slot object; do not confuse it with top-level `Component.new.with_content(...)` for the component's main body.

## Populate many slots from a collection

For a component-backed `renders_many` slot, the plural setter accepts a collection of initializer arguments:

```erb
<% navigation.with_links([
  { name: "Home", href: "/" },
  { name: "Pricing", href: "/pricing" }
]) %>
```

Use the singular setter for per-item blocks or when each item needs bespoke construction. Use the plural form for uniform data-driven child components.

## Polymorphic slots

Use one named region with a closed set of alternative renderers:

```ruby
class ListItemComponent < ApplicationComponent
  renders_one :visual, types: {
    icon: IconComponent,
    avatar: ->(**arguments) { AvatarComponent.new(size: 16, **arguments) }
  }
end
```

Default setters combine slot and type:

```erb
<% item.with_visual_icon(name: :key) %>
<% item.with_visual_avatar(src: user.avatar_url, alt: user.name) %>
```

The getter and predicate stay `visual` and `visual?`. Set the polymorphic slot once; supplying multiple types raises `ContentAlreadySetForPolymorphicSlotError`.

Customize generated setter names with exact `renders:` and `as:` keys:

```ruby
renders_one :visual, types: {
  icon: { renders: IconComponent, as: :icon_visual },
  avatar: { renders: AvatarComponent, as: :avatar_visual }
}
```

Callers then use `with_icon_visual` or `with_avatar_visual`. Choose names that do not collide with existing methods.

## Default slots

ViewComponent 4 supports a component-owned fallback:

```ruby
class CardComponent < ApplicationComponent
  renders_one :header

  def default_header
    HeadingComponent.new(text: "Untitled")
  end
end
```

`default_SLOT_NAME` may return content or a component. A caller-provided slot replaces the fallback. Defaults are appropriate for stable component-owned UI, not hidden domain queries.

Default slots are compatible with self-caching because the component controls their output; caller-populated slots are not compatible with `cache_on`.

## Render a component collection

Repeat the same component over a collection with the class API:

```erb
<%= render ProductComponent.with_collection(@products) %>
```

By default, the initializer keyword is derived from the component name:

```ruby
class ProductComponent < ApplicationComponent
  def initialize(product:)
    @product = product
  end
end
```

Use an explicit keyword when derivation would be unclear:

```ruby
class ProductComponent < ApplicationComponent
  with_collection_parameter :item

  def initialize(item:)
    @item = item
  end
end
```

The first argument to `.with_collection` must respond to `to_ary`. Pass additional shared keyword arguments after the collection:

```erb
<%= render ProductComponent.with_collection(@products, compact: true) %>
```

The initializer must accept them.

### Counter and iteration context

Accept optional generated metadata using the effective collection parameter:

```ruby
def initialize(product:, product_counter:, product_iteration:)
  @product = product
  @counter = product_counter
  @iteration = product_iteration
end
```

Iteration exposes `size`, `index`, `first?`, and `last?`. Use the supplied API rather than recomputing positions. Do not rely on undocumented index/counter bases without checking the installed version or source.

### Spacer component

Render an instantiated component between items:

```erb
<%= render ProductComponent.with_collection(
  @products,
  spacer_component: DividerComponent.new
) %>
```

Use semantic CSS spacing when no actual separator belongs in the accessibility tree. Use a spacer component when the separator is meaningful markup or has its own rendering contract.

## Data performance

`.with_collection` streamlines rendering; it does not preload data. The caller must prepare the collection efficiently:

- apply authorization and tenant scope before rendering;
- preload associations used by item components;
- paginate large result sets;
- avoid component-level database queries;
- keep shared expensive values in explicit collection arguments rather than recomputing per item.

## Composition review

- Is `content` enough, or does the region need a name?
- Does a slot need arbitrary markup, a lambda adapter, or a real child component?
- Can callers create invalid combinations? If so, narrow the API or use a polymorphic slot.
- Has a lambda grown into a hidden component?
- Is a default truly component-owned?
- Is `.with_collection` repeating the outer component, while `with_items` populates children inside one outer component?
- Are collection data and associations prepared in bulk?
- If self-caching is enabled, has all caller content been removed from the contract?
