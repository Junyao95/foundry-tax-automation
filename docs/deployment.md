# Deployment guide (A → Z)

This walks from an empty Azure subscription to a working three-step Streamlit
app. Follow the sections in order. Everything deployment-specific lives in
environment variables — **never commit real values**.

---

## 0. What you will create

| # | Resource | Approx. purpose |
| --- | --- | --- |
| 1 | Microsoft Foundry project + `gpt-4.1-mini` deployment | Model + agent hosting |
| 2 | Foundry hosted agent: `extraction-agent` | PDF/XLSX → compensation JSON |
| 3 | Foundry hosted agent: `sow-builder-agent` | Prior-year comparison → proposed SOW |
| 4 | Azure Document Intelligence | `prebuilt-layout` table extraction |
| 5 | Azure AI Search + `prior-year-sows` index | Prior-year SOW lookup (optional in demo mode) |
| 6 | Azure Blob Storage | Compensation documents, exposed via short-lived SAS URLs |
| 7 | *(Optional)* Azure Key Vault + managed identity | Production secret storage |

---

## 1. Prerequisites

- Azure subscription with permission to create resources and grant role assignments
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) 2.87+ (or any recent version)
- [Azure Developer CLI (`azd`)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd) 1.27.1+
- Python 3.13+ and Git
- Access to the `gpt-4.1-mini` model in your chosen region

```bash
az --version
azd version
python --version
git --version
```

Install the Foundry extension when prompted (or pre-install it):

```bash
azd ext install microsoft.foundry
```

---

## 2. Rotate exposed keys

> **Do this first if you are the original author of the source project.**
> The earlier working copy contained a plaintext Document Intelligence API key
> and a plaintext Azure AI Search admin key inside two `azure.yaml` files, plus
> a pasted Entra bearer token in the Streamlit app. Those values should be
> treated as compromised even though they were never committed to git.
>
> 1. Azure Portal → your **Document Intelligence** resource → *Keys and Endpoint* → **Regenerate Key1 / Key2**.
> 2. Azure Portal → your **Azure AI Search** resource → *Keys* → **Regenerate admin key**.
> 3. Update any deployed app settings that used the old values.
> 4. The bearer token was short-lived, but it encoded your name, tenant ID and
>    group IDs — it has been removed from this repository entirely.

**This cleaned repository contains no credentials.** The steps below use fresh
values that you supply at deploy time.

---

## 3. Sign in

```bash
az login
azd auth login
az account set --subscription "<your-subscription-id>"
```

`DefaultAzureCredential` will use this `az login` session locally. On Azure it
uses a managed identity, so no token is ever stored in the repo.

---

## 4. Configure environment variables

```bash
cp .env.example .env
```

Fill in the values you get from the following steps. Keep `.env` local — it is
gitignored. See [configuration.md](configuration.md) for every variable.

`azd` resolves the `${VAR}` placeholders in each `azure.yaml` from your shell
environment or the active azd environment's `.env` file. Export them before
running `azd up`:

```bash
# Git Bash / macOS / Linux
export DOCUMENTINTELLIGENCE_ENDPOINT="https://<your-doc-intel>.cognitiveservices.azure.com/"
export DOCUMENTINTELLIGENCE_API_KEY="<fresh-key>"
export AZURE_SEARCH_ENDPOINT="https://<your-search>.search.windows.net"
export AZURE_SEARCH_KEY="<fresh-admin-key>"
```

```powershell
# PowerShell
$env:DOCUMENTINTELLIGENCE_ENDPOINT = "https://<your-doc-intel>.cognitiveservices.azure.com/"
$env:DOCUMENTINTELLIGENCE_API_KEY = "<fresh-key>"
$env:AZURE_SEARCH_ENDPOINT = "https://<your-search>.search.windows.net"
$env:AZURE_SEARCH_KEY = "<fresh-admin-key>"
```

---

## 5. Create the supporting Azure resources

You can create these in the Portal or with the CLI. Example CLI shape:

```bash
az group create --name rg-tax-automation --location eastus2

# Document Intelligence (F0 free tier is fine for a demo)
az cognitiveservices account create \
  --name tax-doc-intel --resource-group rg-tax-automation \
  --kind FormRecognizer --sku F0 --location eastus2 --yes

# Blob storage for compensation documents
az storage account create --name <unique-storage-name> \
  --resource-group rg-tax-automation --location eastus2 --sku Standard_LRS
```

Copy the Document Intelligence endpoint and key into `.env` as
`DOCUMENTINTELLIGENCE_ENDPOINT` / `DOCUMENTINTELLIGENCE_API_KEY`.

### Generate a short-lived SAS URL for a test document

```bash
az storage container create --name compensation --account-name <unique-storage-name>
az storage blob upload --account-name <unique-storage-name> --container-name compensation \
  --file ./sample.pdf --name sample.pdf

az storage blob generate-sas --account-name <unique-storage-name> \
  --container-name compensation --name sample.pdf \
  --permissions r --expiry "<utc-expiry-within-1-hour>" --https-only --output tsv
```

Prefix the result with the blob URL and paste the full URL into the Streamlit
app. **SAS URLs are credentials**: use read-only, short expiry, and never paste
them into issues, screenshots or logs.

---

## 6. Deploy the Extraction Agent

Each agent is an independent `azd` app. Run from its own directory:

```bash
cd agents/extraction-agent
azd init            # only if no azd environment exists yet
azd up              # provision + build container remotely + deploy
cd ../..
```

`azd` will:
1. Provision the `ai-project` service and the `gpt-4.1-mini` deployment
   (GlobalStandard, capacity 10) declared in `azure.yaml`.
2. Build the container from `src/Dockerfile` with
   `dependencyResolution: remote_build`.
3. Deploy the hosted agent on 0.5 vCPU / 1 GiB, listening on port 8088.

Test it locally before deploying, if you prefer:

```bash
azd ai agent run                              # http://localhost:8088
azd ai agent invoke --local "Extract data from: <SAS-URL>"
```

---

## 7. Deploy the SOW Builder Agent

```bash
cd agents/sow-builder-agent
azd init
azd up
cd ../..
```

> **Sharing one Foundry project:** each manifest declares its own `ai-project`
> service, so two `azd up` runs may create two projects and two model
> deployments. To reuse the first project, set `FOUNDRY_PROJECT_ENDPOINT` to
> the existing project and run `azd deploy` (skipping the provisioning step)
> for the second agent. Check `azd`'s planned changes before confirming.

---

## 8. Discover the two agent endpoint URLs

After deployment, get the Responses-protocol URLs from the Portal
(**Foundry project → Agents → your agent → Endpoint**) or from `azd`:

```bash
azd ai agent list        # if available in your azd extension version
```

They look like:

```
https://<account>.services.ai.azure.com/api/projects/<project>/agents/<agent-name>/endpoint/protocols/openai/responses?api-version=v1
```

Set `EXTRACTION_AGENT_ENDPOINT` and `SOW_AGENT_ENDPOINT` in `.env`, and set
`FOUNDRY_PROJECT_ENDPOINT` to the project URL (without the `/agents/...` part).

---

## 9. Create the prior-year SOW index (optional)

Skip this for demo mode: with `AZURE_SEARCH_ENDPOINT` / `AZURE_SEARCH_KEY`
empty, the tool returns clearly labelled `_source: "demo-data"` fixtures.

For a real lookup, create an Azure AI Search resource and an index named
`prior-year-sows` with at least these fields:

| Field | Type | Attributes |
| --- | --- | --- |
| `employee_name` | `Edm.String` | searchable, filterable |
| `label` | `Edm.String` | searchable |
| `amount` | `Edm.Double` | filterable, sortable |
| `year` | `Edm.Int32` | filterable |

Then set `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_KEY` and
`AZURE_SEARCH_INDEX_NAME` in `.env`.

---

## 10. Run the Streamlit app

```bash
python -m venv .venv
source .venv/Scripts/activate           # Windows Git Bash
# .venv\Scripts\activate               # Windows CMD/PowerShell
pip install -r webapp/requirements.txt

# Load .env into the shell (Git Bash)
set -a; source ./.env; set +a

streamlit run webapp/app.py
```

Open the URL Streamlit prints (normally <http://localhost:8501>).

> `python-dotenv` is intentionally not a dependency. Either export the
> variables as above or use your shell/IDE's env-file support. Never commit a
> filled-in `.env`.

CLI equivalent for quick debugging:

```bash
python webapp/orchestrator.py
```

---

## 11. Smoke test

| Check | Expected |
| --- | --- |
| `azd ai agent invoke --local "<SAS-URL>"` (in `agents/extraction-agent`) | JSON with `employee_name` and `compensation_items` |
| `azd ai agent invoke --local "Employee Jane Tan ... build the SOW"` (in `agents/sow-builder-agent`) | Proposed SOW, optionally with `REQUIRES_HUMAN_REVIEW` |
| Streamlit step 1 → step 2 | Proposed SOW rendered as JSON |
| Click **Reject** | Returns to step 1, nothing computed |
| Click **Approve** | Tax JSON + downloadable A4 PDF |

See [api.md](api.md) for direct curl examples and
[troubleshooting.md](troubleshooting.md) if anything fails.

---

## 12. Host the web app on Azure (optional)

The app is a normal Python process. Common options:

- **Azure Container Apps** — containerize `webapp/`, enable a system-assigned
  managed identity, inject settings as secrets/Key Vault references.
- **Azure App Service (Linux, Python 3.13)** — startup command:
  `python -m streamlit run webapp/app.py --server.port 8000 --server.address 0.0.0.0`.

In either case grant the managed identity the **Cognitive Services OpenAI
User** / **Azure AI Developer** roles on the Foundry project, and move the two
service keys into Key Vault. See
[configuration.md#4-secret-handling](configuration.md#4-secret-handling).

---

## 13. Cost notes

The largest recurring cost is the `gpt-4.1-mini` deployment capacity declared
in each `azure.yaml` (GlobalStandard, capacity 10). Two `azd up` runs may
create **two** such deployments. For a portfolio demo:

- Reuse a single model deployment (see step 7).
- Reduce `sku.capacity` during development.
- Use F0/free tiers for Document Intelligence and the smallest AI Search tier.
- Run `azd down` when finished (next section).

Always check the [Azure pricing calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
for your region, and set a budget alert on the resource group.

---

## 14. Teardown

```bash
cd agents/sow-builder-agent && azd down --force --purge && cd ../..
cd agents/extraction-agent && azd down --force --purge && cd ../..
az group delete --name rg-tax-automation --yes --no-wait
```

`azd down` removes the hosted agents and their model deployments; the resource
group deletion cleans up Document Intelligence, Storage and AI Search.
