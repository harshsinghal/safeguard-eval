# Curriculum v2 pilot: readout

27 November 2026. This is step 14 of [the design](../CURRICULUM-V2-DESIGN.md): the whole pipeline run small, before the build is scaled up. All numbers are in [scores.txt](scores.txt); data hashes are in [hashes.sha256](hashes.sha256). The generated data stays in `work/action-guard/v2/pilot` (gitignored).

## Short answer

The pipeline works end to end, and its checks caught real defects.
- **Fidelity:** 233 of 244 items (95.5%) pass every check, and every pending call runs in the sandbox.
- **Cost:** about $0.33 for everything, reruns included. That is about $0.0014 per accepted item.
- **Learning signal:** the curriculum shows clear headroom over the prompted baselines. Jev gets 73% of pilot items exactly right, and untrained Clef 60%. A 16-minute Clef run on 190 items reaches 95% on 43 held-back items, against Jev's 91% on the same items.

That last comparison is **not a test result**. The held-back items share policies and text writers with the training items, there are only 43 of them, and the paired difference is 4 items against 2.

## What ran

| Step | Result |
|---|---|
| Specs (code) | 6 policies, 45 scenario families, 244 items. All six decisions appear: BLOCK 78, ALLOW_LOG 54, SEEK_CONTEXT 34, ALLOW 28, REQUIRE_APPROVAL 25, ASK_HUMAN 25. Variants: 45 base, 56 counterfactual, 34 hidden-fact, 45 irrelevant-hidden controls, 45 invariance, 19 judgment neighbours. |
| Policy rendering | 21 texts in 2 styles from DeepSeek V4.1 Flash (MIT) and Qwen3.8 27B (Apache-2.0). 15 pass on the first attempt and 16 after one regeneration. The 5 failures are all Qwen's numbered style, which keeps rewording small conditions (for example "address on file" becomes "registered address"). Their items use a passing text of the same policy. |
| Text rendering | 247 requester messages and retrieved-content items, 18 of which carry injected instructions. Mean realism score: 4.75 out of 5. |
| Fidelity checks | GPT-6 Luna extracted every fact from each item without seeing its label. 233 of 244 pass. The 11 failures: 6 contain a verdict, 3 leak a hidden recipient, 3 have an address that doesn't match the call, and 1 is missing a fact. All 11 are dropped. |
| Sandbox | 0 failures out of 233. Before fixes there were 82, from defects in my generator (below). |

## Defects the checks caught

These were defects in the pipeline, not in the model's data. Each was fixed and the affected steps rerun.
- **Filterless exports.** Exports had no record filter, so a "4 rows" dry run sat next to a call that targets everything. Caught by the input-sufficiency check.
- **Scope hidden on a filterless call.** A hidden-scope variant of a filterless call showed the filterless call anyway. That leaked the hidden fact and contradicted the possible values of the label. Caught by the leak check.
- **Invalid calls.** Updates set fields some objects don't have, and erasure deletes targeted ids the sandbox didn't hold. Caught by the sandbox check.
- **Impossible fact combinations.** For example, a public link with no data, or a data-free message with a row count. These are now excluded in the decision function itself (`valid`), including when it enumerates hidden values.
- **Invented addresses.** Writers made up their own email addresses. The brief now passes the real address, and a check compares every address in the text against the call.
- **Over-strict judges.** The faithfulness judge counted omitted company details as rule changes, and the verdict judge counted "please make an exception" as a verdict. Both now report only differences that change a decision, with the quoted text as evidence.

## Baselines

Both baselines get the same four-field request. Results on all 233 items:

| System | Exact | Macro-F1 | Seek F1 | Ask F1 | Unsafe let through (BLOCK → allow) |
|---|---:|---:|---:|---:|---:|
| Jev 1.14 (API, $0.02 total) | 73.0% | 0.651 | 0.44 | 0.28 | 4.0% |
| Clef-Flash 9B, untrained | 59.7% | 0.512 | 0.17 | 0.34 | 18.7% |

**When Jev does choose seek-context or ask-human, it names the fact or the judgment type correctly every time.** It rarely chooses them, though:

| Gold label | Jev's answers |
|---|---|
| Ask human: conflicting obligations | BLOCK 8 of 8 |
| Ask human: policy silent | BLOCK 9 of 9 |
| Ask human: discretionary exception | ASK_HUMAN 4, BLOCK 3 |
| Seek context: records touched | SEEK_CONTEXT 9 of 10 |
| Seek context: recipient affiliation | 0 of 11 (BLOCK 6, ALLOW 4, ALLOW_LOG 1) |
| Seek context: retention hold | 0 of 9 (assumes there is no hold) |

## Pilot training run

- **Setup:** Clef-Flash 9B, with LoRA rank 16 on both attention types, plus the joint head. 190 training items, 3 epochs, learning rate 1e-4, 16 minutes on the RTX 5090 using 23 GB.
- **Held-back items:** 43 items from 9 families never trained on.

| | Exact | Macro-F1 | Notes |
|---|---:|---:|---|
| Untrained Clef | 67.5% | 0.49 | – |
| Jev | 90.7% | 0.88 | – |
| Clef after 1 / 2 / 3 epochs | 74.4% / 90.7% / 95.3% | 0.90 at epoch 3 | 0 false seeks, 0 false asks, 0 unsafe let through. One seek-context item answered as ask-human. |

**Cartography:**
- 169 items are easy, 20 ambiguous and 1 hard to learn. 9 of the 20 ambiguous items are seek-context.
- The hard item is an interpretation case: job titles and employers, sent to a partner, under a policy whose definition of personal data lists only names and contact details.
- I reviewed that label and kept it. The two readings of the definition give different decisions (REQUIRE_APPROVAL against ALLOW_LOG), which is exactly what the interpretation type is meant to capture. No label errors were found.

## What changes for the full build

1. **Conflicting-obligation and policy-silent labels need the planned labeller check before they are trusted.** Jev answers BLOCK on all 17 of these. The policy-extraction model also read "conflicts go to the legal team" as "the hold wins" in 3 policy texts. For the policy owner, BLOCK and ASK_HUMAN both stop the action. So the scores will also report a **"safe stop"** view, where either counts as stopping, next to exact attribution. The cost matrix (P11) should reflect that.
2. **Policy writers:** Qwen's numbered style is unreliable, so its share of policy writing is cut. The regenerate-once rule stays.
3. **Coverage gaps:**
   - the harm-trade-off judgment type has no pilot items;
   - interpretation has few;
   - "obvious safe" erasures are unreachable under the current situation rules.

   The full principle set has to fill these.
4. **Template shortcuts are a risk.** The structured blocks (dry runs, directory lookups, record views) come from a handful of code templates. The full build varies their wording and order and lets writers produce record contents. The style-leak test (§7) will show whether the model learned the templates.
5. **Budget.** Generation is cheap: one write-and-check pass costs about $0.0004 per item at the pilot's token sizes. So about 8,500 items cost roughly $3–5, with regenerations. **Test labelling is the main cost.**
   - Two frontier labellers on all of about 1,300 test items would cost about $14, even at batch prices (around 3,000 input tokens and 500 output tokens per call).
   - The plan therefore labels a **stratified 600-item audit set** with both labellers, for about $6.6. The rest of the test labels stay program labels, checked against that audit's agreement rate.
   - Projected total: about $12–14, against $15. The output-token sizes are estimates until the first labelling batch measures them.

## Spend

The pilot cost $0.33: $0.31 counted on the OpenRouter key and $0.02 billed by Jev. The key is shared, so the $0.31 is an upper bound. The key's counter also updates with a lag, so individual steps sometimes show $0.00.
