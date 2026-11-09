#!/usr/bin/env python3
"""Streamlit front end for the Foundry tax automation workflow.

Run from the repository root::

    streamlit run webapp/app.py

Three steps:
  1. Upload  - paste a short-lived Blob SAS URL to a PDF/XLSX compensation file.
  2. Review  - inspect the proposed SOW, explicitly approve or reject it.
  3. Result  - view the tax computation and download the A4 PDF package.

Step 2 is the human-in-the-loop control: no tax computation runs without an
explicit approval. All endpoints and credentials come from the environment -
see ``docs/configuration.md``.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import streamlit as st
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    ConfigurationError,
    build_tax_input,
    call_hosted_agent,
    clean_json_string,
    credential,
    demo_fallback_enabled,
    demo_sow_items,
    endpoints,
    generate_tax_pdf,
    load_tax_prompt,
    parse_sow_items,
)

st.set_page_config(page_title="Tax Automation", page_icon="📊", layout="centered")


def _show_sow(raw: str) -> None:
    try:
        st.json(json.loads(clean_json_string(raw)))
    except (json.JSONDecodeError, TypeError):
        st.warning("The SOW agent did not return valid JSON. Showing the raw response:")
        st.info(raw)


def main() -> None:
    st.title("📊 Employee Tax Automation")
    st.caption("Two Microsoft Foundry hosted agents · human-in-the-loop approval · PDF deliverable")

    if "step" not in st.session_state:
        st.session_state.step = 1

    with st.sidebar:
        st.markdown("### Workflow")
        st.markdown("1. Upload document URL  \n2. Review & approve SOW  \n3. Download tax package")
        if st.button("Start new employee"):
            st.session_state.step = 1
            st.rerun()

    try:
        eps = endpoints()
    except ConfigurationError as exc:
        st.error(str(exc))
        st.info("See [docs/configuration.md](docs/configuration.md) for setup.")
        st.stop()

    # ------------------------------------------------------------------ Step 1
    if st.session_state.step == 1:
        st.subheader("Step 1 · Upload compensation file")
        sas_url = st.text_input("Paste the Blob Storage SAS URL of the PDF or XLSX file:")
        st.caption("SAS URLs grant direct file access. Use short-lived, read-only tokens and never paste them into issues or logs.")

        if st.button("Extract & build SOW", type="primary"):
            if not sas_url:
                st.error("Please provide a document URL.")
                return
            with st.spinner("Extracting data and building the proposed SOW..."):
                try:
                    cred = credential()
                    extracted_raw = asyncio.run(
                        call_hosted_agent(
                            eps.extraction,
                            f"Extract all compensation data from this link: {sas_url}",
                            cred,
                        )
                    )
                    try:
                        employee_name = json.loads(clean_json_string(extracted_raw)).get(
                            "employee_name", "Unknown Employee"
                        )
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        employee_name = "Unknown Employee"

                    sow_prompt = (
                        f"Employee Name: {employee_name}. "
                        f"Here is the extracted data: {extracted_raw}. "
                        "Please build the proposed SOW."
                    )
                    sow_raw = asyncio.run(call_hosted_agent(eps.sow, sow_prompt, cred))

                    st.session_state.sow_data = sow_raw
                    st.session_state.employee_name = employee_name
                    st.session_state.step = 2
                    st.rerun()
                except Exception as exc:  # noqa: BLE001 - surface to the UI
                    st.error(f"Extraction or SOW build failed: {exc}")

    # ------------------------------------------------------------------ Step 2
    elif st.session_state.step == 2:
        st.subheader("Step 2 · Review & approve the proposed SOW")
        st.caption(f"Employee: **{st.session_state.employee_name}**")

        raw = st.session_state.sow_data
        if "REQUIRES_HUMAN_REVIEW" in raw:
            st.warning("The SOW builder flagged one or more new items for human review. Verify them before approving.")
        _show_sow(raw)

        col1, col2 = st.columns(2)
        with col1:
            approve = st.button("✅ Approve & calculate tax", type="primary")
        with col2:
            reject = st.button("❌ Reject")
        if reject:
            st.info("Workflow stopped. The SOW was rejected by the reviewer.")
            st.session_state.step = 1
            st.rerun()
        if approve:
            with st.spinner("Computing tax..."):
                try:
                    cred = credential()
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

                    try:
                        items = parse_sow_items(raw)
                    except (json.JSONDecodeError, TypeError, ValueError):
                        items = []

                    if not items:
                        if not demo_fallback_enabled():
                            raise ValueError(
                                "The SOW agent did not return parseable JSON and DEMO_FALLBACK is disabled."
                            )
                        st.warning("SOW parsing failed. Using demo data - do not use this output for real tax work.")
                        items = demo_sow_items()

                    response = asyncio.run(tax_agent.run(json.dumps(build_tax_input(items))))
                    st.session_state.final_tax = response.text
                    st.session_state.step = 3
                    st.rerun()
                except Exception as exc:  # noqa: BLE001 - surface to the UI
                    st.error(f"Tax calculation failed: {exc}")

    # ------------------------------------------------------------------ Step 3
    elif st.session_state.step == 3:
        st.subheader("Step 3 · Final tax calculation")
        st.success("Tax calculation complete.")
        raw_tax = st.session_state.final_tax
        try:
            st.json(json.loads(clean_json_string(raw_tax)))
        except (json.JSONDecodeError, TypeError):
            st.info(raw_tax)

        st.markdown("---")
        st.markdown("### Download deliverable")
        try:
            pdf_bytes = generate_tax_pdf(raw_tax)
            safe_name = "".join(
                char for char in st.session_state.employee_name if char.isalnum() or char in " _-"
            ).strip().replace(" ", "_") or "Employee"
            st.download_button(
                label="📄 Download tax package (A4 PDF)",
                data=pdf_bytes,
                file_name=f"Tax_Package_{safe_name}.pdf",
                mime="application/pdf",
                type="primary",
            )
        except Exception as exc:  # noqa: BLE001 - surface to the UI
            st.error(f"Could not generate the PDF: {exc}")


# Streamlit executes this file as a script; call the entry point directly so
# it renders regardless of how the module name is set by the runner.
main()
