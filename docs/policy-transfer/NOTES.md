# Experiment notes

2026-10-25 (Los Angeles): Protocol and implementation registered before new inference.
The original 35 tests and eight transfer tests pass. Exact dataset and baseline
artifact hashes were verified; fit and validation groups do not overlap.

The earlier selected policies are not reused for authoring. The five original p0
fitting/validation runs are reused as fixed inputs; all twenty drafts are fresh.
A single pinned Qwen3.5-27B editor is held constant and blinded to the recipient name.
This procedural choice makes the feedback isolated and reproducible, but introduces
an editor-family confound that is explicitly documented in the protocol.

GPU.ai still has capacity and $17.46 account credit. The remaining user-authorized
project budget is only $11.53880246544. One $1.99/hour RTX PRO 6000 was requested
with a five-hour automatic lifetime; RunPod is available if needed. No audit or
test dataset is included in the initial GPU upload.

The GPU became ready with provider cutoff 2026-10-26 06:40:03 UTC.
All five pinned checkpoints downloaded. Initial four PolicyLM-feedback drafts passed
format/schema checks. No manual policy changes were made. A preliminary semantic
read flags possible scope drift: one draft says to block persona-based bypass
attempts without restating the harmful-output condition, despite benign-framing
exceptions elsewhere. Another broadens “copyright infringement” to disclosure of
copyrighted material before qualifying it later. Record these as policy-authoring
risks, not merely wording improvements; do not remove a candidate after seeing scores.

All 20 author calls produced valid schema on the first attempt; there were no
format repairs or baseline fallbacks. The four editing strategies use soft length
targets in the editor instruction and a hard 1500-word eligibility limit. At least
one compact draft exceeded its 200-word target slightly; retain and disclose the
actual lengths, rather than perform unregistered extra editing.

PolicyLM's fresh candidate validation scores are p1 83.98%, p2 90.82%, p3 83.01%,
p4 86.91%, versus p0 90.23%. Thus only p2 improves this model's validation score
in this bounded search. These are validation results, not test conclusions.

Pre-test semantic review of Shieldstral p3: its 98.828125% validation accuracy
exceeds p0's 95.5078125%, but the generated block rule omits the original explicit
sexual-content category. It also names behavioral jailbreak manipulation as a
blocking category before a later harmful-objective qualification. The editor was
instructed to preserve scope; the schema checker cannot guarantee that. This is
a substantive limitation/finding, not a reason for a score-informed rewrite.
The registered candidate remains unchanged and eligible under the format/length
checks. Report benchmark agreement separately from adherence to the intended
platform policy. A scope-corrected ablation would require a separate experiment.

All 40 new search runs completed (20 drafts × fit/validation), with zero
classification errors. The five source winners are PolicyLM p2, Shieldstral p3,
Qwen 2B p3, and unchanged p0 for both Qwen 4B and Qwen 27B. The pool therefore
contains four distinct policies. Do not force a new draft to win or describe p0
as a newly optimized 27B policy. Transfer of a successful distinct 27B revision
remains untested in this bounded search. All five recipients now evaluate the
same four-policy pool on validation before any new audit/test upload.

First transfer-validation observation: the Shieldstral-selected policy scores
98.828125% on its source but 77.5390625% on PolicyLM. PolicyLM's own selected
policy scores 90.8203125% on validation. This is an interaction to examine on
test, not a test finding or proof of a universal model–policy optimum.

Global freeze created 2026-10-26T02:18:46.910763+00:00. Recipient pool choices: PolicyLM p2;
Qwen 2B p3 for Shieldstral, Qwen 2B and Qwen 27B; p0 for Qwen 4B.
Shieldstral ties at 98.828125% for its own text (484 substantive words) and
Qwen 2B p3 (481 words); the registered shorter-text tie-break selects the latter.
Qwen 27B chooses Qwen 2B p3 at 92.3828125%, versus p0 at 91.796875%.
All source and recipient choices will be independently rechecked locally before
the audit/test upload. No new text revisions or test-driven selections follow.

Interpretation note before the 27B transfer test finishes: preserve the earlier
Qwen 27B result of 91.29% with its shared p1 policy in the write-up. This fresh
isolated search excludes that policy for methodological reasons. A new small-model
advantage would compare this search's frozen choices, not the models' best known
scores or achievable capabilities. Do not present a favorable new comparison while
omitting that historical context.

Post hoc repeatability check of the five already registered p0 test reruns found
0/1699 changed labels for PolicyLM, 4 for Shieldstral, 7 for Qwen 2B, 5 for Qwen 4B,
and 1 for Qwen 27B, compared with the original public predictions (17/8495 total).
This check adds no inference calls and does not change selection. The cause of
individual changes is not isolated. Report close rankings and source-selection
uncertainty accordingly; the paired intervals do not include optimizer/run variance.

All inference finished. Full collection verified 102 recorded runs, 88,764
classification observations, and 20 isolated authoring traces. That comprises
92 new runs / 81,084 new classifications and ten reused baseline runs / 7,680
classifications. Every saved classifier request was reconstructed from its exact
policy and input; every final decision was reproduced from the raw response.
An initial exact floating-score comparison detected a 1.39e-17 cross-platform
round-off difference. Replay uses an explicit 1e-12 absolute tolerance for scores
only; label agreement remains exact. No predictions or policies were altered.

GPU gpu-07cc74ef was terminated and its temporary SSH keys removed. Provider
usage is 4,193 GPU-seconds, billed $2.32. Cumulative project spend is
$10.78119753456 of $20, leaving $9.21880246544. RunPod capacity was not needed.

The completed primary comparison is Shieldstral 90.7593% versus Qwen 27B
89.3467%, a +1.4126-point difference with an unadjusted paired interval
[+0.0589, +2.7663] points. This is a narrow, exploratory edge for the chosen
configurations. The earlier Qwen score of 91.29% with a different selected
policy prevents interpreting it as a best-known-model ranking.

Bootstrap implementation uses the stored group IDs. The official test has 1,699
distinct group IDs, so its group bootstrap is effectively case-level; no new
semantic clustering was performed. Intervals exclude policy-search and runtime
variation and are not adjusted for multiple comparisons.

Both CPU reproduction paths passed: the repository checkout and the archived
source snapshot each verified all 102 runs / 88,764 predictions, frozen selections,
full audit/test matrices and paired intervals. The figure PNG was visually checked;
SVG/PDF and plotted-data CSV are preserved. Publication checks verified allowed
prediction fields and excluded gated prompt text, raw traces and credentials.
The final readout preserves the prior higher Qwen result and the scope-drift concern.
