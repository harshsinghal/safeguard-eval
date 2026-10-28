# Safeguard Eval — Pi conversation review

Run: 20261028T194335Z-9354a9. Model: openai/gpt-6-luna. Skill: 0.4.0.

Local review only. Check for private information before sharing. No automatic upload.
Original visible turns are in append order; IDs preserve branches. Reasoning and tool payloads are excluded.

## Usage

```json
{
  "tokens": {
    "input": 21,
    "output": 1888,
    "cacheRead": 53615,
    "cacheWrite": 17942,
    "totalTokens": 73466
  },
  "model_responses": 7,
  "pi_estimated_cost_usd": 0.0037250000000000004,
  "assistant_messages_missing_usage": 0,
  "openrouter_cost_usd_for_available_records": 0.0037250000000000004,
  "billing_records_available": 7,
  "billing_records_requested": 7
}
```

Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.

## User · 6ec4eb49 (parent c37fa7be)

We want our enterprise AI assistant to stop employees looking for secret layoff plans, but allow questions about public salary bands. Can your research help us?

## Assistant · 7a26c071 (parent 0abe7b69)

Yes. The research can help you **draft and evaluate a policy**, but it does not establish that a model can reliably detect attempts to find confidential company information. For this use case, pair the policy with **source permissions and retrieval controls**—don’t rely on intent classification alone.

### Untested policy draft

> **Scope:** Apply to employee requests and retrieved content involving workforce planning.  
> **Block:** Requests seeking, locating, summarizing, inferring, or revealing nonpublic layoff plans, lists of affected employees, or confidential deliberations about planned workforce reductions.  
> **Allow:** Questions about salary bands that are officially public or that the employee is authorized to access.  
> **Allow:** General questions about publicly announced workforce changes, and responsible reporting or discussion that does not expose confidential details.  
> **Boundary:** A question mentioning layoffs or compensation is not by itself a violation. Use the sensitivity and authorization of the requested information, not keywords alone.  
> **Unclear cases:** If confidentiality or authorization cannot be determined, don’t retrieve or disclose the material; route for review or ask the user to use an authorized source.

You’ll need to decide what counts as “public” (for example, whether a company-approved internal salary-band document qualifies) and how to handle authorized HR users, public announcements, and requests to infer plans from indirect signals.

### How to test it

Build examples for both sides of the boundary: direct and indirect requests for secret plans, requests for public salary bands, mixed requests, public announcements, authorized access, and ambiguous cases. Have policy owners label them, then measure **missed disclosures** and **false blocks of legitimate salary questions** separately. Freeze the policy, model, adapter, and decision rule before evaluating on held-out examples; review the individual errors, not just one aggregate score.

The research guidance emphasizes defining permitted cases and exceptions, checking that the model’s input format preserves every policy clause, and evaluating false blocks as well as missed violations. It also cautions that successful policy rendering does not prove the model will apply the policy correctly. See [Authoring and testing](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/research-directions/POLICY-INTERFACE-AUDIT.md) and [enterprise governance](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/research-directions/ENTERPRISE-AI-GOVERNANCE.md).

This is a proposed draft, not a policy or performance result validated by the experiments. The research supports a careful authoring and evaluation process; it does not demonstrate this specific enterprise use case.

## User · 99ab8584 (parent 7a26c071)

Help me make a first draft. What decisions do we need to make before testing?

## Assistant · 74b8bf7a (parent 99ab8584)

Here’s a **first-pass decision checklist**. The aim is to settle the policy’s meaning before choosing a model or measuring its performance.

### 1. What information is protected?
Define exactly what “secret layoff plans” includes. For example:

- Unannounced plans, dates, locations, teams, or selection criteria
- Lists or identities of potentially affected employees
- Internal deliberations, drafts, or forecasts
- Attempts to infer plans from indirect clues, such as meeting notes or budget changes

Decide whether the rule covers only confirmed plans or also speculation and preliminary proposals.

### 2. What counts as public or authorized?
Clarify which sources qualify:

- Public salary bands, and where they must be published
- Approved internal salary-band information, if employees may access it
- Publicly announced workforce changes
- Information available to specific roles, such as HR or legal

“Public” and “authorized” should be distinct: authorized internal information may be accessible to some users without being public.

### 3. What should the assistant do with mixed requests?
For a request that combines an allowed question with a prohibited one—for example, “What are the public salary bands, and which teams are about to be cut?”—decide whether it should answer the allowed part while refusing the rest, or refuse the whole request.

Also decide what to do when the assistant cannot tell whether a source or detail is confidential.

### 4. Which contexts are allowed?
Set boundaries for requests about:

- Public news or official announcements
- General explanations of salary-band policy or workforce planning
- Reporting a suspected confidentiality breach
- Authorized business tasks

Don’t let words like “layoff” or “salary” decide the outcome by themselves; the requested information and the user’s authorization matter.

### 5. What actions count as disclosure?
Decide whether the policy should block only revealing protected information, or also searching for it, summarizing it, confirming a guess, or combining clues to infer it. Also decide whether the assistant may explain that it can’t help with confidential plans without confirming whether any such plan exists.

### 6. Who owns the trade-offs?
Name the people responsible for approving the protected categories, allowed cases, and acceptable errors. For example: policy or HR leadership for scope, security and data owners for access rules, and engineering for retrieval controls and model behavior.

### 7. What will count as a successful test?
Before testing, agree on:

- The labels and examples used to evaluate decisions
- How you’ll measure missed disclosures versus false blocks of legitimate salary questions
- Which errors are unacceptable, and what happens in ambiguous cases
- Which model, policy rendering, and decision settings are held fixed during evaluation

Include paired examples that differ only in a crucial detail—such as secret versus officially announced plans, or public versus restricted salary bands. That helps reveal whether the system is following your intended boundary.

These are policy-owner decisions, not model-tuning choices. The research recommends making the rules and exceptions explicit, then testing the specific policy/model/adapter combination; it does **not** establish that a model can reliably infer employee intent or replace access controls. Keep source permissions and retrieval restrictions in place alongside any classifier. See the [authoring guidance](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/research-directions/POLICY-INTERFACE-AUDIT.md) and [enterprise governance direction](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/research-directions/ENTERPRISE-AI-GOVERNANCE.md).

A useful first step is to answer **what counts as public salary information** and **whether the assistant should answer the allowed part of a mixed request**. Those choices change the examples and the expected behavior most directly.

## User · a8c71459 (parent 74b8bf7a)

Does your ensemble show we can get better results without any training or labels?

## Assistant · cded14c4 (parent 5150f0b2)

**Not quite.** The models’ weights stayed fixed, so the ensemble did **not** require additional fine-tuning of the language models. But it **did** use training examples and labels: a small combiner was fitted on labelled data, then selected using validation data.

On the tested tasks, the selected ensemble scored **91.29% accuracy on WildGuard** and **80.82% on a mixed-model HateXplain cohort**. The HateXplain figure was higher than the cited individual-model test result, but the ensemble also missed more hateful posts than its Shieldstral comparator. There wasn’t a consistent ensemble win across tasks.

So the accurate takeaway is: **competitive results were possible without fine-tuning the base models, but not without training or labels.** And those results were on prompt-harmfulness and hate-speech benchmarks—not confidential layoff information or public salary-band questions. They don’t show that this approach will work for your enterprise policy. [Study findings](https://github.com/harshsinghal/safeguard-eval/blob/5f042bda96b377dccc805f052a72914efb6b055c/docs/ensemble/READOUT.md)

