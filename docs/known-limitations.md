# Known limitations

This is a working prototype / portfolio project, not a production tax system.
Being explicit about the gaps is part of the design: the human approval step
exists precisely because the automated parts are not authoritative.

---

## Functional

| Area | Current state | What production would need |
| --- | --- | --- |
| **Tax rules** | `webapp/tax_agent.md` is a **template** describing the expected input/output schema. The original project's private, jurisdiction-specific prompt is not included. | Rules authored and reviewed by a qualified tax professional; versioned prompts; evaluation against a labelled golden set. |
| **Prior-year lookup** | Falls back to `_source: "demo-data"` fixtures when AI Search is unconfigured, and assumes an index with `employee_name`, `label`, `amount`, `year`. | A populated index, ingestion pipeline, and validation that the lookup actually matched the right employee/year. |
| **SOW output validation** | Model-generated JSON parsed tolerantly (`Description`/`Amount (SGD)` or `label`/`amount`, fences stripped). No schema enforcement. | Pydantic/JSON-Schema validation with a repair-and-retry or a hard failure. |
| **Demo fallback** | `DEMO_FALLBACK=true` by default lets the UI substitute sample line items when SOW parsing fails. | Set `DEMO_FALLBACK=false`; fail loudly. Demo output must never be used for real tax work. |
| **Example values** | `YA2024`, SGD, `Example Employer Pte Ltd`, a 7000 personal relief, and sample salary figures are placeholders. | Real tax year, currency, legal entity, reliefs and residency rules. |
| **Stateless agents** | Both hosted agents use `store: False`; no multi-turn memory. Fine for single-document processing. | Explicit conversation/session state if multi-turn refinement is needed. |
| **Extraction fidelity** | `prebuilt-layout` returns every table cell as flat text; the model then infers labels, amounts and the employee name. | Layout-aware parsing, confidence scores, and a human verification step for extraction. |
| **PDF** | Single-page A4, core Arial font, audit trail coerced to ASCII. | Multi-page layout, Unicode font, branding, digital signature, retention policy. |

## Operational

| Area | Current state | What production would need |
| --- | --- | --- |
| **Streamlit auth** | No sign-in; anyone who can reach the app can run the workflow. | Entra ID / App Service authentication, role-based reviewer permissions. |
| **Secrets** | Two service keys injected as container env vars; fine for a demo. | Key Vault + managed identity / RBAC — see [configuration.md](configuration.md#4-secret-handling). |
| **SAS URLs** | Pasted manually by the user; no validation of expiry or scope. | Server-side upload, short-lived read-only tokens, automatic expiry, no URL in logs. |
| **Deployment topology** | Two independent `azd` apps; two `azd up` runs may create two projects and two model deployments (extra cost). | A single combined manifest with a shared project and explicit capacity. |
| **Observability** | Relies on Foundry's built-in logs/traces; no app-level telemetry. | Structured logging, correlation IDs per employee, alerting, PII-safe traces. |
| **Tests / CI** | CI only compiles Python and scans for obvious secret patterns. No unit or integration tests. | Unit tests for parsing/PDF helpers, mocked agent tests, Foundry evaluation harness. |
| **Error recovery** | Failures are surfaced to the UI; no retries, idempotency or queue. | Retry with backoff, idempotency keys, durable workflow orchestration. |
| **Compliance** | No data retention, residency or audit-log guarantees. | Legal review — employee compensation and tax data are sensitive personal data. |

---

## Deliberate exclusions

- The three credentials present in the original working copy (Document
  Intelligence key, AI Search admin key, pasted Entra token) are **not** in
  this repository. Rotate them — see [deployment.md §2](deployment.md#2-rotate-exposed-keys).
- Tenant-specific resource URLs, subscription IDs and account names are
  replaced with `<placeholders>` everywhere.
- The original project's private tax prompt and any real employee data are not
  included.

---

## Disclaimer

This software is provided for demonstration purposes under the
[MIT License](../LICENSE). It does not constitute tax, legal or financial
advice. Do not use it to file, compute or approve real tax positions without
professional review. See the license's warranty disclaimer.
