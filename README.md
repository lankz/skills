# Ben’s Skills

A personal collection of reusable skills for software-engineering agents, maintained by [Ben Caldwell](https://github.com/lankz).

This repository is the canonical source for skills distributed through the open Agent Skills ecosystem and native Claude and Codex plugins. Skills live under `skills/<skill-name>/`.

## Skills

- [AG-UI protocol](skills/ag-ui-protocol/) helps agents design, implement, review, and debug agent-to-user event streams using AG-UI concepts, vocabulary, and event semantics without assuming full wire compatibility.
- [ViewComponent for Rails](skills/view-component/) helps agents create, migrate, refactor, review, test, preview, and troubleshoot Rails interfaces built with the ViewComponent gem.

## Installation

Install a skill in the current project with the [skills CLI](https://skills.sh/):

```bash
npx skills add lankz/skills --skill ag-ui-protocol
npx skills add lankz/skills --skill view-component
```

Add `--global` to install it for the current user instead.

## Repository layout

- `skills/` contains the canonical, agent-independent skill packages.
- `.claude-plugin/` exposes the catalogue as a managed Claude plugin.
- `.codex-plugin/` exposes the same catalogue as a managed Codex plugin.
- `.agents/plugins/` registers the repository with the Codex plugin marketplace.
- `scripts/validate` checks repository structure and synchronized metadata.

## Development

Run the repository checks before committing:

```bash
scripts/validate
```

Plugin metadata uses semantic versions. Keep the Claude and Codex manifest versions synchronized and record meaningful changes in [CHANGELOG.md](CHANGELOG.md).

## License

This repository is available under the [MIT License](LICENSE). Third-party attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
