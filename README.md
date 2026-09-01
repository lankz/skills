# Ben’s Skills

A personal collection of reusable skills for software-engineering agents, maintained by [Ben Caldwell](https://github.com/lankz).

This repository is the canonical source for skills distributed through the open Agent Skills ecosystem and native Claude and Codex plugins. Skills live under `skills/<skill-name>/`.

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
