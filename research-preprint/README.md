# Policy as an Interface

**Policy Authoring and Model Choice in LLM Moderation**  
Harsh Singhal · author review draft v0.5 · 28 October 2026

Policy authoring is deeply coupled with AI engineering. This paper studies what
happens when we change policy wording, transfer it between models, alter its
structure, and combine model scores. Language-model weights stay fixed in our
experiments. The results support testing the policy, model, adapter, and decision
settings together; they do not establish a universally best model or policy format.

- [Read the paper (PDF, 25 pages)](output/pdf/policy-as-interface-review-v0.5.pdf)
- [Read the extracted text](output/text/policy-as-interface-review-v0.5.txt)
- [Download the LaTeX source package](output/policy-as-interface-source-v0.5.zip)
- [Version and file checksums](publication.json)

This is an exploratory **review draft**, not a peer-reviewed publication. It has
not been submitted to arXiv and has no arXiv identifier. The source package is
prepared for further editing; publication here is not an arXiv submission.

## A reading route

Start with the introduction and Section 6 for the implications for policy owners
and engineers. Section 3 explains the experimental process. Section 4 covers
wording, general-purpose models, transfer, and HateXplain structure tests. Section
5 separates calibration and ensembles from policy-writing gains. Section 7 states
the limits. Appendices provide model identities, policies, data construction, and
reproduction details. The small frontier API pilot appears only in Appendix G.

The [Safeguard Eval skill](../skills/safeguard-eval/README.md) lets an agent guide you
through this work. It can read the text copy without downloading models or running
the research scripts. Check the PDF when table layout, figures, or extracted
symbols are unclear. Cite the draft version and section when summarizing it.

## Publication snapshot and reproduction

The PDF and source ZIP are byte-for-byte copies of the existing v0.5 review
artifacts. The text was extracted from that PDF; it is not a separately edited
manuscript. The ZIP contains `main.tex`, its bibliography, sections, figures,
generated tables, policy files, and supporting evidence summaries. Extract it
into a new directory to edit or compile the document.

Some notes inside the preserved source package and Appendix E describe an earlier
publication state, when later studies were still local. Those are historical
notes. The repository now publishes the [ensemble archive](../published_runs/2026-10-27-ensemble/README.md)
and [log-odds extension](../published_runs/2026-10-28-ensemble-logits/README.md), along
with the earlier study archives. Follow those archives for reproducing scores;
the paper source package alone is not a complete inference environment. Reading
or summarizing the paper does not require executing scripts from the ZIP.

Public artifacts omit private traces, credentials, and gated source text. Dataset
access remains subject to the original publishers' terms. Embedded notices and
licenses are retained in the source package; the skill's MIT license does not
relicense the paper or third-party material.
