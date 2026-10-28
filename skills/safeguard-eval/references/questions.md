# Questions this skill can help answer

Use this as a route to the relevant evidence, not a script that forces every answer
into the same shape. Source IDs resolve through [sources.json](sources.json).

| User asks | Start with | Essential distinction |
|---|---|---|
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
| Could this govern employee requests? | [Authoring](authoring.md), `enterprise-track` | Proposed application, not validated intent detection or permission repair. |
| Which is cheapest, fastest, or commercially licensed today? | Current publisher documentation | Historical research compute bills are not serving benchmarks or current terms. |

Useful starter questions:

- Explain to a trust and safety policy owner why policy and model must be tested together.
- What exactly changed in the HateXplain policies, and which changes were rejected?
- Show a successful policy transfer and an unsuccessful reverse transfer.
- How do PolicyLM and Shieldstral expect me to deliver a policy?
- Help me draft an untested policy and a small evaluation plan for my own content.
- What did the ensemble add after individual models were calibrated?

If the user asks for an untested model, a new domain, or a claim absent from the
evidence, identify that gap. Offer a test design when useful. Do not fill it with an
invented result, a live benchmark claim, or an unsolicited paid run.
