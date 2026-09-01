# Tutorial: build a component end to end

Use this learning path for a first ViewComponent in an application. Adapt names and commands to the repository's own rules.

## Outcome

Build a small `NoticeComponent` with an explicit contract, caller content, conditional rendering, a preview, and a rendered-output test.

## 1. Confirm ViewComponent is installed

Check the lockfile and the application's base class. A typical base class is:

```ruby
class ApplicationComponent < ViewComponent::Base
end
```

If the dependency or base class is absent, stop treating the task as a ViewComponent implementation. Do not add the gem unless adding or migrating to it is part of the requested change.

Current ViewComponent 4 documentation supports actively maintained Ruby versions from 3.2 and Rails versions from 7.1, but the project's lockfile is authoritative.

## 2. Generate the component

Prefer the project generator so class, template, test, and preview paths follow configuration:

```console
bin/rails generate view_component:component Notice tone --preview
```

Use the repository's required command launcher. A standard generator creates the component class, an ERB template, a test, and—when requested—a preview.

## 3. Define a narrow contract

Use keyword inputs and validate finite choices. Content supplied by the caller is available through `content`:

```ruby
class NoticeComponent < ApplicationComponent
  TONES = %i[info success warning danger].freeze

  def initialize(tone: :info, dismissible: false)
    raise ArgumentError, "unknown tone: #{tone}" unless TONES.include?(tone)

    @tone = tone
    @dismissible = dismissible
  end

  def render?
    content?
  end

  private

  attr_reader :tone

  def dismissible?
    @dismissible
  end

  def classes
    ["notice", "notice--#{tone}"]
  end
end
```

Do not read `params`, query records, or call view-context helpers in `initialize`.

## 4. Write semantic, declarative markup

```erb
<div class="<%= class_names(classes) %>" role="status">
  <div class="notice__body"><%= content %></div>

  <% if dismissible? %>
    <button type="button" class="notice__dismiss" aria-label="Dismiss notice">
      <%= helpers.icon("x", aria: { hidden: true }) %>
    </button>
  <% end %>
</div>
```

This markup is only illustrative. Reuse the application's local alert, button, icon, Stimulus, token, and translation conventions. Choose `role="status"`, `alert`, or no live-region role from the actual urgency and update behavior; do not cargo-cult the example.

## 5. Render it

```erb
<%= render NoticeComponent.new(tone: :success, dismissible: true) do %>
  Profile updated.
<% end %>
```

For literal string content, `with_content` is also available:

```erb
<%= render NoticeComponent.new(tone: :success).with_content("Profile updated.") %>
```

Use either a render block or `with_content`, never both.

## 6. Create preview states

```ruby
class NoticeComponentPreview < ViewComponent::Preview
  def default
    render NoticeComponent.new do
      "An informational notice"
    end
  end

  def dismissible_error
    render NoticeComponent.new(tone: :danger, dismissible: true) do
      "We could not save your changes."
    end
  end

  def long_content
    render NoticeComponent.new do
      "A deliberately long localized message that exercises wrapping and layout."
    end
  end
end
```

Built-in previews are normally at `/rails/view_components` in development and test. Give scenarios safe, deterministic data.

## 7. Test the rendered contract

```ruby
class NoticeComponentTest < ViewComponent::TestCase
  test "renders a dismissible danger notice" do
    render_inline(NoticeComponent.new(tone: :danger, dismissible: true)) do
      "Could not save"
    end

    assert_selector ".notice.notice--danger[role='status']", text: "Could not save"
    assert_selector "button[type='button'][aria-label='Dismiss notice']"
  end

  test "does not render without content" do
    render_inline(NoticeComponent.new)

    refute_component_rendered
  end
end
```

If dismissal uses JavaScript, add a browser/system test for keyboard activation, visibility change, and focus behavior. Do not force implementation details into the unit test.

## 8. Review the result

Confirm that:

- the initializer reveals every required dependency;
- the component has one coherent responsibility;
- caller markup uses content or slots, not an unsafe string argument;
- the template contains little decision-making;
- preview scenarios expose the meaningful states;
- tests assert what users and assistive technology observe;
- local design-system and documentation contracts remain accurate.
