# Upstream source map and version notes

## Provenance

These references synthesize the official `ViewComponent/view_component` documentation from:

- Version declared by the documentation: `4.15.0`
- Git commit: `2e6e02d516b645c545eeecb021367047b69a6201`
- Commit date: 2026-08-25
- Repository: <https://github.com/ViewComponent/view_component>
- Maintained documentation: <https://viewcomponent.org/>

ViewComponent 4 is described upstream as Long-Term Support and feature-complete. Verify the application's locked version before using APIs added in recent 4.x releases.

## Complete in-scope coverage

Every in-scope documentation page is represented below. Site scaffolding and assets were inventoried but are not copied into the skill.

| Upstream file | Encoded in |
|---|---|
| `docs/index.md` | `tutorial.md`, `architecture-and-quality.md` |
| `docs/how-it-works.md` | `authoring.md`, `architecture-and-quality.md` |
| `docs/best_practices.md` | `architecture-and-quality.md` |
| `docs/api.md` | `api-reference.md` and topic references |
| `docs/compatibility.md` | `advanced-operations.md` |
| `docs/known_issues.md` | `advanced-operations.md`, `api-reference.md` |
| `docs/guide/index.md` | This routing map; the upstream page is only a navigation parent |
| `docs/guide/getting-started.md` | `tutorial.md`, `authoring.md` |
| `docs/guide/lifecycle.md` | `authoring.md` |
| `docs/guide/templates.md` | `authoring.md` |
| `docs/guide/slots.md` | `composition.md` |
| `docs/guide/collections.md` | `composition.md` |
| `docs/guide/conditional_rendering.md` | `authoring.md` |
| `docs/guide/helpers.md` | `authoring.md` |
| `docs/guide/translations.md` | `authoring.md` |
| `docs/guide/testing.md` | `testing-and-previews.md`, `api-reference.md` |
| `docs/guide/previews.md` | `testing-and-previews.md`, `advanced-operations.md` |
| `docs/guide/generators.md` | `advanced-operations.md` |
| `docs/guide/configuration.md` | `advanced-operations.md`, `api-reference.md` |
| `docs/guide/instrumentation.md` | `advanced-operations.md` |
| `docs/guide/caching.md` | `advanced-operations.md`, `api-reference.md` |
| `docs/guide/turbo_streams.md` | `advanced-operations.md` |
| `docs/case-studies/jellyswitch.md` | `architecture-and-quality.md` as a migration lesson, not as modern sample code |
| `docs/resources.md` | Ecosystem list below |
| `docs/logo.md` | Branding boundary below |

The changelog, contribution guide, code of conduct, and history are outside this skill's component-authoring scope. Contributor data, site build dependencies, Jekyll theme files, Sass, raster/vector logo binaries, and favicon/CNAME files are site implementation rather than component-authoring documentation.

## Corrected upstream documentation defects

The skill uses verified API names and valid examples instead of preserving these source defects:

- The overview's first HTML example has a malformed closing `h1` tag.
- The generators page says `config.view_component.parent_class`; current source reads `config.view_component.generate.parent_class`.
- Generated API docs omit `generate.parent_class` and `previews.paths` because of source-comment gaps.
- API prose mentions `ViewComponent.config.previews.paths`; current source uses Rails config / `ViewComponent::Base.config.previews.paths`.
- The instrumentation page retains a stale `!render.view_component` comment; current code emits `render.view_component`.
- Preview test examples pass or assert parameters that their shown preview methods do not accept or render.
- A preview-template example closes a table with `</div>`.
- The Turbo Streams slot example passes an undeclared `title:` initializer argument.
- The TestHelpers example says `request.env` where the documented accessor is `vc_test_request`.
- The known-issues page discusses `form_with` but demonstrates `form_for`; the underlying requirement is to pass the intended `builder:` explicitly.
- The slots page has two malformed ERB block closers in its polymorphic example.
- The caching page's dynamic-component example calls `.new` on the result of `render`; instantiate the selected class before rendering it.
- The Jellyswitch example is historical and conflicts with modern guidance in several ways; it is not copied as a recommended implementation.
- The logo page writes `rbg(223 55 48)`, apparently intending `rgb(223 55 48)`.

## Optional ecosystem, not core API

The official resources page lists these examples and extensions. Inspect local dependencies and current upstream documentation before relying on any of them:

- Component libraries: Primer ViewComponents, GOV.UK Rails Components, Polaris ViewComponents, Rails Designer, and Flowbite Components.
- Interactive frameworks: Motion, StimulusReflex, and ViewComponentReflex.
- Preview/catalogue extensions: Lookbook, ViewComponent::Storybook, ViewComponent Contrib, and ViewComponentAttributes.
- Linting: `rubocop-view_component`.
- Official demo: `view-component/demo`.

The remaining podcasts, conference talks, and articles in `docs/resources.md` are a bibliography, not ViewComponent's supported API. Their contents were not promoted into skill rules.

## Branding boundary

The upstream logo page provides color, black, white, and inverse logo assets and documents the project red as `#DF3730`. Those marks identify ViewComponent; they are not an application design token. Do not add ViewComponent branding to product UI merely because the library renders it, and do not imply commercial endorsement. The upstream marks are MIT-licensed, with additional usage guidance on the official logo page.
