# Can better retrieval and example formatting improve the result?

**Status: a completed analysis of saved validation outputs, followed by a proposed
experiment.** No new model inference has run. The original study and its frozen
archive remain unchanged. This diagnosis adds no GPU or API charges.

The first study tested a simple retrieval configuration. It did not establish the
best accuracy obtainable with retrieved examples. A stronger embedding model,
better examples and a more suitable native format are reasonable things to test.
We do not yet know which of them would help, or by how much.

## What the first experiment left open

We used **intfloat/e5-small-v2**, a 33.4-million-parameter encoder producing
384-dimensional vectors. Neighbors were ranked by exact cosine similarity. Both
sides received the `query:` prefix, as its publisher recommends for symmetric
similarity tasks. Mean pooling and normalization followed the model's approach;
our extension for long targets pooled complete windows instead of clipping the
target. This was a working semantic-search baseline, not a task-trained example
selector. [E5 model card](https://huggingface.co/intfloat/e5-small-v2).

There was one encoder, one fixed example set, four examples per condition, and no
reranker, example-order search, relevance filter or learned selection rule. Only
1,814 distinct training groups were eligible. The length/content filter excluded
2,138 of the 4,096 fitting rows, then 144 eligible duplicates were collapsed. The
short-example restriction made input lengths manageable, but may have removed
useful coverage. That possible effect has not been isolated.

Semantic similarity is also different from usefulness for a policy decision.
For example, asking how to recognize a threatening message and asking someone to
compose a threatening message share a topic. A useful demonstration should help
explain the difference in the requested action. Our search did not explicitly
represent that distinction. Research on demonstration selection has found that
usefulness depends on the receiving model and the task, and that examples which
resolve label ambiguity can outperform similarity alone. Those findings motivate
a test here; they are not evidence that our classifiers will obtain the same
gains. [Model-dependent selection](https://arxiv.org/abs/2401.12087),
[ambiguity-aware selection](https://arxiv.org/abs/2309.07900).

## Format compatibility is not the same as effective conditioning

**PolicyLM:** our adapter put labeled JSON examples after the existing exceptions
in `exception_override`. The native schema and length checks passed, after a
documented single-line formatting fix. However, this field has a policy meaning:
it describes exceptions and precedence. The publisher recommends compact
categories with violation rules, non-violation rules and exceptions. It does not
establish our JSON suffix as an effective few-shot interface. Putting examples
there was an experimental choice, not a verified best practice.
[Pinned publisher guidance](https://huggingface.co/musubilabs/policylm-1.7b/blob/b3b2cd408a08a68ab6a30c1fc1e440204e44d57e/README.md).

**Shieldstral:** the outer structure followed its native interface: instructions
in `Instruct`, one yes/no question in `Query`, and the target in `Document`.
Examples went into `Instruct`. That preserves the policy/content boundary, but
does not establish the best wording, placement or number of demonstrations.
[Shieldstral model card](https://huggingface.co/mistralai/Shieldstral-1.0-3B).

The original report explicitly called PolicyLM's example conditioning
experimental. It is still a valid measurement of that configuration. It cannot
support the broader claim that either specialist cannot benefit from examples.

## What the saved validation outputs tell us

This is a **post-hoc descriptive analysis**, not a new preregistered comparison.
It reads public validation metadata, saved neighbors and predictions only. It
does not read test labels or source prompt text.

Of 718 benign validation targets, 250 had a harmful-labeled nearest neighbor.
For 205, at least three of the four nearest neighbors were harmful-labeled.
That is a reason to audit whether retrieval is matching topic rather than the
policy distinction. It is not proof of bad retrieval: opposite-label examples
can be useful contrasts, and the bank's label quality also matters.

More revealingly, **238 benign targets had four benign neighbors**. For this same
subset, PolicyLM's false blocks increased from **9 without examples to 25 with
nearest examples**. A shortage of benign demonstrations cannot be the whole
explanation. Presentation, example content and the model's response to longer
policy text remain plausible contributors; this analysis does not distinguish
them. The class-balanced condition also reduced PolicyLM validation accuracy,
so enforcing a two/two label balance was not sufficient.

| Validation condition | PolicyLM false blocks | PolicyLM missed harmful prompts |
|---|---:|---:|
| Policy only | 50 | 68 |
| Four fixed examples | 121 | 52 |
| Four nearest examples | 183 | 39 |
| Two nearest per class | 172 | 46 |

The examples changed the pattern of mistakes. They did not simply fail to have
an effect. On the already reported test, the nearest-example condition similarly
removed 57 misses while adding 97 false blocks. Neither observation identifies a
causal mechanism. PolicyLM had identical validation message-window counts across
conditions, so changed window counts do not explain this comparison.

[Reproducible validation counts](validation-retrieval-audit.json) include the
other three classifiers and input hashes. Regenerate them without credentials:

```bash
python3 tools/audit_retrieved_examples.py \
  --archive published_runs/2026-11-01-retrieved-examples \
  --output /tmp/validation-retrieval-audit.json
```

## Proposed follow-up: separate the changes before combining them

This is a design proposal, **not a registration or a scheduled paid run**. The
final candidate list, search budget and evaluation population must be recorded
before new inference.

1. **Audit the example bank using training data.** Review a fixed, reproducible
   sample for label ambiguity, requested action, policy category, duplication and
   coverage. Inspect the excluded long examples. Preserve benchmark labels; record
   any proposed exclusions or corrected labels as a separate intervention.

2. **Test native presentation while holding examples constant.** Begin with
   PolicyLM and Shieldstral. Compare the current JSON suffix against compact
   allowed/prohibited illustrations in the relevant native policy fields. For
   PolicyLM, put blocked cases with violation rules and allowed cases with
   non-violation rules, preserving the existing exception field. For Shieldstral,
   keep the native query and target boundary, and use clearly labeled cases in
   `Instruct`. These are candidate formats to validate, not publisher-certified
   recipes. Keep the exact example texts, labels, order and base policy clauses
   fixed. If examples are summarized into new rules or given new rationales,
   treat that as a separate policy-authoring experiment.

3. **Compare retrievers under the same bank and format.** Keep E5 as the baseline.
   A practical instruction-aware comparison is Qwen3-Embedding-0.6B and 4B, using
   their documented pooling and query instructions. Their cards report embedding
   benchmarks and support task-specific retrieval instructions. The next run
   should check the current MTEB English retrieval results before freezing its
   shortlist; these names are not a claim about today's number-one model.
   Include a lexical-search control if the bounded search budget permits it.
   Expand the bank only in a separate comparison, so bank size is not confused
   with encoder quality. [Qwen embedding models](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B),
   [MTEB leaderboard](https://leaderboard.mteb.org/).

4. **Test relevance to the decision, not just the topic.** Retrieve a candidate
   pool, then compare direct nearest neighbors with a selector that favors the
   same requested action, relevant allowed/blocked contrasts and nonredundant
   cases. An instruction-aware reranker is a candidate, not an assumed upgrade.
   Compare zero, two and four examples; permit no examples when no useful match
   exists. Do not force an unrelated opposite-label case just to balance labels.
   Any learned usefulness score or error-based selector must use fitting-only
   cross-validation, never evaluation labels.

5. **Combine only promising choices and freeze them per classifier.** Bound and
   disclose the search. Select by validation accuracy, then balanced accuracy,
   then fewer examples, while reporting false blocks and misses separately. Retain
   policy-only and original-retrieval controls. Check multiple prespecified fixed
   example sets rather than attributing results to one fortunate or unfortunate
   set. Keep model weights and output cutoffs unchanged; calibration would be a
   different experiment.

6. **Evaluate after selection is closed.** Report corrected and newly introduced
   errors, both error rates, accuracy, balanced accuracy and paired uncertainty.
   Keep retrieval training-only and separate duplicate groups. The existing
   WildGuardTest has already informed multiple studies, including this follow-up
   question; another score on it remains exploratory. A newly reserved,
   independently labeled population would provide stronger confirmation. Never
   describe further tuning on this reused benchmark as a fresh blind test.

The objective is to find examples that help a particular interpreter make fewer
mistakes. A higher embedding benchmark rank or higher nearest-neighbor label
agreement is useful diagnostic evidence, but the final criterion remains the
moderation system's performance on examples excluded from development.
