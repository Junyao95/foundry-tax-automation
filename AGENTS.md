# Coding Agent Instructions

This project contains **two Microsoft Foundry hosted agents** and a Streamlit
client application. Read [`docs/architecture.md`](docs/architecture.md) before
changing the workflow.

## Key files

| Path | Role |
| --- | --- |
| `agents/extraction-agent/azure.yaml` | azd manifest for agent #1 |
| `agents/extraction-agent/src/main.py` | Agent #1 entry point + tools |
| `agents/sow-builder-agent/azure.yaml` | azd manifest for agent #2 |
| `agents/sow-builder-agent/src/main.py` | Agent #2 entry point + tools |
| `webapp/app.py` | Streamlit UI (the final application) |
| `webapp/orchestrator.py` | CLI equivalent |
| `webapp/common.py` | Shared helpers |
| `.env.example` | All configuration variables |
| `docs/` | Full documentation set |

## Non-negotiable rules

1. **No secrets in source.** No keys, tokens, SAS URLs, tenant IDs or
   tenant-specific URLs. Use `os.getenv` and `DefaultAzureCredential`.
2. **Do not remove or bypass the human approval gate** in `webapp/app.py`
   step 2 / `webapp/orchestrator.py`. No tax computation runs before approval.
3. **Do not enable demo fallback silently.** Demo data is only allowed when
   `DEMO_FALLBACK=true`, and it must be visibly labelled in the UI.
4. Keep `agents/*/src/requirements.txt` in sync with imports — the Dockerfiles
   install only those files.
5. Update `docs/configuration.md` whenever an environment variable changes,
   and `docs/architecture.md` whenever a data contract changes.

## Development workflow

Each agent is an independent `azd` app:

```bash
cd agents/extraction-agent   # or agents/sow-builder-agent
azd ai agent run                           # local, http://localhost:8088
azd ai agent invoke --local "your message" # test locally
azd deploy                                 # deploy to Foundry
azd ai agent invoke "your message"         # invoke deployed agent
```

Client apps run from the repository root:

```bash
streamlit run webapp/app.py
python webapp/orchestrator.py
```

## References

- [Hosted agents overview](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Foundry samples](https://github.com/microsoft-foundry/foundry-samples)
- [Microsoft Foundry Skill](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/use-microsoft-foundry-skill)
