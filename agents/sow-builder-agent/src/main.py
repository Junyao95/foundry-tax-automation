#!/usr/bin/env python3
"""SOW Builder Agent - a Microsoft Foundry hosted agent (Responses protocol).

This is stage 2 of the tax automation workflow. It receives the JSON produced
by the Extraction Agent, looks up the employee's prior-year Schedule of Work,
compares the two sets of line items, and flags anything new as
``REQUIRES_HUMAN_REVIEW`` before emitting a proposed SOW table.

The comparison is deliberately conservative: a human must approve the result
in the Streamlit app before any tax computation runs. See
``docs/architecture.md`` for the full flow.
"""
from __future__ import annotations

import json
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "prior-year-sows")


def search_prior_year_sow(employee_name: str) -> str:
    """Return prior-year SOW line items for an employee as a JSON string.

    Uses Azure AI Search when ``AZURE_SEARCH_ENDPOINT`` and
    ``AZURE_SEARCH_KEY`` are configured. Otherwise returns clearly labelled
    demo data so the agent can be exercised locally without cloud resources.

    The index is expected to expose at least ``employee_name``, ``label`` and
    ``amount`` fields. See ``docs/deployment.md`` for index setup.
    """
    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        return json.dumps(
            {
                "employee_name": employee_name,
                "prior_year_items": [
                    {"label": "Basic Salary", "amount": 50000},
                    {"label": "Transport Allowance", "amount": 1200},
                ],
                "notes": "Excluded: Club Membership. Included: Transport Allowance.",
                "_source": "demo-data",
            }
        )

    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient

        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX,
            credential=AzureKeyCredential(SEARCH_KEY),
        )
        items = [
            {
                "label": doc.get("label", "Unknown"),
                "amount": doc.get("amount", 0),
            }
            for doc in client.search(search_text=employee_name, top=20)
        ]
        return json.dumps(
            {
                "employee_name": employee_name,
                "prior_year_items": items,
                "_source": "azure-ai-search",
            }
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to the model as JSON
        return json.dumps(
            {"status": "error", "message": f"Prior-year lookup failed: {exc}"}
        )


def main() -> None:
    model_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.getenv("FOUNDRY_MODEL_NAME")
    project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    if not model_name:
        raise RuntimeError("Set AZURE_AI_MODEL_DEPLOYMENT_NAME (see docs/configuration.md).")
    if not project_endpoint:
        raise RuntimeError("Set FOUNDRY_PROJECT_ENDPOINT (see docs/configuration.md).")

    client = FoundryChatClient(
        project_endpoint=project_endpoint,
        model=model_name,
        credential=DefaultAzureCredential(),
    )

    agent = Agent(
        client=client,
        instructions=(
            "You are a SOW (Schedule of Work) Builder for a tax automation system. "
            "You receive current-year compensation data extracted from a document. "
            "Use the search_prior_year_sow tool to look up last year's items for this employee. "
            "Compare the current-year items with the prior-year items. "
            "If an item appears in the current year but NOT in the prior year, mark it "
            "'REQUIRES_HUMAN_REVIEW'. Never silently drop or invent an item. "
            "If the lookup returns status 'error', say so and return no proposed SOW. "
            "Output the final proposed SOW table as JSON."
        ),
        tools=[search_prior_year_sow],
        default_options={"store": False},
    )

    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
