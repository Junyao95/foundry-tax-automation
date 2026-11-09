# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| `0.1.x` | ✅ |
| `< 0.1` | ❌ |

This is a portfolio/prototype project. It is not a production tax system — see
[known limitations](docs/known-limitations.md) before using it with real data.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Use GitHub's private **Report a vulnerability** flow under the repository's
*Security* tab, or contact the maintainer directly through their GitHub
profile. Include:

- what you found and where (file/path or Azure resource type),
- steps to reproduce,
- potential impact,
- any suggested fix.

Please redact keys, tokens, SAS URLs and personal data even in private reports.
You should get an acknowledgement within a few days.

## What this repository deliberately excludes

- API keys (Document Intelligence, Azure AI Search)
- Entra ID bearer tokens
- `.env` files and `.foundry/` / `.azure/` deployment state
- Tenant IDs, subscription IDs and tenant-specific resource URLs
- Real employee names, compensation documents and the private tax prompt

All deployment-specific values are supplied through environment variables.
Authentication uses `DefaultAzureCredential`. See
[configuration.md §4](docs/configuration.md#4-secret-handling) and
[`.gitignore`](.gitignore).

## If you find a leaked secret here

1. **Rotate it immediately** in the Azure Portal — rotation matters more than
   cleaning git history.
2. Report it privately as above.
3. Enable [GitHub secret scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
   and push protection for the repository.

## Historical note

This repository was derived from a local working copy that contained three
plaintext credentials (a Document Intelligence key, an Azure AI Search admin
key, and a pasted Entra bearer token). Those files were **untracked** and were
never committed to any git history. The credentials were removed during the
cleanup and are not present here, but they should be treated as exposed:

- Azure Portal → Document Intelligence → *Keys and Endpoint* → regenerate keys
- Azure Portal → Azure AI Search → *Keys* → regenerate the admin key
- The bearer token was short-lived; it was removed from the source entirely

Rotation steps: [deployment.md §2](docs/deployment.md#2-rotate-exposed-keys).

## Screenshot hygiene

Anyone contributing screenshots must follow the
[redaction rules](docs/screenshots.md#redaction-rules-read-before-capturing).
Screenshots are reviewed like code.
