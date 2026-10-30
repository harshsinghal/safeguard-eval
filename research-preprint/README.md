# Policy as an Interface

**Authoring and Evaluating Moderation with Language and Decision Models**
Harsh Singhal · author review draft **v0.6** · 29 October 2026

Policy authoring is deeply coupled with AI engineering. This paper follows the work from wording and model choice through transfer, structured documents, calibration, ensembles, and the Jev, Kev, and Clef decision models. The practical recommendation is to maintain an approved policy and representative labeled evaluations, then test the policy, native model interface, and decision rule together as models change.

- [Read the updated paper — PDF, 38 pages](output/pdf/policy-as-interface-review-v0.6.pdf)
- [Read the extracted text](output/text/policy-as-interface-review-v0.6.txt)
- [Download the editable LaTeX source package](output/policy-as-interface-source-v0.6.zip)
- [Revision plan and completed checks](REVISION-v0.6.md)
- [Version and checksums](publication.json)

This is an exploratory **review draft**, not peer reviewed or submitted to arXiv. It has no arXiv identifier. Repository publication is not an arXiv submission.

## Start with the new evidence

| Reading question | Location |
|---|---|
| How did Jev, Kev, and Clef respond to policy edits? | Section 6, pp. 11–12 |
| Which systems are competitive, and how do false blocks and misses change the comparison? | Section 7, pp. 12–15 |
| Should teams invest in policies, models, or benchmarks? Who owns which decisions? | Section 8, pp. 15–18 |
| What are the limits and useful next experiments? | Section 9, p. 18 |
| What are the native decision interfaces and frozen configurations? | Appendix G, pp. 31–32 |
| Where are all leaderboard entries and metric definitions? | Appendix H, pp. 32–36 |

The introduction and Sections 3–5 explain the preceding wording, transfer, structure, and ensemble studies. Their original accuracy-oriented selections remain separate from the later balanced comparison. The frontier API pilot appears only in Appendix I.

## What this revision adds

The expanded leaderboard contains **20 entries per benchmark**, drawn from **209 eligible archived candidate records**. Entries include individual models and ensemble methods. Tables report balanced accuracy, ordinary accuracy, macro-F1, MCC, false blocks, missed violations, unresolved outputs, and uncertainty. Separate profiles show whether validation-selected false-block limits and recall targets actually held on test.

The paper explains why more detailed policies can help one interpreter and harm another, why cutoff improvements are not wording improvements, and why close ranks do not establish universal winners. It distinguishes Jev's hosted API from the self-hosted Kev and Clef implementations, without inferring Jev's hidden architecture or claiming matched cost, latency, or privacy advantages. Stakeholder responsibilities are proposed from the technical evidence, not presented as a tested professional-team workflow.

The [interactive leaderboard](../published_runs/2026-10-29-leaderboard-decision-models/index.html), [full machine-readable archive](../published_runs/2026-10-29-leaderboard-decision-models/README.md), [decision-model report](../docs/decision-models/README.md), and [original Jev study](../docs/jev/README.md) retain detailed evidence. GitHub readers can download the HTML and open it locally.

## Reproduction and preservation

The portable ZIP includes `main.tex`, sections, bibliography, vector figures, generated tables, policy files, and prompt-free evidence summaries. Extract into a new directory and compile with Tectonic or a conventional LaTeX installation. The included README explains how to regenerate new assets and audit the claims. Reading or compiling the paper needs no GPU or provider token.

[Verification](output/validation-v0.6.json) confirms successful compilation and identical content in all 38 pages of the independently rebuilt source package. The [claim audit](output/claim-checks-v0.6.json) checks 119 configuration/profile rows, 33 citation keys, and unchanged hashes for all 3,235 existing experiment files. Full row-level reproduction uses the experiment archives, not just the manuscript package. No new inference or paid compute was used for the rewrite.

The earlier [v0.5 PDF](output/pdf/policy-as-interface-review-v0.5.pdf), [source ZIP](output/policy-as-interface-source-v0.5.zip), and [metadata](publication-v0.5.json) are preserved. The current installed skill release still pins its earlier paper snapshot; this revision does not silently change that version. The magazine and media articles remain at their prior versions.

Dataset access, attribution, and embedded licenses remain applicable. Public artifacts omit credentials, private traces, and gated source text. Redacted examples are marked; they are not the actual inference prompts. The skill's MIT license does not relicense the paper or third-party material.
