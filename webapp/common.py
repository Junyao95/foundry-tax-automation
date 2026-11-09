"""Shared helpers for the Streamlit UI (``app.py``) and the CLI orchestrator.

Both clients call the two *deployed* Foundry hosted agents over the OpenAI
Responses protocol, then run a local tax-computation agent through
``FoundryChatClient``. Authentication uses ``DefaultAzureCredential`` (an
``az login`` session locally, managed identity on Azure) - this repository
contains no tokens, keys or tenant-specific URLs.

See ``docs/configuration.md`` for every environment variable and
``docs/api.md`` for the wire format.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
from azure.identity import DefaultAzureCredential

TOKEN_SCOPE = "https://ai.azure.com/.default"
REQUEST_TIMEOUT_SECONDS = 120.0

# Placeholder only. Replace with the real legal entity in your own deployment.
DEFAULT_EMPLOYER = "Example Employer Pte Ltd"


class ConfigurationError(RuntimeError):
    """Raised when a required environment variable is missing."""


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigurationError(
            f"Missing required environment variable {name!r}. "
            "Copy .env.example to .env and fill it in; see docs/configuration.md."
        )
    return value


@dataclass(frozen=True)
class Endpoints:
    project: str
    extraction: str
    sow: str
    model: str


def endpoints() -> Endpoints:
    """Resolve all deployment-specific URLs from the environment."""
    return Endpoints(
        project=require_env("FOUNDRY_PROJECT_ENDPOINT"),
        extraction=require_env("EXTRACTION_AGENT_ENDPOINT"),
        sow=require_env("SOW_AGENT_ENDPOINT"),
        model=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini"),
    )


def credential():
    """Return an Azure credential. Never paste a bearer token into source."""
    return DefaultAzureCredential()


async def call_hosted_agent(endpoint_url: str, prompt: str, cred) -> str:
    """Invoke a hosted agent's Responses endpoint and return its message text."""
    token = cred.get_token(TOKEN_SCOPE)
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(endpoint_url, headers=headers, json={"input": prompt})
        response.raise_for_status()
        data = response.json()

    for item in data.get("output", []):
        if item.get("type") == "message":
            try:
                return item["content"][0]["text"]
            except (KeyError, IndexError, TypeError):
                continue
    return json.dumps(data)


def clean_json_string(raw: str) -> str:
    """Strip Markdown fences and leading prose so ``json.loads`` can succeed."""
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    candidate = match.group(1) if match else raw.strip()
    starts = [i for i in (candidate.find("{"), candidate.find("[")) if i >= 0]
    return candidate[min(starts):] if starts else candidate


def load_tax_prompt() -> str:
    """Load the tax-computation system prompt.

    The bundled ``tax_agent.md`` is a TEMPLATE, not tax advice. Provide your
    own jurisdiction-specific rules via ``TAX_AGENT_PROMPT_PATH`` before using
    this workflow with real data.
    """
    override = os.getenv("TAX_AGENT_PROMPT_PATH")
    path = Path(override) if override else Path(__file__).with_name("tax_agent.md")
    if not path.is_file():
        raise ConfigurationError(f"Tax prompt not found at {path}.")
    return path.read_text(encoding="utf-8").strip()


def parse_sow_items(raw_sow: str) -> list[dict]:
    """Normalize a proposed SOW JSON payload into the tax agent's input schema."""
    data = json.loads(clean_json_string(raw_sow))
    items = data if isinstance(data, list) else data.get("proposed_SOW", [])

    formatted: list[dict] = []
    for item in items:
        amount_text = str(item.get("Amount (SGD)", item.get("amount", "0")))
        digits = re.sub(r"[^\d.\-]", "", amount_text)
        formatted.append(
            {
                "label": item.get("Description", item.get("label", "Unknown")),
                "amount": float(digits) if digits else 0.0,
                "employer": DEFAULT_EMPLOYER,
                "tax_borne_by_employer": False,
            }
        )
    return formatted


def demo_sow_items() -> list[dict]:
    """Clearly-labelled demo data for local development and UI screenshots."""
    return [
        {"label": label, "amount": amount, "employer": DEFAULT_EMPLOYER, "tax_borne_by_employer": False}
        for label, amount in [
            ("Basic Salary", 145000.0),
            ("Performance Bonus", 25000.0),
            ("Transport Allowance", 12000.0),
            ("Housing Allowance", 18000.0),
            ("Gym Membership", 1200.0),
        ]
    ]


def demo_fallback_enabled() -> bool:
    return os.getenv("DEMO_FALLBACK", "true").strip().lower() in {"1", "true", "yes"}


def build_tax_input(items: list[dict], tax_year: str = "YA2024") -> dict:
    """Assemble the payload expected by the tax-computation agent."""
    return {
        "sow_items": items,
        "tot_method": "none",
        "deductions": [],
        "reliefs": [{"label": "Personal Reliefs", "amount": 7000}],
        "tax_year": tax_year,
        "residency": "resident",
    }


def generate_tax_pdf(tax_data_str: str) -> bytes:
    """Render the final tax computation as a one-page A4 PDF deliverable."""
    from fpdf import FPDF

    try:
        data = json.loads(clean_json_string(tax_data_str))
    except (json.JSONDecodeError, TypeError):
        data = {
            "gross_income": "Error",
            "tax_payable_final": "Error",
            "chargeable_income_final": "Error",
            "audit_trail": ["The agent did not return valid JSON."],
        }

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, txt="CONFIDENTIAL TAX COMPUTATION PACKAGE", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 5, txt="Year of Assessment: see request payload", ln=True, align="C")
    pdf.ln(10)

    def add_row(label: str, value: str, bold: bool = False) -> None:
        pdf.set_font("Arial", "B" if bold else "", 10)
        pdf.cell(120, 8, txt=label, border=0)
        pdf.cell(70, 8, txt=f"SGD {value}", border=0, align="R", ln=True)

    def fmt(value) -> str:
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, txt="1. TAX COMPUTATION SUMMARY", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    add_row("Total Gross Income", fmt(data.get("gross_income", "0")))
    add_row("Less: Total Deductions", f"({fmt(data.get('total_deductions', '0'))})")
    add_row("Less: Total Reliefs Allowed", f"({fmt(data.get('total_reliefs_allowed', '0'))})")
    pdf.ln(2)
    add_row("Final Chargeable Income", fmt(data.get("chargeable_income_final", "0")), bold=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, txt="2. TAX PAYABLE", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    add_row("Tax on Chargeable Income", fmt(data.get("tax_payable_final", "0")))
    add_row("Less: Tax Borne by Employer (TOT)", f"({fmt(data.get('tax_allowance', '0'))})")
    pdf.ln(2)
    add_row("FINAL TAX PAYABLE BY EMPLOYEE", fmt(data.get("employee_borne_portion", "0")), bold=True)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, txt="3. AUDIT TRAIL", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", size=9)
    for step in data.get("audit_trail", []):
        ascii_step = str(step).encode("ascii", "ignore").decode("ascii")
        pdf.multi_cell(0, 5, txt=f"- {ascii_step}")
        pdf.ln(1)

    return bytes(pdf.output())
