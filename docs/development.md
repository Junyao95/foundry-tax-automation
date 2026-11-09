# Development guide

## 1. Local setup

```bash
git clone https://github.com/Junyao95/foundry-tax-automation.git
cd foundry-tax-automation

python -m venv .venv
source .venv/Scripts/activate          # Windows Git Bash
# .venv\Scripts\activate              # CMD / PowerShell

# Hosted agents and the web app have separate dependency sets
pip install -r agents/extraction-agent/src/requirements.txt
pip install -r agents/sow-builder-agent/src/requirements.txt
pip install -r webapp/requirements.txt

cp .env.example .env                  # fill in your own values
set -a; source ./.env; set +a         # Git Bash / Linux / macOS
az login
```

> A single virtualenv is fine for local development. In Azure, each agent is
> built from its own `requirements.txt` inside its own container, and the web
> app is deployed separately.

---

## 2. Running the hosted agents locally

Each agent directory is an `azd` app. Use `azd` for the full experience
(including remote builds), or run `main.py` directly for a quick syntax/logic
check.

```bash
# Option A - azd (recommended)
cd agents/extraction-agent
azd auth login
azd ai agent run                                        # http://localhost:8088
# in a second terminal, from the same folder:
azd ai agent invoke --local "Extract data from: <SAS-URL>"
azd deploy                                              # deploy to Foundry
azd ai agent invoke "Extract data from: <SAS-URL>"      # invoke deployed agent
```

```bash
# Option B - plain Python (needs FOUNDRY_PROJECT_ENDPOINT + model name)
cd agents/extraction-agent/src
python main.py
```

Repeat in `agents/sow-builder-agent/`. Both servers listen on port 8088, so
**do not run them at the same time locally** unless you change one port.

### VS Code / Foundry Toolkit

The upstream Microsoft sample also supports the **Foundry Toolkit** VS Code
extension and its Agent Inspector (`F5` to debug, then
*Foundry Toolkit: Open Agent Inspector*). This repo keeps the same
`ResponsesHostServer` entry-point structure, so that workflow still applies.

---

## 3. Running the client apps

```bash
# Web UI (the main deliverable)
streamlit run webapp/app.py

# CLI equivalent, useful for debugging agent responses
python webapp/orchestrator.py
```

`webapp/common.py` is imported by both via a `sys.path` insert, so run them
from the repository root as shown.

---

## 4. Where to make changes

| Goal | File |
| --- | --- |
| Change extraction behaviour or tools | `agents/extraction-agent/src/main.py` |
| Change SOW comparison rules or prior-year lookup | `agents/sow-builder-agent/src/main.py` |
| Change the UI flow | `webapp/app.py` |
| Change the CLI flow | `webapp/orchestrator.py` |
| Change agent invocation / JSON normalization / PDF | `webapp/common.py` |
| Supply real tax rules | `webapp/tax_agent.md` or `TAX_AGENT_PROMPT_PATH` |
| Change model / container size / injected env | `agents/*/azure.yaml` |
| Change container build | `agents/*/src/Dockerfile` + `requirements.txt` |

After any source change to a hosted agent, redeploy with
`cd agents/<agent> && azd deploy`.

---

## 5. Adding a tool to a hosted agent

Tools are plain Python functions with type hints and a docstring; the Agent
Framework exposes them to the model automatically.

```python
def lookup_exchange_rate(currency: str) -> str:
    """Return the current SGD exchange rate for a currency code."""
    return json.dumps({"currency": currency, "rate": 1.0})

agent = Agent(client=client, instructions="...", tools=[lookup_exchange_rate])
```

Guidelines used in this repo:

- Return **JSON strings**, not Python objects, so the model gets a stable shape.
- Return `{"status": "error", "message": "..."}` instead of raising — the model
  can then explain the failure rather than hallucinate.
- Never log or return secrets, SAS URLs or raw bearer tokens.
- Clean up temporary files in a `finally` block.
- Add the new dependency to that agent's `requirements.txt` (the Dockerfile
  installs it).

---

## 6. Code style

- Python 3.13, UTF-8, 4-space indentation.
- Type hints on public functions; `from __future__ import annotations`.
- No credentials, tenant IDs or resource URLs in source.
- Prefer small, pure helpers in `webapp/common.py` over duplicated logic.
- Keep Markdown code fences balanced and use relative links between docs.

A minimal CI workflow (`.github/workflows/ci.yml`) compiles all Python files
and blocks obvious secret patterns on every push.

---

## 7. Manual test checklist

Before opening a PR, walk through:

- [ ] `python -m compileall -q agents webapp` passes
- [ ] `grep` finds no real keys, tokens or SAS URLs in tracked files
- [ ] `azd ai agent invoke --local` works for each agent
- [ ] Streamlit step 1 produces a proposed SOW
- [ ] Step 2 shows a `REQUIRES_HUMAN_REVIEW` warning for a novel item
- [ ] **Reject** stops the workflow with no tax computation
- [ ] **Approve** produces JSON and a downloadable PDF
- [ ] `DEMO_FALLBACK=false` makes unparseable SOW JSON fail loudly
- [ ] README links and screenshot images still resolve (see [shot list](screenshots.md))

---

## 8. Suggested next improvements

1. Replace `tax_agent.md` with reviewed, jurisdiction-specific rules.
2. Add `pydantic` schemas to validate agent JSON instead of tolerant parsing.
3. Add unit tests for `clean_json_string`, `parse_sow_items` and
   `generate_tax_pdf`, plus a mocked agent-invocation test.
4. Add a Foundry evaluation harness comparing proposed SOWs against a labelled
   golden set.
5. Move both keys to Key Vault / managed identity and add Streamlit
   authentication.
6. Add a single combined `azd` manifest (or a root `azure.yaml`) that deploys
   both agents plus the web app in one `azd up`.
