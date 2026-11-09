# Screenshots

This folder holds the showcase images referenced by the README and docs.

**They have not been captured yet.** The repository deliberately uses labelled
`📸 SLOT` callouts instead of broken image links. See the
[Screenshot shot list](../screenshots.md) for:

- the exact filename for each slot,
- what to capture and where to embed it,
- the redaction rules (SAS URLs, tenant IDs, employee names, keys),
- the ready-to-paste Markdown snippet.

## Naming convention

```
NN-short-description.png
```

| Prefix | Subject |
| --- | --- |
| `01`–`03` | Azure Portal / terminal / deployment evidence |
| `04`–`06` | Streamlit web app steps 1–3 |
| `07`–`09` | Generated PDF, observability, CLI |

## Before committing an image

- PNG, ~1440 px wide, cropped to the relevant window, ideally < 500 KB
- Blur or replace: SAS query strings, keys, tokens, tenant/subscription IDs,
  emails, real employee names and real compensation figures
- Use sample identities (`Jane Tan` / `John Doe`) and demo amounts
- Verify the image renders at 100% zoom in GitHub's preview

Large binaries are better kept out of git history. If you later add many
high-resolution images, consider Git LFS or an external image host.
