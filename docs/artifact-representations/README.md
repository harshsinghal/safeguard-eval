# Code embeddings and Qwen for code and skill screening

**Status: registered; development evaluation running.**

This follow-up asks whether a compact learned classifier can make better use of
code representations than an LLM applying instructions. It also expands the
instruction search for Qwen and includes a larger Qwen model. The models inspect
source files and skill documentation as text. They never run that content.

We compare two paths:

1. **Write the decision rule:** give Qwen3.5 4B or 9B a policy describing malicious
   behavior. Test six policy versions on validation, then freeze the selection.
2. **Learn the decision boundary:** embed each artifact with a frozen Jina model,
   then train logistic regression or a small neural network on labeled examples.
   The embedding model's weights stay unchanged.

Both paths use the exact input views and splits from the
[eight-system artifact benchmark](../malicious-artifacts/README.md). That study
already tested Qwen 4B; this is an extension, not its first evaluation.

Networking, credentials and deletion appear in legitimate tools too. The new
policy candidates contrast authorized uses with covert, unrelated or destructive
actions. They also distinguish a skill's active instructions from quoted examples.
The benchmark labels remain binary. This study does not claim separately
validated detectors for networking, destruction or every attack category.

[Registered plan](PLAN.md) · [Methods](METHODS.md) ·
[Running the study](RUNNING.md) · [Existing data limits](../malicious-artifacts/METHODS.md)
