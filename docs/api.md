# API reference

Both hosted agents expose the **OpenAI Responses protocol (v2.0.0)** via
`ResponsesHostServer`. This document describes the wire format, both agent
contracts and the tool signatures. For the higher-level flow see
[architecture.md](architecture.md).

---

## 1. Endpoint and authentication

A deployed agent's endpoint has this shape:

```
https://<account>.services.ai.azure.com/api/projects/<project>/agents/<agent-name>/endpoint/protocols/openai/responses?api-version=v1
```

All calls require an Entra ID bearer token for the scope
`https://ai.azure.com/.default`. In code this is obtained with
`DefaultAzureCredential`:

```python
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
```

Locally that credential comes from `az login`; on Azure it comes from a managed
identity. **Never paste a token into source, a `.env` file, or an issue.**

When running an agent locally with `azd ai agent run`, it listens on
`http://localhost:8088` and normally needs no bearer token.

---

## 2. Request / response shape

### Request

```http
POST <agent-endpoint> HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{ "input": "Extract all compensation data from this link: https://.../file.pdf?sv=...&sig=..." }
```

| Field | Type | Notes |
| --- | --- | --- |
| `input` | string | The user turn. For this project it is a prompt that embeds a document URL or extracted JSON. |

### Response

```json
{
  "output": [
    {
      "type": "message",
      "content": [{ "type": "output_text", "text": "{\"employee_name\": \"...\"}" }]
    }
  ]
}
```

`webapp/common.py::call_hosted_agent()` walks `output[]`, returns the first
`message`'s text, and falls back to the raw JSON if no message is present.
Agents are created with `default_options={"store": False}`, so there is no
server-side conversation state to manage.

---

## 3. curl example

```bash
ENDPOINT="$EXTRACTION_AGENT_ENDPOINT"
TOKEN=$(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)

curl -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "Extract all compensation data from this link: https://<blob>/sample.pdf?<SAS>"}'
```

Using `azd` instead (handles auth for you):

```bash
cd agents/extraction-agent
azd ai agent invoke --local "Extract data from: <SAS-URL>"   # local container
azd ai agent invoke "Extract data from: <SAS-URL>"            # deployed agent
```

---

## 4. Python example

```python
import asyncio
from azure.identity import DefaultAzureCredential
from common import call_hosted_agent, endpoints

async def main():
    eps = endpoints()
    text = await call_hosted_agent(
        eps.sow,
        "Employee Name: Jane Tan. Here is the extracted data: {...}. Please build the proposed SOW.",
        DefaultAzureCredential(),
    )
    print(text)

asyncio.run(main())
```

---

## 5. Agent contracts

### 5.1 `extraction-agent`

**Input prompt** — a natural-language instruction containing a URL to a PDF or
XLSX, typically a Blob SAS URL.

**Output** — JSON produced by the model:

```json
{
  "employee_name": "Jane Tan",
  "compensation_items": [
    { "label": "Basic Salary", "amount": 145000 },
    { "label": "Transport Allowance", "amount": 12000 }
  ]
}
```

**Tools**

| Tool | Signature | Returns |
| --- | --- | --- |
| `extract_from_pdf` | `(file_url: str) -> str` | `{"status":"success","extracted_text":["..."]}` or `{"status":"error","message":"..."}` |
| `extract_from_excel` | `(file_url: str) -> str` | `{"status":"success","extracted_text":"[{...}]"}` or a structured error |

PDF extraction uses Document Intelligence `prebuilt-layout` and returns every
table cell's text. Excel extraction uses `pandas.read_excel` and returns JSON
records. Downloads time out after 30 seconds; temporary files are always
cleaned up.

### 5.2 `sow-builder-agent`

**Input prompt** — the employee name plus the raw extraction result.

**Output** — a proposed SOW table; items missing from the prior year carry
`status: REQUIRES_HUMAN_REVIEW`.

```json
{
  "employee_name": "Jane Tan",
  "proposed_SOW": [
    { "Description": "Basic Salary", "Amount (SGD)": "145,000", "status": "MATCHED" },
    { "Description": "Gym Membership", "Amount (SGD)": "1,200", "status": "REQUIRES_HUMAN_REVIEW" }
  ]
}
```

**Tools**

| Tool | Signature | Returns |
| --- | --- | --- |
| `search_prior_year_sow` | `(employee_name: str) -> str` | Prior-year items plus `_source`; returns `{"status":"error"}` on failure. |

When `AZURE_SEARCH_ENDPOINT` / `AZURE_SEARCH_KEY` are unset, the tool returns
fixtures marked `_source: "demo-data"`. The agent is instructed to report a
failed lookup rather than invent a baseline.

> Model-generated JSON is not schema-validated server-side.
> `parse_sow_items()` tolerates `Description`/`Amount (SGD)` and
> `label`/`amount`, strips Markdown fences, and strips non-numeric characters
> from amounts. See [known-limitations.md](known-limitations.md).

---

## 6. Tax Computation Agent (client-side)

This is **not** an HTTP endpoint. It is an `Agent` constructed inside the web
app with `FoundryChatClient` and invoked with
`await tax_agent.run(json.dumps(build_tax_input(items)))`.

- Input: the payload in [architecture.md §4.3](architecture.md#43-tax-computation-agent-input)
- Output: the tax result object in [architecture.md §4.4](architecture.md#44-tax-computation-agent-output)
- System prompt: [`webapp/tax_agent.md`](../webapp/tax_agent.md) — a **template** you must replace with reviewed rules.

---

## 7. Errors

| Status / symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` | Expired token or wrong scope | Re-run `az login`; confirm the `https://ai.azure.com/.default` scope. |
| `403 Forbidden` | Missing role on the Foundry project | Grant **Azure AI Developer** / **Cognitive Services OpenAI User** to your identity. |
| `404 Not Found` | Wrong agent name or `api-version` | Copy the exact endpoint from the Portal. |
| `408 / timeout` | Document Intelligence or a large PDF took too long | Increase `REQUEST_TIMEOUT_SECONDS`; use a smaller test file. |
| `200` but no `output[].message` | Model returned tool calls only | Inspect the raw JSON; `call_hosted_agent` already falls back to it. |
| `{"status":"error", ...}` inside agent text | Tool failed | Read the `message`; check keys, SAS URL expiry and index name. |

More detail in [troubleshooting.md](troubleshooting.md).
