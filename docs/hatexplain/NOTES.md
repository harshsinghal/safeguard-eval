# HateXplain lab notebook

Append observations and deviations; retain unsuccessful candidates and attempts.

## 26 October 2026 — authorization and preparation

The user authorized the structured authoring, revision, and transfer experiments.
The earlier cumulative $20 cap remains in force. Prior reconciled spending is
$10.78119753456; available authorized headroom is $9.21880246544. GPU.ai account
credit is $15.14 and no instances are running. A previously reliable 96 GB RTX PRO
6000 offering is available at $1.99/hour with no disk surcharge. Plan a provider
three-hour cutoff, at most $5.97, with RunPod retained as fallback.

The pinned Hugging Face loader downloads its data from GitHub. We pinned both
revisions and the dataset/split byte hashes. The publisher's 19,229 official split
IDs exclude 919 source rows. Majority voting precedes the binary action mapping.
The official test retains all 1,924 rows. Exact and approximate duplicate grouping
quarantines 12 training and two validation rows, yielding 1,920 validation rows.
Four training demonstrations were selected by a fixed hash rule and their groups
excluded from the 1,024 fitting posts. No held-out examples were inspected for
authoring. The data manifest records all exclusions and limitations.

The common policy has 319 words, seven sections, and four demonstrations. Native
helper inspection caught that PolicyLM rule fields must be single lines; its
renderer joins the component texts with spaces, preserving every clause. Whole
document syntax treatments remain excluded for that native field interface.
Seven new checks cover majority mapping, faithful treatment delivery, supported
native fields, fixed scope/examples, failure scoring, and paired alignment.
All 50 repository tests passed before inference; the seven new checks also passed
after the single-line rendering correction. These are local checks, not model
results. No paid resources have yet been created.

## 26 October 2026 — provision and final-input guard

The protocol and implementation were committed as `d428f8e` before provisioning.
While GPU allocation was pending, an additional check tightened the final-input
guard: verify the hash of the actual policy file supplied to the runner, rather
than a same-ID file in the standard policy directory. A regression check covers
that alternate-file case. No inference had begun. The original registration is
retained alongside a source amendment record; the experimental protocol is unchanged.

## 26 October 2026 — fitting and editor amendment

GPU `gpu-8e9d66ea` became ready at 23:19 UTC with automatic termination at
2026-10-27 02:19:07 UTC. Only fit and validation files were uploaded. The three
baseline fitting runs completed with zero classification errors. PolicyLM's native
helper measured 465 policy tokens with 1,581 tokens left for content. No post in
any study population exceeds its 2,000-character window size (maximum fit length
526 characters, validation 331, test 335); no source post needs multiple windows.

The initial six author calls echoed their input envelopes and produced no valid
policy drafts. This was an editor output-contract failure, not a classifier refusal.
The [prospective amendment](AUTHORING-AMENDMENT.md) changes only author output
packaging and adds six equally budgeted calls before validation or test. The repair
emits four schema-constrained arrays of rule text; fixed metadata, scope and examples
are restored by code. Exact initial and amended traces are retained. All six
amended calls produced structurally valid candidates and all six fitting runs
completed without classifier errors.

AI-assisted [scope review](SCOPE-REVIEW.md) excludes both PolicyLM candidates for
an inconsistent normal/offensive definition and loss of the original context
constraint. PolicyLM p2 is also identical to p1. Qwen p2 duplicates Qwen p1 and is
excluded from selection to avoid a second chance through inference variation.
Qwen p1 and Shieldstral p1 are identical punctuation edits. Shieldstral p2 additionally
clarifies context and group membership. The search therefore found little diversity;
it must not be presented as a strong or exhaustive model-specific optimizer.

All nine fitting runs are retained, including rejected and duplicate drafts. The
classification implementation has not changed since the pre-inference input-guard
fix. The scope review was finalized before any validation results were observed.
Validation now evaluates p0 for PolicyLM, p0/p1/p2 for Shieldstral, and p0/p1 for Qwen.
The test data remain local. Source selections may retain p0.

## 26 October 2026 — validation and freeze

All six eligible validation runs completed with zero classifier errors. Source
selection retains p0 for PolicyLM, chooses Shieldstral p2's context clarification,
and chooses Qwen p1's punctuation edits. Validation macro-F1 is respectively
65.8968%, 53.7954%, and 74.4118%. Shieldstral's p0 is 52.8534%; Qwen's p0 is
74.3264%. The Qwen advantage is only 0.0854 percentage points and should not be
presented as a robust improvement from validation alone.

The global freeze hash is
`9e2181c8ffdadf03e2c975865b7e60c0968dda18c4d1e4e8711560f67d4b7731`.
It binds source, policies, eligibility, source choices, data, and all final jobs.
There are three distinct source-selected bodies: p0, Shieldstral p2, and Qwen p1.
Thus the possible cross-source duplicate noted during review does not occur in
the final pool. PolicyLM's selected column is the unchanged shared policy, not a
new PolicyLM-authored version. The matrix includes 27 full-test conditions and
three 256-post repeatability subsets. Test and repeat files were uploaded only
after the local freeze verified all inputs. No further wording or selection is
permitted in this study.

## 26 October 2026 — final test, integrity checks, and billing

All 45 recorded runs completed: nine fitting runs, six validation runs, 27
full-test conditions and three 256-post reference repeats. The total is 73,452
classification observations, with zero classifier output failures. Six failed
original editor calls remain separate from that classifier count. Reconstructed
all saved requests from the pinned adapters and verified their hashes against the
private traces. Replayed all decisions, including scores to absolute tolerance
1e-12. No requests or recorded model outputs were edited.

The most substantial contrasts are presentation and omission effects. Removing
all four examples improves Shieldstral accuracy from 52.39% to 60.97% and reduces
Qwen accuracy from 72.45% to 61.80%. Linear presentation of identical clauses
improves Shieldstral by 4.89 accuracy points and reduces Qwen by 1.82 points.
PolicyLM's definitions omission raises accuracy by 1.46 points but misses 36 more
hateful posts while avoiding 64 false blocks. All registered conditions, including
negative results, are retained and reported.

The bounded editor search yielded small effects: Shieldstral p2 improves test
macro-F1 by 0.838 points; Qwen p1 by 0.022 points (interval spans zero); PolicyLM
retains p0 because its revisions failed scope review. Transfer effects are small
and mixed. Reference repeats change zero PolicyLM decisions and one decision each
for Shieldstral and Qwen. Intervals are unadjusted and do not include search or
inference variability. Fixed specialist cutoffs were not calibrated.

An initial analysis report duplicated a contrast when PolicyLM's selected policy
was p0: versus-p0 and versus-own-winner were the same comparison. The reporting
helper now emits it once; underlying runs, metrics, selections and interval values
are unchanged. The initial report is preserved privately. Figures show all
registered formats/components and the three distinct transfer texts.

GPU.ai instance gpu-8e9d66ea was terminated after collecting and verifying all
artifacts. Provider billing is $1.34 for 2,416 GPU seconds at $1.99/hour. Cumulative
spending is $12.12119753456 of $20; remaining authorization is $7.87880246544.
Temporary provider and local SSH keys were removed. RunPod was not needed.
The readout and evidence bundle distinguish exact record reproduction from a new
inference run, and the limited editor search from an optimal policy.

## Completion — public reproduction and documentation

The public bundle reproduces all 45 runs, 73,452 observations, validation choices,
metrics and 2,000-resample paired intervals exactly using its archived sources.
The check ran from /tmp rather than the working repository, with Python 3.11.14
and NumPy 2.4.6; no dataset download, GPU or model API was needed. Public-file hashes,
decompressed prediction hashes, local documentation links and credential-pattern
checks passed. All three figures were visually checked. The readable report and
exact wording changes are saved alongside the protocol and unsuccessful attempts.

After successful reproduction, only completion metadata and these documentation
snapshots were finalized; predictions, frozen code, policies and analysis were not
changed. Final evidence hashes were checked again. Existing preprint and magazine
files are left for review against this new evidence before any subsequent rewrite.
