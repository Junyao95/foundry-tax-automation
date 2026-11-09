# Screenshots

Showcase images referenced by the README and the docs. **Slots `00`–`07` are
captured and published**; slots `08`–`09` are optional and not captured yet.
See the [Screenshot shot list](../screenshots.md) for what each image shows,
where it is embedded, and the redaction rules.

## Inventory

| File | Dimensions | What it shows |
| --- | --- | --- |
| `00-sample-input.png` | 781 × 735 | Synthetic remuneration & allowances PDF used as the input document |
| `01-portal-project.png` | 1657 × 601 | Azure Portal overview of the Foundry project — **redacted** |
| `02-hosted-agents.png` | 1701 × 733 | Foundry "Recent work → Agents" list with both hosted agents |
| `03-generate-sas.png` | 1707 × 785 | Generate SAS pane — **cropped above the token fields + redacted** |
| `04-upload.png` | 1697 × 767 | Streamlit Step 1, empty SAS URL field |
| `05-sow-review.png` | 1327 × 932 | Streamlit Step 2, `REQUIRES_HUMAN_REVIEW` items and Approve / Reject |
| `06-result-pdf.png` | 707 × 1140 | Streamlit Step 3, tax JSON and the PDF download button |
| `07-pdf-package.png` | 797 × 806 | Generated A4 PDF: summary, tax payable, audit trail |

Eight PNGs, ~912 KB total. Largest single file is 223 KB.

## Naming convention

```
NN-short-description.png
```

| Prefix | Subject |
| --- | --- |
| `00` | Sample input document |
| `01`–`03` | Azure Portal / deployment evidence |
| `04`–`06` | Streamlit web app steps 1–3 |
| `07`–`09` | Generated PDF, observability, CLI |

## Redaction applied to this set

- `01` — subscription name, subscription GUID and parent-resource link covered
  with grey bars.
- `03` — the **Blob SAS token** and **Blob SAS URL** fields are not in the file
  at all (the source was cropped at y = 785 px, above those fields). The
  storage-account name in the breadcrumb is covered. Cropping beats blurring:
  there are no secret pixels left to recover.
- All other images contain only synthetic demo data and no identifiers.

## Before committing a new image

- PNG, ~1440 px wide, cropped to the relevant window, ideally < 500 KB
- Blur or crop out: SAS query strings, keys, tokens, tenant/subscription IDs,
  emails, real employee names and real compensation figures
- Use sample identities (`Jane Tan` / `John Doe`) and demo amounts
- Inspect the final PNG at 100% zoom and verify it renders in GitHub's preview
- Add a row to the [shot list](../screenshots.md) and update this inventory

Large binaries are better kept out of git history. If you later add many
high-resolution images, consider Git LFS or an external image host.
