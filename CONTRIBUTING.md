# Contributing

Thanks for taking an interest. This is a small portfolio project, so the bar is
simple: be clear, be kind, and don't commit secrets.

## Ground rules

- **Never commit credentials.** No API keys, bearer tokens, SAS URLs, `.env`
  files, tenant IDs or real employee data. See [SECURITY.md](SECURITY.md).
- **Never lower the human-approval gate.** The "no tax computation before an
  explicit approval" rule is the core safety property of this project.
- Keep documentation in sync with code. A changed env var means an updated
  [configuration reference](docs/configuration.md).
- Screenshots must be redacted per the
  [shot list](docs/screenshots.md#redaction-rules-read-before-capturing).

## Getting set up

```bash
git clone https://github.com/Junyao95/foundry-tax-automation.git
cd foundry-tax-automation
python -m venv .venv && source .venv/Scripts/activate
pip install -r webapp/requirements.txt
pip install -r agents/extraction-agent/src/requirements.txt
pip install -r agents/sow-builder-agent/src/requirements.txt
cp .env.example .env
```

See [development.md](docs/development.md) for local agent runs, and
[deployment.md](docs/deployment.md) for the Azure side.

## Making a change

1. Open an issue first for anything beyond a typo, so we can agree on the shape.
2. Create a branch: `git checkout -b feat/short-description`.
3. Make the change and update the relevant docs.
4. Run the checks:

   ```bash
   python -m compileall -q agents webapp
   ```

5. Walk the [manual test checklist](docs/development.md#7-manual-test-checklist)
   if you touched the workflow.
6. Commit with a concise message and open a PR using the template.

## Commit messages

Short imperative summary, optional body explaining *why*:

```
Add schema validation for proposed SOW output

Model output was occasionally wrapped in prose, which broke parsing.
Fails loudly now instead of falling back to demo data.
```

## Reporting bugs

Use the bug report template. Include the component, the exact error, and the
steps to reproduce — with all keys, tokens, SAS URLs and personal data removed.
Check [troubleshooting.md](docs/troubleshooting.md) first; many issues are
configuration-related.

## Reporting security issues

Do **not** open a public issue. See [SECURITY.md](SECURITY.md).

## License

By contributing you agree that your contributions are licensed under the
[MIT License](LICENSE).
