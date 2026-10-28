# Questions this skill can help answer

Use this as a route to the relevant evidence, not a script that forces every answer
into the same shape. Source IDs resolve through [sources.json](sources.json).

| User asks | Start with | Essential distinction |
|---|---|---|
| What is this about? Give me a quick overview. | [Start here](start-here.md) | Welcome, a familiar workflow, then a few next directions; no background knowledge required. |
| What do I do after installing? | [Start here](start-here.md) | Give the overview now, not just another list of files to read. |
| How did we get from rules to policy models? | [Start here](start-here.md), basics narrative | The tools can coexist; natural-language policies still need examples and tests. |
| Can you walk me through writing a policy? | [Walkthrough](walkthrough.md) | An untested teaching draft and test plan, not an inference result. |
| Which datasets were used, and where do I get them? | [Datasets](datasets.md) | Used benchmark, synthetic demonstration, and proposed dataset are different statuses. |
| Did you test every WildGuard task? | [Datasets](datasets.md), `wildguard-methods` | Prompt harmfulness only; not response harmfulness or refusal. |
| Did HateXplain mean blocking all offensive text? | [Datasets](datasets.md), `hatexplain-data` | Hate was BLOCK; offensive and normal were ALLOW. |
| Where are the models and their policy guides? | [Providers](providers.md), [models](models.md) | Exact checkpoint and native contract; current cards versus frozen runs. |
| What does OpenAI recommend for Safeguard policies? | [Providers](providers.md), official Safeguard guide | Provider recommendations are starting points, not optima proven here. |
| Can you download or summarize the research paper? | [Paper](paper.md) | Read the actual version; review draft, not arXiv or peer-reviewed publication. |
| What is ROOST doing, or what other guards exist? | [Providers](providers.md), [search](search.md) | Discovery resources are not an evaluated comparison panel. |
| Does changing a policy really change outcomes? | [Studies](studies.md), sections 1 and 4 | Wording, examples, presentation, and cutoffs are different interventions. |
| What is a selected policy? | [Studies](studies.md), section 1 | A validation choice from a bounded search; baseline can win. |
| Can I use one policy with every model? | [Models](models.md), [studies](studies.md), section 3 | Shared source plus native adapters can help; behavior still needs testing. |
| Were the earlier experiments invalid because formats differ? | `interface-audit` | Native adapters were already used; best authoring practices were not exhaustively optimized. |
| Can PolicyLM beat a larger Qwen? | [Studies](studies.md), sections 2 and 3 | Do not substitute Shieldstral's result for PolicyLM or mix studies. |
| Should I remove examples or definitions? | [Studies](studies.md), section 4 | Opposite changes across models and hidden error trade-offs; no universal recipe. |
| Are XML tags or Markdown headings best? | [Models](models.md), `hatexplain-results` | Required native packaging differs from presentation ablations. |
| Can I avoid fine-tuning? | [Studies](studies.md), section 5 and its closing discussion | No additional LM fine-tuning here; upstream training and labelled combiner fitting remain. |
| Is an ensemble always better? | [Studies](studies.md), section 5 | Calibrated individual controls matter; specialist-only HateXplain did not win. |
| Did you collect raw logits? | `logits-claims` | The extension reconstructed log-odds from saved class probabilities. |
| Can the model return REVIEW? | [Models](models.md) | Main studies are binary; a third workflow state needs separate validation. |
| What about prompt injection? | `injection-results` | Earlier demo, separate dataset and protocol; not WildGuard's task. |
| Were the first 48 scored prompts from DiffusionDB? | [Datasets](datasets.md), `demo-methods` | No; the scored set was original synthetic data. |
| Could this govern employee requests? | [Authoring](authoring.md), `enterprise-track` | Proposed application, not validated intent detection or permission repair. |
| Which is cheapest, fastest, or commercially licensed today? | Current publisher documentation | Historical research compute bills are not serving benchmarks or current terms. |
| Can a new model handle my company's policy? | [Search](search.md), [authoring](authoring.md) | An input interface is not empirical validation in that domain. |

Useful starter questions:

- Explain to a trust and safety policy owner why policy and model must be tested together.
- What exactly changed in the HateXplain policies, and which changes were rejected?
- Show a successful policy transfer and an unsuccessful reverse transfer.
- How do PolicyLM and Shieldstral expect me to deliver a policy?
- Help me draft an untested policy and a small evaluation plan for my own content.
- What did the ensemble add after individual models were calibrated?
- Explain WildGuard and HateXplain to someone choosing their first benchmark.
- Find the official policy-writing guidance for my checkpoint and compare it with our adapter.
- Read the v0.5 paper and summarize what a policy owner should learn from it.

If the user asks for an untested model, a new domain, or a claim absent from the
evidence, identify that gap. Offer a test design when useful. Do not fill it with an
invented result, a live benchmark claim, or an unsolicited paid run.
