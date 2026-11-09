# Screenshot shot list

**Status: captured.** Slots `00`–`07` are committed in [`docs/screenshots/`](screenshots/)
and wired into the README, architecture guide and deployment guide. Slots `08`
and `09` are optional and have not been captured.

- Folder: [`docs/screenshots/`](screenshots/)
- The `![...](...)` snippets below are **relative to the file named in "Embed in"**.
  For `README.md` they start with `docs/screenshots/`; for files inside `docs/`
  they start with `screenshots/`.
- Format: PNG, cropped to the relevant window, optimised (all 8 images total < 1 MB)
- Filenames: exactly as listed below (lowercase, hyphens, numbered)
- All figures in the images are **synthetic demo data** (`John Doe`, demo SGD amounts)

| Slot | File | Size | State |
| --- | --- | --- | --- |
| 00 | `00-sample-input.png` | 781 × 735 | Captured |
| 01 | `01-portal-project.png` | 1657 × 601 | Captured, redacted |
| 02 | `02-hosted-agents.png` | 1701 × 733 | Captured |
| 03 | `03-generate-sas.png` | 1707 × 785 | Captured, cropped + redacted |
| 04 | `04-upload.png` | 1697 × 767 | Captured |
| 05 | `05-sow-review.png` | 1327 × 932 | Captured |
| 06 | `06-result-pdf.png` | 707 × 1140 | Captured, two shots stitched |
| 07 | `07-pdf-package.png` | 797 × 806 | Captured |
| 08 | `08-logs-traces.png` | — | Optional, not captured |
| 09 | `09-cli-orchestrator.png` | — | Optional, not captured |

---

## Redaction rules (read before capturing)

A portfolio screenshot can leak more than a README ever will. Before publishing,
blur or crop out:

- Subscription IDs, tenant IDs, resource group names and full resource URLs
- Email addresses, employee names (use `Jane Tan` / `John Doe` sample data)
- **SAS query strings** (`?sv=...&sig=...`) — click into the URL field and
  select a fake URL before capturing, or blur the field entirely
- API keys, tokens, client secrets and connection strings
- Browser profile pictures, notification toasts and bookmarks bar
- Anything from a real employer or a real compensation document

Run `git diff --cached` / inspect the final PNG at 100% zoom before committing.

### What was redacted in this set

| Image | Action taken | Why |
| --- | --- | --- |
| `01-portal-project.png` | Grey bars over subscription name + subscription GUID and over the parent-resource link | Identifiers tied to the author's Azure subscription |
| `03-generate-sas.png` | Cropped at y = 785 px so the **Blob SAS token** and **Blob SAS URL** fields are not in the file at all; grey bar over the storage-account name in the breadcrumb | A SAS token is a live credential. Cropping is safer than blurring because the pixels are absent from the published file |
| `06-result-pdf.png` | Two captures of the same Step 3 screen stitched vertically at a common width | The second capture held the "Download Deliverable" button that the first one cut off |

No other image contained a URL, token, key, email, subscription ID or real
personal data. The sample document (`00`) and the generated PDF (`07`) contain
only synthetic demo figures.

---

## Slots

### Slot 00 — `00-sample-input.png`

| | |
| --- | --- |
| **Capture** | The sample remuneration & allowances PDF opened in a viewer |
| **Show** | The input shape: salary, bonus, allowances and employer-borne tax items |
| **Embed in** | `README.md` → "Demo & screenshots" → "The input document" |
| **Redact** | None needed — synthetic figures, no employee/employer name |

![Sample compensation document used as input](screenshots/00-sample-input.png)

```markdown
![Sample compensation document used as input](docs/screenshots/00-sample-input.png)
```

### Slot 01 — `01-portal-project.png`

| | |
| --- | --- |
| **Capture** | Azure Portal → the Microsoft Foundry project → Overview |
| **Show** | The project exists and links through to the Foundry portal |
| **Embed in** | `README.md` (collapsed "Azure-side evidence"); `docs/deployment.md` §5 |
| **Redact** | **Subscription name + GUID** and parent-resource ID — done |

![Foundry project overview](screenshots/01-portal-project.png)

```markdown
![Foundry project overview](screenshots/01-portal-project.png)
```

### Slot 02 — `02-hosted-agents.png`

| | |
| --- | --- |
| **Capture** | Foundry project home → "Recent work → Agents" list |
| **Show** | `sow-builder-agent` and `extraction-agent-test` deployed, plus the in-process `TaxComputationAgent` |
| **Embed in** | `README.md` (collapsed "Azure-side evidence"); `docs/architecture.md` §1 |
| **Redact** | None needed — no resource IDs or endpoints are expanded |

![Hosted agents listed in Microsoft Foundry](screenshots/02-hosted-agents.png)

```markdown
![Hosted agents listed in Microsoft Foundry](screenshots/02-hosted-agents.png)
```

### Slot 03 — `03-generate-sas.png`

> This slot was **repurposed**. The original `03-terminal-invoke.png` slot
> expected a terminal capture of `azd ai agent invoke`; no such capture was
> supplied. The screenshot provided was an Azure Portal **Generate SAS** pane,
> so the slot now documents SAS-URL creation instead. Steps 2–3 of
> `docs/development.md` and §3 of `docs/api.md` remain text-only.

| | |
| --- | --- |
| **Capture** | Azure Portal → storage container → blob → "Generate SAS" pane |
| **Show** | Read-only permission, HTTPS only, short expiry, account-key signing |
| **Embed in** | `README.md` (collapsed "Azure-side evidence"); `docs/deployment.md` §5 |
| **Redact** | **SAS token and SAS URL fields cropped out entirely**; storage-account name in breadcrumb covered |

![Generating a read-only Blob SAS URL in the Azure Portal](screenshots/03-generate-sas.png)

```markdown
![Generating a read-only Blob SAS URL in the Azure Portal](screenshots/03-generate-sas.png)
```

### Slot 04 — `04-upload.png`

| | |
| --- | --- |
| **Capture** | Streamlit Step 1 — "Upload Compensation File", empty SAS URL field |
| **Show** | The entry point of the app |
| **Embed in** | `README.md` → "Demo & screenshots" → Step 1 |
| **Redact** | None needed — **the SAS URL field is empty** |

![Step 1 - upload a compensation document](screenshots/04-upload.png)

```markdown
![Step 1 - upload a compensation document](docs/screenshots/04-upload.png)
```

### Slot 05 — `05-sow-review.png`

| | |
| --- | --- |
| **Capture** | Streamlit Step 2 — proposed SOW in `st.json` with flagged items and Approve / Reject buttons |
| **Show** | **The most important screenshot**: the human-in-the-loop control point |
| **Embed in** | `README.md` → "Demo & screenshots" → Step 2 |
| **Redact** | None needed — `John Doe` and demo amounts only |

![Step 2 - review and approve the proposed SOW](screenshots/05-sow-review.png)

```markdown
![Step 2 - review and approve the proposed SOW](docs/screenshots/05-sow-review.png)
```

### Slot 06 — `06-result-pdf.png`

| | |
| --- | --- |
| **Capture** | Streamlit Step 3 — tax computation JSON plus the "Download Tax Package (A4 PDF)" button |
| **Show** | A completed end-to-end run and the deliverable |
| **Embed in** | `README.md` → "Demo & screenshots" → Step 3 |
| **Redact** | None needed — no name appears in the result JSON |

![Step 3 - tax result and PDF download](screenshots/06-result-pdf.png)

```markdown
![Step 3 - tax result and PDF download](docs/screenshots/06-result-pdf.png)
```

### Slot 07 — `07-pdf-package.png`

| | |
| --- | --- |
| **Capture** | The generated A4 PDF opened in a viewer |
| **Show** | Sections 1–3: tax computation summary, tax payable, audit trail |
| **Embed in** | `README.md` → "The generated tax package"; `docs/architecture.md` §4.4 |
| **Redact** | None needed — no employee name, synthetic SGD amounts |

![Generated A4 tax computation package](screenshots/07-pdf-package.png)

```markdown
![Generated A4 tax computation package](screenshots/07-pdf-package.png)
```

### Slot 08 — `08-logs-traces.png` *(optional, not captured)*

| | |
| --- | --- |
| **Capture** | Foundry Agent Service logs / tracing view for one invocation |
| **Show** | Azure-side observability |
| **Embed in** | `docs/deployment.md` §11 (smoke test) |
| **Redact** | Request IDs that contain tenant info, full endpoint URLs, user email |

```markdown
![Foundry hosted agent logs and traces](screenshots/08-logs-traces.png)
```

### Slot 09 — `09-cli-orchestrator.png` *(optional, not captured)*

| | |
| --- | --- |
| **Capture** | `python webapp/orchestrator.py` showing the `[1/3]`, `[2/3]`, approval prompt and final result |
| **Show** | The CLI alternative and the terminal approval gate |
| **Embed in** | `docs/development.md` §3 |
| **Redact** | SAS URL, absolute paths, employee name |

```markdown
![CLI orchestrator showing the human approval gate](screenshots/09-cli-orchestrator.png)
```

---

## Where each image is embedded

| File | Live in |
| --- | --- |
| `00-sample-input.png` | `README.md`, this page |
| `01-portal-project.png` | `README.md`, `docs/deployment.md`, this page |
| `02-hosted-agents.png` | `README.md`, `docs/architecture.md`, this page |
| `03-generate-sas.png` | `README.md`, `docs/deployment.md`, this page |
| `04-upload.png` | `README.md`, this page |
| `05-sow-review.png` | `README.md`, this page |
| `06-result-pdf.png` | `README.md`, this page |
| `07-pdf-package.png` | `README.md`, `docs/architecture.md`, this page |
| `08`, `09` | Not captured — snippets above are ready when they are |

---

## README wiring (already applied)

The README's "Demo & screenshots" section now contains real images in this
order: `00` → `04` → `05` → `06` → `07`, with `01`–`03` inside a collapsed
`<details>` block so the landing page stays readable. The old `📸 SLOT`
callouts were removed.

---

## Quick checklist

- [x] All captured PNGs named as above and placed in `docs/screenshots/`
- [x] No SAS URLs, keys, tenant/subscription IDs or real employee data visible
- [x] Callout blocks replaced with real `![...](...)` images
- [x] Images use relative paths that resolve in GitHub's Markdown preview
- [x] PNGs optimised — 8 files, ~912 KB total (largest 223 KB)
- [x] `docs/screenshots/README.md` updated with the current inventory
- [ ] Optional: capture slots `08` and `09` and add them to the deployment/development guides
