# Maintaining the Safeguard Eval skill

The skill is a portable explanation and evidence layer for Codex, Claude Code, and Pi.
It is not a model-serving package. Its central message is that policy authoring
and engineering must be evaluated together. New releases should improve that
understanding while preserving unsuccessful results and limitations.

## Release plan and scope

Version 0.5.0 covers the recorded model interfaces, WildGuard policy tuning,
nearby-size Qwen comparisons, policy transfer, HateXplain structure/omission tests,
individual calibration, and probability/log-odds ensembles. Earlier demos and
the frontier API pilot are routed separately. Enterprise governance is labelled
as a proposal. Building the package needs no paid inference; using the skill may
incur the learner's normal agent-backend charges.

The gateway update adds dataset provenance, publisher model cards and authoring
guides, a curated external catalog, scoped search guidance, and the v0.5 paper's
PDF/text/source package. The paper remains a review draft. The skill's evidence
registry pins those files; the external catalog deliberately distinguishes live
provider material from historical project evidence.

The guided-learning update adds a welcome, a two-minute introduction, five learning
paths, and an untested policy-writing exercise. The author attribution links to
Harsh Singhal's LinkedIn profile. No research findings or evidence pins changed.
The [onboarding notes](ONBOARDING.md) describe the installation handoff and the
acceptance checks for progressive learning.

Version 0.4.0 adds Pi installation, a separate opt-in conversation-testing lab,
task-sensitive guidance for different readers, and local/hosted/GPU running options.
The [Pi test guide](PI-USER-TEST.md) explains the ordinary-user simulation and local
feedback workflow. The [recorded checks](evidence/2026-10-28/README.md) preserve an
incorrect transfer attribution, the retest, citation/verbosity limitations, and a
local Ollama integration that overblocked all allowed teaching cases. Do not turn
these smoke checks into a new benchmark or a guarantee for every agent backend.
Do not publish the author's future user sessions without an explicit request.

Version 0.5.0 makes the learning role explicit: distinguish findings from examples
and hypotheses, check each suggested action against the user's rule, preserve
unresolved choices, and turn a relevant finding into a proportionate experiment.
The offline transfer lookup reads the exact source-selected policy and recipient
row from the bundled numeric anchors. Its tests cover all named pairs and baseline
selections; prose still needs behavioral review. See the
[learning-revision plan](evidence/2026-10-28-learning/PLAN.md) and its recorded
conversation checks. Retain the failure that motivated a change and avoid claiming
that a successful retest makes a cheap backend universally reliable.

The first release also publishes the previously local ensemble evidence and its
reproduction code. The frozen archives are copied byte for byte, including their
historical notes. Contemporary publication status is recorded by the Git commit
and release; old archive text is not retroactively rewritten.

## When experiments change

1. Commit the reviewed evidence first. Keep frozen study bundles immutable; publish
   a correction separately if necessary. Avoid credentials, private notes, or
   dataset content that is not intended for redistribution.
2. Review `skills/safeguard-eval/references/` for changed interpretations. Update
   models, datasets, studies, authoring guidance, and question routing as appropriate. Preserve
   the distinction between findings and hypotheses. An automated hash refresh is
   not an editorial review.
   When changing provider guidance, read the primary source and update the external
   catalog's check date and scope. A source being reachable is not proof that its
   contents support the summary. Mark new models as untested until evidence exists.
   For a new paper version, publish its PDF, matching text extraction, portable
   source, and metadata together; preserve the previous version and its status.
3. Add relevant files to `SOURCES` in `tools/skill_release.py`. Every dated
   `published_runs` directory needs at least one source entry. If the new experiment
   changes JSON shape, update the numeric extractor and its checks deliberately.
4. Update `release.json` with the evidence date, version, and matching `skill-vX.Y.Z`
   tag. Update the version in `SKILL.md`, installation URLs in the README, and root
   README links. Use a new tag; never move an already published release tag.
5. Refresh against the committed evidence revision, then validate and build:

```bash
python3 tools/skill_release.py refresh --evidence-ref <full-evidence-commit>
python3 tools/skill_release.py check
python3 -m unittest discover -s tests -p 'test_skill_*.py' -v
python3 tools/skill_release.py build
```

The refresh regenerates source URLs/hashes, compact numeric anchors, and the package
manifest. The check fails when a referenced source or dated study inventory differs
from the evidence pin. It verifies numbers against frozen JSON and checks local
package links. The ZIP build is deterministic and contains only the skill folder.

## Review before publishing

Use realistic questions to inspect the guide's routing and evidence, including:

- Can the same policy transfer? Answer with success and failure, not an absolute ban.
- Did a small specialist always beat a large Qwen? Keep studies and model names separate.
- What did removing examples do? Include the opposite effects and fixed-setting caveat.
- Did ensembles require no training? Explain the supervised combiner and frozen LMs.
- Is REVIEW validated? Distinguish the binary studies from earlier demonstrations.
- Can it govern employee intent? Identify the proposed, unvalidated scope.
- Were the first scored prompts from DiffusionDB? No; distinguish the browsing
  source from the original synthetic demonstration.
- What did HateXplain label? Preserve the hate/offensive/normal mapping and our
  binary adaptation; do not call all offensive text a BLOCK case.
- Can it summarize the paper? Fetch the actual pinned text/PDF and disclose the
  review-draft status; do not claim a full read from a summary.
- Does a newly discovered guard support our policy? Separate a provider's stated
  interface from a measured project result; route to current primary sources.

If an agent runtime is used for behavioral evaluation, record its version, prompts,
answers, and judged failures. Offline file checks do not establish answer quality.
Do not run paid agent or model calls merely to publish documentation.

Commit the reviewed skill and maintenance files, open a pull request, and publish
from the reviewed release commit. The source registry points to a separate earlier
evidence commit, avoiding a self-referential hash. A release can remain installable
from its tag while its integration pull request is being reviewed.

```bash
git tag -a skill-vX.Y.Z -m 'Safeguard Eval skill X.Y.Z'
git push origin skill-vX.Y.Z
gh release create skill-vX.Y.Z dist/safeguard-eval-skill-vX.Y.Z.zip dist/SHA256SUMS --verify-tag --title 'Safeguard Eval skill X.Y.Z' --notes-file /path/to/release-notes.md
```

The GitHub workflow validates pull requests and tags and uploads the built package
as a workflow artifact. The explicit release command publishes downloadable assets;
CI does not automatically publish or mutate installed skills. After publication,
download the release asset, verify its checksum, and install it into temporary
Codex, Claude Code, and Pi project directories. Record those checks in the release notes.

## Validation recorded for 0.1.0

- Frozen ensemble archives: 111 and 84 checksum entries verified before copying.
- Existing ensemble unit tests: 19 passed with the archived dependency versions.
- Credential-pattern scan of the newly published evidence: passed before commit.
- Skill format validator: passed. Thirteen installation, update, evidence freshness,
  and deterministic ZIP tests passed locally.
- Skill package, install/update behavior, release download, and source-link checks:
  recorded in the release notes after completing the release verification.

These checks use local CPU work and GitHub access. They do not rerun the models,
change historical results, or claim testing inside every version of Codex/Claude Code.

## Gateway release checks

Check that external links resolve and match the described publisher. Review the
paper reading map against the actual PDF. Verify the public artifacts against
`research-preprint/publication.json` and the pinned source registry. Run the same
installer, source-drift, and reproducible-package checks used for the first release.
For updates, test upgrading an extracted prior release with a local edit and
confirm that the backup preserves it. Record results in the new release notes.

Do not claim a behavioral evaluation of Codex or Claude Code unless one was
actually performed. Static routing review and installation checks establish the
package's integrity and portability, not guaranteed answers from every agent.
