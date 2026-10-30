# Implementation notes

* A separate implementation preserves the earlier frozen PolicyLM/Qwen study.
* The same populations and overlap exclusions were verified before inference.
* Both models receive the existing Shieldstral p4 policy through their native
  templates. Qwen content honors its template's outer-whitespace trimming.
* Direct score controls condition on the canonical pair of label tokens; they
  are not a test of unconstrained generated-label compliance.
* Eleven tests cover fitting/scaling, missing cases, split separation, score
  combinations, mutation guards, complete selection/evaluation and reproduction.
