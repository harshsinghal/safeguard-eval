# Implementation notes

* A separate implementation preserves the earlier frozen PolicyLM/Qwen study.
* The same populations and overlap exclusions were verified before inference.
* Both models receive the existing Shieldstral p4 policy through their native
  templates. Qwen content honors its template's outer-whitespace trimming.
* Direct score controls condition on the canonical pair of label tokens; they
  are not a test of unconstrained generated-label compliance.
* Eleven tests cover fitting/scaling, missing cases, split separation, score
  combinations, mutation guards, complete selection/evaluation and reproduction.

* Pre-fit technical repair: Transformers 5.10.2 returns a BatchEncoding from
  `apply_chat_template(tokenize=True)` by default. Comparing that container to a
  token list triggered the first smoke guard. The contained token IDs matched
  exactly; normalize the return container before comparing. No token IDs, policy
  text, feature definitions or search choices changed, and no fitting had begun.
