# Configuration reference

**Single rule: no deployment-specific value lives in source control.**
Every URL, key and model name is read from the environment. The template is
[`.env.example`](../.env.example); copy it to `.env` (gitignored) and fill it in.

---

## 1. How configuration flows

```
.env (local, gitignored)
   ├── exported into your shell  ──>  webapp/app.py, webapp/orchestrator.py
   │                                 (read via os.getenv in webapp/common.py)
   │
   └── exported before `azd up` ──>  ${VAR} placeholders in each azure.yaml
                                      ──> injected as container env vars
                                          ──> read by agents/*/src/main.py
```

`azd` resolves `${VAR}` from the shell environment or the active azd
environment's `.env` file. If a placeholder is unresolved, deployment fails —
see [troubleshooting.md](troubleshooting.md#azd-unresolved-variable).

> There is no `python-dotenv` dependency. Load `.env` yourself with
> `set -a; source ./.env; set +a` (Git Bash / Linux / macOS), or use your IDE's
> env-file support or PowerShell `$env:` assignments.

---

## 2. Variable reference

Legend for **Required by**: `A1` = extraction-agent, `A2` = sow-builder-agent,
`W` = Streamlit app, `C` = CLI orchestrator.

| Variable | Required by | Description | Example / default | Secret? |
| --- | --- | --- | --- | --- |
| `FOUNDRY_PROJECT_ENDPOINT` | A1, A2, W, C | Foundry project URL used by `FoundryChatClient`. No trailing `/agents/...` segment. | `https://<account>.services.ai.azure.com/api/projects/<project>` | No |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | A1, A2, W, C | Model deployment name. Also used as the fallback for the tax agent. | `gpt-4.1-mini` | No |
| `FOUNDRY_MODEL_NAME` | A1, A2 | Legacy fallback if the variable above is unset. | — | No |
| `DOCUMENTINTELLIGENCE_ENDPOINT` | A1 | Document Intelligence resource endpoint. | `https://<name>.cognitiveservices.azure.com/` | No |
| `DOCUMENTINTELLIGENCE_API_KEY` | A1 | Document Intelligence key. Empty → PDF tool returns a structured error. | *(empty in template)* | **Yes** |
| `AZURE_SEARCH_ENDPOINT` | A2 | AI Search endpoint. Empty → labelled demo data. | `https://<name>.search.windows.net` | No |
| `AZURE_SEARCH_KEY` | A2 | AI Search **admin** key. Empty → labelled demo data. | *(empty in template)* | **Yes** |
| `AZURE_SEARCH_INDEX_NAME` | A2 | Index holding prior-year SOWs. | `prior-year-sows` | No |
| `EXTRACTION_AGENT_ENDPOINT` | W, C | Full Responses URL of the deployed `extraction-agent`. | see `.env.example` | No |
| `SOW_AGENT_ENDPOINT` | W, C | Full Responses URL of the deployed `sow-builder-agent`. | see `.env.example` | No |
| `TAX_AGENT_PROMPT_PATH` | W, C | Override path to the tax-computation system prompt. | defaults to `webapp/tax_agent.md` | No |
| `DEMO_FALLBACK` | W | Allow labelled demo SOW data when agent JSON cannot be parsed. | `true` | No |
| `PYTHONNOUSERSITE` | A1, A2 | Set to `1` inside `azure.yaml` so container dependencies are isolated. | `1` | No |

### Variables set only in `azure.yaml`

These are container env vars injected by `azd`, not local shell variables:

- `PYTHONNOUSERSITE: "1"`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME: gpt-4.1-mini` (hardcoded deployment name declared in the same manifest)
- `AZURE_SEARCH_INDEX_NAME: prior-year-sows` (sow-builder only)
- `${DOCUMENTINTELLIGENCE_ENDPOINT}`, `${DOCUMENTINTELLIGENCE_API_KEY}` (extraction only)
- `${AZURE_SEARCH_ENDPOINT}`, `${AZURE_SEARCH_KEY}` (sow-builder only)

---

## 3. Startup validation

Both agent entry points fail fast with a readable message if
`FOUNDRY_PROJECT_ENDPOINT` or the model deployment name is missing. The web app
validates `FOUNDRY_PROJECT_ENDPOINT`, `EXTRACTION_AGENT_ENDPOINT` and
`SOW_AGENT_ENDPOINT` at startup via `endpoints()` and shows the error in the UI.

Optional variables degrade gracefully:

| Unset | Behaviour |
| --- | --- |
| `DOCUMENTINTELLIGENCE_*` | `extract_from_pdf` returns `{"status":"error"}`; the agent explains the failure. |
| `AZURE_SEARCH_*` | `search_prior_year_sow` returns fixtures tagged `_source: "demo-data"`. |
| `DEMO_FALLBACK` | Defaults to `true`. Set `false` to make unparseable SOW output a hard error. |
| `TAX_AGENT_PROMPT_PATH` | Uses the bundled `webapp/tax_agent.md` template. |

---

## 4. Secret handling

The two service keys should not be passed as raw environment variables in a
production deployment. Recommended progression:

1. **Local demo** — keys in a gitignored `.env`, exported into your shell.
2. **Better** — Azure Key Vault with a system-assigned managed identity on the
   hosted agents. Grant the identity `Key Vault Secrets User`, replace the
   `${..._KEY}` entries in `azure.yaml` with Key Vault references, and read the
   secret at startup.
3. **Best** — drop key-based auth entirely: use managed identity + RBAC for
   Document Intelligence (`Cognitive Services User`) and Azure AI Search
   (`Search Index Data Reader`). `DefaultAzureCredential` already supports
   this; swap `AzureKeyCredential` for the credential object in the two tools.

Also:

- **Never** commit `.env`, `*.key`, `*.pem`, `.foundry/`, `.azure/` or SAS URLs.
  The [`.gitignore`](../.gitignore) covers these.
- **Never** paste an Entra bearer token into code. Use
  `DefaultAzureCredential` — it is used everywhere in this repo.
- SAS URLs in the UI should be read-only, HTTPS-only and expire within the hour.
- Before publishing screenshots, redact tenant IDs, subscription IDs, emails,
  account names and SAS query strings — see [screenshots.md](screenshots.md).
- If a secret ever lands in a commit, rotate it first, then consider
  history rewriting and GitHub secret scanning. See
  [SECURITY.md](../SECURITY.md).

> The pre-cleanup working copy contained three live secrets. They are not in
> this repository. Rotation instructions:
> [deployment.md §2](deployment.md#2-rotate-exposed-keys).

---

## 5. Verifying your configuration

```bash
# Git Bash
set -a; source ./.env; set +a
python -c "import os; print({k: ('set' if os.getenv(k) else 'MISSING') for k in ['FOUNDRY_PROJECT_ENDPOINT','EXTRACTION_AGENT_ENDPOINT','SOW_AGENT_ENDPOINT','AZURE_AI_MODEL_DEPLOYMENT_NAME']})"
```

Then run the CLI orchestrator — it will surface auth, endpoint and JSON issues
without the Streamlit layer:

```bash
python webapp/orchestrator.py
```
