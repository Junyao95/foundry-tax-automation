# Troubleshooting

Quick index: [configuration](#1-configuration--startup) ·
[authentication](#2-authentication) ·
[deployment / azd](#3-deployment--azd) ·
[agents and JSON](#4-agents-and-json) ·
[Streamlit and PDF](#5-streamlit-and-pdf) ·
[Azure services](#6-azure-services)

---

## 1. Configuration / startup

| Symptom | Cause | Fix |
| --- | --- | --- |
| `RuntimeError: Set FOUNDRY_PROJECT_ENDPOINT` | Required variable missing when an agent starts | Copy `.env.example` → `.env`, fill it in, and export it before starting the process. |
| `RuntimeError: Set AZURE_AI_MODEL_DEPLOYMENT_NAME` | Model name unset | Set it to the deployment name declared in `azure.yaml` (default `gpt-4.1-mini`). |
| Streamlit shows "Missing required environment variable ..." | `endpoints()` validation failed | Load `.env` into the shell: `set -a; source ./.env; set +a`. See [configuration.md](configuration.md#1-how-configuration-flows). |
| `Tax prompt not found at ...` | `TAX_AGENT_PROMPT_PATH` points to a missing file | Fix the path or unset it to use `webapp/tax_agent.md`. |
| Everything uses demo data unexpectedly | `AZURE_SEARCH_*` are empty | That is by design. Set the two variables to enable the real index. |

### azd: unresolved variable

If `azd up` fails while expanding `${DOCUMENTINTELLIGENCE_ENDPOINT}` or
`${AZURE_SEARCH_KEY}`, the placeholder has no value in the shell or the azd
environment file.

```bash
# Check what azd will see
echo "$DOCUMENTINTELLIGENCE_ENDPOINT"
echo "$AZURE_SEARCH_KEY"

# Export them, then retry
export DOCUMENTINTELLIGENCE_ENDPOINT="https://<name>.cognitiveservices.azure.com/"
export DOCUMENTINTELLIGENCE_API_KEY="<key>"
azd up
```

On PowerShell use `$env:NAME = "value"`. Alternatively put the values in the
active azd environment's `.env` file (`.azure/<env>/.env`).

---

## 2. Authentication

| Symptom | Cause | Fix |
| --- | --- | --- |
| `DefaultAzureCredential: ... failed to acquire a token` | No Azure login, or the wrong tenant | Run `az login --tenant <tenant-id>` and `azd auth login`. |
| `401 Unauthorized` calling a hosted agent | Expired token or wrong scope | The scope must be `https://ai.azure.com/.default`. `common.py` already uses it. Re-run `az login`. |
| `403 Forbidden` on the Foundry project | Identity lacks a data-plane role | Grant **Azure AI Developer** or **Cognitive Services OpenAI User** on the project/resource group. |
| Works locally, fails on Azure | Managed identity not enabled or not granted roles | Enable a system-assigned identity and grant the same roles. |
| `az account get-access-token` returns a token for the wrong resource | Default resource is ARM | Pass `--resource https://ai.azure.com` explicitly. |

> Never work around auth errors by pasting a bearer token into source. That was
> the pattern removed from the original working copy.

---

## 3. Deployment / azd

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Dockerfile: COPY pyproject.toml ... failed` | Leftover upstream Dockerfile from the Microsoft sample | This repo uses a pip-based Dockerfile with `requirements.txt`. Make sure you are deploying from `agents/<agent>/`, not the upstream sample folder. |
| Module not found at container start (e.g. `pandas`, `azure.ai.documentintelligence`) | Dependency missing from the agent's `requirements.txt` | Add it, then `azd deploy`. The Dockerfile installs only that file. |
| Container starts then exits | Missing `FOUNDRY_PROJECT_ENDPOINT` or model name in container env | Check the `env:` block in `azure.yaml` and the `${VAR}` exports. |
| Nothing listens on 8088 | Wrong entry point | `azure.yaml` must point to `main.py`, and `main.py` must call `ResponsesHostServer(agent).run()`. |
| `azd up` creates a second model deployment | Each manifest declares its own `ai-project` | Reuse the first project and run `azd deploy` for the second agent — see [deployment.md §7](deployment.md#7-deploy-the-sow-builder-agent). |
| `azd ai agent invoke` not found | Foundry extension not installed | `azd ext install microsoft.foundry` (or install what `azd` prompts for). |
| Local agent port conflict | Both agents default to 8088 | Run one at a time locally, or change the port. |

---

## 4. Agents and JSON

| Symptom | Cause | Fix |
| --- | --- | --- |
| `{"status":"error","message":"... credentials not configured"}` | Document Intelligence env vars empty/unset in the container | Set them in `azure.yaml`'s `env:` block / shell and redeploy. |
| `Error processing PDF: 403` / download fails | SAS URL expired, wrong permissions, or not URL-safe | Generate a fresh read-only HTTPS SAS URL with a short expiry; quote it properly. |
| Excel tool returns an error | `openpyxl` missing or the file is `.xls` | Install `openpyxl`; convert legacy `.xls` to `.xlsx`. |
| `The SOW agent did not return valid JSON` | Model wrapped output in prose or Markdown fences | `clean_json_string()` strips fences and leading prose. If it persists, tighten the agent instructions or add schema validation. |
| `parse_sow_items` raises `ValueError` | Amount string had no digits | Check the SOW output shape; `parse_sow_items` accepts `Description`/`Amount (SGD)` and `label`/`amount`. |
| Prior-year lookup returns `_source: "demo-data"` | AI Search credentials unset | Expected. Configure the index per [deployment.md §9](deployment.md#9-create-the-prior-year-sow-index-optional). |
| `Prior-year lookup failed: ...` | Wrong index name, key or endpoint | Check `AZURE_SEARCH_INDEX_NAME`, key type (admin vs query), and endpoint. |
| No `REQUIRES_HUMAN_REVIEW` ever appears | Prior-year data is missing or the model is not comparing | Verify the tool output; strengthen the system prompt in `agents/sow-builder-agent/src/main.py`. |

---

## 5. Streamlit and PDF

| Symptom | Cause | Fix |
| --- | --- | --- |
| Blank page / nothing renders | Script executed with an import failure | Run `streamlit run webapp/app.py` from the repo root and read the terminal traceback. |
| `ModuleNotFoundError: common` | Script run from a different working directory | The app inserts its own folder into `sys.path`; run from the repo root as documented. |
| "Extraction or SOW build failed: ..." | Agent call failed | Check endpoints, auth and SAS URL; use `webapp/orchestrator.py` to see the raw error. |
| Step 2 shows raw text instead of JSON | Model returned prose | Expected fallback. Tighten the agent instructions. |
| "SOW parsing failed. Using demo data" | Unparseable SOW + `DEMO_FALLBACK=true` | For real usage set `DEMO_FALLBACK=false` so the workflow fails loudly. |
| PDF download button missing | `generate_tax_pdf` raised | Check the traceback; usually an `fpdf2` version difference or invalid JSON. |
| `UnicodeEncodeError` in the PDF | Non-ASCII audit-trail text | `generate_tax_pdf()` encodes audit steps to ASCII. Keep that coercion or switch to a Unicode TTF font. |
| `fpdf` import error | Installed the wrong package | Use `fpdf2` (`pip install fpdf2`), which provides the `fpdf` module. |

---

## 6. Azure services

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ResourceNotFound` for the model | Model deployment not created or wrong region | Run `azd provision`, or check the deployment name/region in the Portal. |
| `429 TooManyRequests` | Model capacity (10) exhausted or quota | Lower `sku.capacity`, retry with backoff, or request a quota increase. |
| Document Intelligence `401` | Key rotated or wrong resource | Regenerate/refresh `DOCUMENTINTELLIGENCE_API_KEY` and redeploy. |
| Slow first invocation | Cold start of a hosted container | Normal. The container is 0.5 vCPU / 1 GiB; increase resources if needed. |
| Unexpected charges | Two `azd up` runs created two model deployments | See [deployment.md §13](deployment.md#13-cost-notes) and run `azd down`. |

---

## 7. Getting a clean diagnostic run

```bash
az login
set -a; source ./.env; set +a
python webapp/orchestrator.py        # prints each stage and the raw agent output
```

If that works but the Streamlit UI does not, the problem is in the UI layer;
if it fails, the problem is configuration, auth or an agent. Capture the
terminal output (with secrets redacted) when filing an issue.
