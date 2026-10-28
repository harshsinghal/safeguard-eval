# Read or summarize the research paper

**Harsh Singhal. Policy as an Interface: Policy Authoring and Model Choice in LLM
Moderation. Author review draft v0.5, 28 October 2026.**

This is a 25-page exploratory draft, not peer reviewed and not submitted to arXiv.
It has no arXiv identifier. Do not manufacture a citation, DOI, acceptance, or
arXiv link. Publication in this repository makes the draft accessible; it does
not change its research status.

## Find the versioned files

Resolve these IDs through [sources.json](sources.json) to get commit-pinned
`url`, `raw_url`, and SHA256 values:

| Source ID | Use |
|---|---|
| `paper-home` | Public reading page, status, and links |
| `paper-pdf` | The review PDF, including charts and tables |
| `paper-text` | Text extracted from that exact PDF; easiest route for an agent |
| `paper-source` | Portable ZIP with LaTeX, bibliography, figures, and supporting files |
| `paper-publication` | Title, date, version, file sizes, checksums, and publication status |

Offer the readable PDF link when the user wants the paper. When asked to summarize,
fetch `paper-text` or read it from an available checkout; inspect the PDF where
figures or table extraction matter. If your tools support local downloads, save
the `raw_url` to an appropriate temporary/workspace file and verify its hash.
The skill does not bundle the paper itself, so it remains a small installation.

Reading the paper needs no API token, GPU, model download, or execution of scripts
from the source archive. Do not bypass access restrictions. If fetching fails,
use the bundled study guide, say that the full paper was unavailable, and provide
the source link. Do not claim to have read the full paper from its abstract alone.

## Choose a reading path

| User's question | v0.5 sections and PDF pages |
|---|---|
| Why should policy owners work with engineers? | Introduction, pp. 1–2; Section 6, pp. 10–11 |
| What does tuning a policy actually mean? | Section 3, pp. 3–5; Section 4.1, p. 6 |
| Can a small specialist replace a general-purpose model? | Section 4.2, p. 6; Section 4.3, pp. 7–8; limits in Section 7 |
| Does a policy transfer? | Section 4.3, pp. 7–8 |
| Why do examples and structure matter? | Section 4.4, pp. 8–9; Appendix F.1, p. 21 |
| What did calibration and ensembles add? | Section 5, pp. 9–10; Appendix F.2–F.3, pp. 22–23 |
| How were datasets, inputs, and models controlled? | Appendices B–C, pp. 17–18 |
| Where are policies and reproducibility details? | Appendices D–F, pp. 19–23; pinned run archives |
| What about frontier APIs? | Appendix G, pp. 24–25; limited pilot only |

Use page numbers printed in the PDF, and check the section before citing it.
Extracted text may have broken ligatures, columns, or mathematical symbols; the
PDF is authoritative for layout. Frozen result JSON is the route to exact metrics.

## Summarize without strengthening the claims

Lead with the practical finding: policy text is part of an evaluated system,
alongside the model, adapter, and decision rule. Explain the separate interventions
in order: wording, model choice, transfer, structure, calibration, combination.
Then choose a few relevant numerical examples, including unsuccessful results.

Keep the scope attached to the claim: bounded searches, English text tasks,
binary main studies, reused tests in later extensions, uncertain upstream
training exposure, and no matched new fine-tuning baseline. Include only the
limitations relevant to the question rather than reciting all caveats every time.
The experiments demonstrate competitive configurations without additional LM
fine-tuning, not that policy editing universally replaces fine-tuning.

The preserved PDF and ZIP contain historical publication notes. Later ensemble
evidence is now in the repository; `paper-home` explains that change. Do not treat
an old “local only” note as current access status. Conversely, do not silently
correct the paper's results. If a paper/table/JSON discrepancy is found, identify
the versions and report it. Separate any later evidence from this draft.
