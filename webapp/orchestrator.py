#!/usr/bin/env python3
"""Command-line version of the tax automation workflow.

Useful for debugging the two hosted agents without the Streamlit UI::

    az login
    python webapp/orchestrator.py

The flow mirrors ``app.py`` but asks for approval in the terminal. It is a
diagnostic tool, not a production entry point.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    ConfigurationError,
    build_tax_input,
    call_hosted_agent,
    clean_json_string,
    credential,
    endpoints,
    load_tax_prompt,
    parse_sow_items,
)


async def main() -> None:
    print("🚀 Starting tax automation workflow...\n")

    try:
        eps = endpoints()
    except ConfigurationError as exc:
        print(f"❌ {exc}")
        return

    cred = credential()
    sas_url = input("📄 Paste the Blob Storage SAS URL of the PDF/XLSX to process:\n> ").strip()
    if not sas_url:
        print("🛑 No URL supplied.")
        return

    # --- Step 1: extraction agent ------------------------------------------
    print("\n⏳ [1/3] Sending the document to the Extraction Agent...")
    try:
        extracted_raw = await call_hosted_agent(
            eps.extraction,
            f"Extract all compensation data from this link: {sas_url}",
            cred,
        )
        extracted = json.loads(clean_json_string(extracted_raw))
        employee_name = extracted.get("employee_name", "Unknown Employee")
        print(f"✅ Extraction complete. Employee: {employee_name}")
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Extraction failed: {exc}")
        return

    # --- Step 2: SOW builder agent -----------------------------------------
    print("\n⏳ [2/3] Sending the extracted data to the SOW Builder Agent...")
    sow_prompt = (
        f"Employee Name: {employee_name}. "
        f"Here is the extracted data: {extracted_raw}. "
        "Please build the proposed SOW."
    )
    try:
        sow_raw = await call_hosted_agent(eps.sow, sow_prompt, cred)
        print("✅ Proposed SOW generated.")
    except Exception as exc:  # noqa: BLE001
        print(f"❌ SOW Builder failed: {exc}")
        return

    # --- Step 3: human-in-the-loop approval --------------------------------
    print("\n" + "=" * 60)
    print("⚠️  HUMAN APPROVAL REQUIRED: PROPOSED SOW")
    print("=" * 60)
    print(sow_raw)
    print("=" * 60 + "\n")
    if "REQUIRES_HUMAN_REVIEW" in sow_raw:
        print("⚠️  New items were flagged for review. Verify them before approving.")
    approval = input("🤔 Approve this SOW and proceed to tax computation? (yes/no): ")
    if approval.strip().lower() not in {"y", "yes"}:
        print("🛑 Workflow paused. SOW rejected by the human reviewer.")
        return

    # --- Step 4: tax computation agent -------------------------------------
    print("\n⏳ [3/3] Sending the approved SOW to the Tax Computation Agent...")
    try:
        items = parse_sow_items(sow_raw)
        if not items:
            raise ValueError("The SOW agent did not return any parseable line items.")

        client = FoundryChatClient(
            project_endpoint=eps.project,
            model=eps.model,
            credential=cred,
        )
        tax_agent = Agent(
            client=client,
            instructions=load_tax_prompt(),
            name="TaxComputationAgent",
        )
        response = await tax_agent.run(json.dumps(build_tax_input(items)))
        print("\n✅ FINAL TAX CALCULATION:")
        print(response.text)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Tax calculation failed: {exc}")
        print("The SOW JSON was invalid or missing. Workflow halted.")


if __name__ == "__main__":
    asyncio.run(main())
