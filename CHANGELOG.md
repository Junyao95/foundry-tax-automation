# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-09

First public release: the two-agent tax automation side project, reorganized
into a standalone, publishable repository with a full documentation set.

### Added

- Standalone repository layout: `agents/extraction-agent/`,
  `agents/sow-builder-agent/`, `webapp/`, `docs/`.
- Complete documentation: README, architecture (with Mermaid + SVG diagrams),
  deployment guide, API reference, configuration reference, development guide,
  troubleshooting, known limitations, and a screenshot shot list with
  placeholder slots.
- `webapp/common.py` — shared agent invocation, JSON normalization, SOW
  parsing, tax-input builder and PDF rendering.
- `webapp/tax_agent.md` — a clearly-labelled tax prompt template with the
  expected input/output schemas.
- Structured error returns from both agent tools, download timeouts, and
  temporary-file cleanup.
- Real Azure AI Search query path in `search_prior_year_sow`, with an explicit
  `_source: "demo-data"` fallback.
- Startup validation of required environment variables.
- `.env.example` covering every variable, `.gitignore` covering secrets and
  Azure local state, MIT `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`,
  issue/PR templates and a CI workflow (Python compile + secret scan).
- Pip-based Dockerfiles with complete `requirements.txt` files.

### Changed

- Moved all configuration to environment variables; no tenant-specific
  resource URLs remain in source.
- Replaced the pasted Entra bearer token in the Streamlit app with
  `DefaultAzureCredential`.
- Renamed the two agents and updated both `azure.yaml` manifests to describe
  what they actually do.
- The Streamlit app now derives the employee name from the extraction result
  and generates a matching PDF filename.
- The CLI orchestrator now uses the same shared helpers as the web app.

### Removed

- Plaintext Document Intelligence API key, plaintext Azure AI Search admin
  key and a pasted Entra ID bearer token.
- Hardcoded Foundry account/project/agent endpoint URLs.
- The upstream sample's `uv.lock` / `pyproject.toml` build path (the Dockerfiles
  referenced a `pyproject.toml` that did not exist).
- Stock Microsoft sample README/boilerplate that did not describe this project.

### Security

- All three credentials from the original working copy were excluded. They
  must be **rotated** in Azure — see
  [docs/deployment.md §2](docs/deployment.md#2-rotate-exposed-keys).
- No secrets were ever committed to git history: the original working folder
  was untracked.

[0.1.0]: https://github.com/Junyao95/foundry-tax-automation/releases/tag/v0.1.0
