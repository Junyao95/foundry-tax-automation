#!/usr/bin/env python3
"""Extraction Agent - a Microsoft Foundry hosted agent (Responses protocol).

This is stage 1 of the tax automation workflow. It exposes two tools to the
model and turns a document URL into a normalized JSON payload:

  * ``extract_from_pdf``   - Azure Document Intelligence ``prebuilt-layout``
  * ``extract_from_excel`` - pandas / openpyxl

Output contract (produced by the agent's instructions)::

    {
      "employee_name": "Jane Tan",
      "compensation_items": [
        {"label": "Basic Salary", "amount": 145000},
        {"label": "Transport Allowance", "amount": 12000}
      ]
    }

Run locally with ``python main.py`` (listens on port 8088) or deploy with
``azd up`` from ``agents/extraction-agent/``. Configuration is entirely
environment-driven - see ``docs/configuration.md``.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import requests
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

DOC_INTEL_ENDPOINT = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT", "")
DOC_INTEL_KEY = os.getenv("DOCUMENTINTELLIGENCE_API_KEY", "")
DOWNLOAD_TIMEOUT_SECONDS = 30


def _error(message: str) -> str:
    """Return a structured error so the model can reason about the failure."""
    return json.dumps({"status": "error", "message": message})


def _download(url: str, suffix: str) -> Path:
    """Download a remote document to a temporary file and return its path."""
    response = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
    response.raise_for_status()
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        handle.write(response.content)
    finally:
        handle.close()
    return Path(handle.name)


def extract_from_pdf(file_url: str) -> str:
    """Download a PDF and extract every table cell with Document Intelligence.

    ``file_url`` is typically a short-lived Azure Blob Storage SAS URL. Never
    log or commit the URL: a SAS token grants direct access to the document.
    """
    if not DOC_INTEL_ENDPOINT or not DOC_INTEL_KEY:
        return _error(
            "DOCUMENTINTELLIGENCE_ENDPOINT / DOCUMENTINTELLIGENCE_API_KEY are not configured."
        )

    path: Path | None = None
    try:
        path = _download(file_url, ".pdf")
        client = DocumentIntelligenceClient(
            endpoint=DOC_INTEL_ENDPOINT,
            credential=AzureKeyCredential(DOC_INTEL_KEY),
        )
        with path.open("rb") as document:
            poller = client.begin_analyze_document("prebuilt-layout", body=document)
        result = poller.result()

        cells = [
            cell.content.strip()
            for table in result.tables
            for cell in table.cells
            if cell.content
        ]
        return json.dumps({"status": "success", "extracted_text": cells})
    except Exception as exc:  # noqa: BLE001 - surfaced to the model as JSON
        return _error(f"PDF extraction failed: {exc}")
    finally:
        if path:
            path.unlink(missing_ok=True)


def extract_from_excel(file_url: str) -> str:
    """Download an XLSX file and return its rows as JSON records."""
    path: Path | None = None
    try:
        path = _download(file_url, ".xlsx")
        frame = pd.read_excel(path)
        return json.dumps({"status": "success", "extracted_text": frame.to_json(orient="records")})
    except Exception as exc:  # noqa: BLE001 - surfaced to the model as JSON
        return _error(f"Excel extraction failed: {exc}")
    finally:
        if path:
            path.unlink(missing_ok=True)


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
            "You are an Extraction Agent for a tax automation system. "
            "When the user provides a URL to a PDF or Excel file, use the correct tool to read it. "
            "Extract all compensation items AND the employee name. "
            "Return strictly a JSON object with two keys: 'employee_name' (string) and "
            "'compensation_items' (array of objects with 'label' and 'amount'). "
            "If a tool returns status 'error', explain the failure instead of inventing data."
        ),
        tools=[extract_from_pdf, extract_from_excel],
        default_options={"store": False},
    )

    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
