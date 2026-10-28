# Maintaining the Safeguard Eval skill

The skill is a portable explanation and evidence layer for Codex and Claude Code.
It is not a model-serving package. Its central message is that policy authoring
and engineering must be evaluated together. New releases should improve that
understanding while preserving unsuccessful results and limitations.

## Release plan and scope

Version 0.1.0 covers the recorded model interfaces, WildGuard policy tuning,
nearby-size Qwen comparisons, policy transfer, HateXplain structure/omission tests,
individual calibration, and probability/log-odds ensembles. Earlier demos and
the frontier API pilot are routed separately. Enterprise governance is labelled
as a proposal. No new paid inference is needed to build or use the skill.

The first release also publishes the previously local ensemble evidence and its
reproduction code. The frozen archives are copied byte for byte, including their
historical notes. Contemporary publication status is recorded by the Git commit
and release; old archive text is not retroactively rewritten.

## When experiments change

1. Commit the reviewed evidence first. Keep frozen study bundles immutable; publish
   a correction separately if necessary. Avoid credentials, private notes, or
   dataset content that is not intended for redistribution.
2. Review `skills/safeguard-eval/references/` for changed interpretations. Update
   models, studies, authoring guidance, and question routing as appropriate. Preserve
   the distinction between findings and hypotheses. An automated hash refresh is
   not an editorial review.
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
python3 -m unittest discover -s tests -p 'test_skill_package.py' -v
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
Codex and Claude Code project directories. Record those checks in the release notes.

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
