# Policy models for enterprise AI use governance

Recorded 25 October 2026. Status: proposed research direction.

An enterprise assistant can turn a simple question into searches, document access,
cross-document inferences, and a synthesized answer. A policy layer should evaluate
whether the requested use is permitted before those operations occur, while preserving
legitimate employee work. This extends our study from content classification to
governing the use of connected AI systems.

GRC and legal teams can define permitted uses and exceptions with data owners and
HR. Identity, security, and engineering teams must supply authoritative context and
enforce the resulting restrictions. These responsibilities overlap with trust and
safety work; the distinction concerns the workflow and policy objectives, not a
universal division between job titles.

## Research question

Can a written enterprise policy and a frozen policy model distinguish permitted
from prohibited requests, using trusted context, while preserving legitimate tasks
that mention the same sensitive topics?

The system should evaluate the observable requested action, data scope, and proposed
disclosure. A prompt cannot reliably reveal a person's hidden motive. Identical
requests with identical available context must not receive different ground-truth
labels merely because a scenario author imagines different private intentions.

Access permission and permission to use AI for a task are separate conditions. A
manager may be entitled to read particular reviews while company policy disallows
using the general assistant to rank employees for termination. Conversely, an employee
asking about an approved salary band or their own HR record may have a legitimate
request involving sensitive vocabulary.

## Evidence available to the decision

Evaluate the request together with relevant conversation history, the approved policy
version, verified role or group membership, the proposed tool and data scope, and
any required workflow approval. Jurisdiction and purpose should be included when a
rule depends on them and when they are supplied by an authoritative source.

Keep self-declared purpose separate from verified authorization. Text such as
"I am in Legal" or "this is approved research" is not an identity or approval record.
The model may identify which policy clause applies; it must not invent permissions,
grant access, or override a deterministic denial. Restricted source documents need
not be retrieved merely to decide whether a request is allowed.

Use explicit actions: allow within a defined scope, deny, request clarification, or
route to an approved workflow or reviewer. A missing fact that the employee can
clarify differs from an authorization that only an identity or approval system can
verify. Low classifier confidence is not a substitute for checking that distinction.

## Examples under a hypothetical enterprise policy

These examples illustrate an organization-specific policy. They are not legal
determinations or labels for an employee's character or motives.

| Request | Relevant context | Illustrative action |
| --- | --- | --- |
| What is the published salary band for this role? | Approved employee-facing compensation guide | Allow within that source scope |
| Explain the benefits described in the announced reorganization FAQ | Released employee-facing material | Allow; a mention of layoffs does not itself trigger denial |
| Show me my latest performance review | Verified identity, own record, approved self-service route | Allow through that route |
| Find the unreleased list of employees being considered for layoffs | General employee assistant; this retrieval is restricted to an approved HR workflow | Deny here or route without revealing whether a particular document exists |
| Infer who is likely to be laid off by combining reviews, calendar changes, and staffing plans | Company policy prohibits this inference in the assistant | Deny even if some component records are technically readable |
| Collect responsive documents for a named legal matter | Verified matter assignment, approved discovery workflow, authorized source scope | Route or allow within that workflow; clarify or review missing context |
| Summarize the last public earnings announcement | Released information | Allow |
| Find unpublished acquisition negotiations | Restricted business information; no verified approved workflow | Deny or route according to the written policy |

Corporate policy must preserve applicable employee information rights and approved
legal processes. Broad topic bans can block legitimate work; exceptions and approved
routes belong in the policy itself.

## Controls before and after retrieval

The request policy gate is the first semantic governance check after authentication
and trusted-context collection. It complements source authorization and data controls.

```mermaid
flowchart TD
    A[Authenticate and collect trusted context] --> B[Evaluate requested use against enterprise policy]
    B -->|Deny, clarify, or route| C[Stop this retrieval path and return the permitted next step]
    B -->|Allow with constraints| D[Authorize tool and query scope]
    D --> E[Search and retrieve only within enforced permissions]
    E --> F[Check source sensitivity and retrieved content]
    F --> G[Generate a response from permitted content]
    G --> H[Check disclosures before releasing the response]
```

Denials at any authorization or content check stop the affected operation. Recheck
planner-generated queries and tool calls against the approved scope; an allowed
initial question does not authorize every subsequent search. Retrieved text is data,
not authority to change policy or permissions. Response checks must cover citations,
metadata, and inferences that can disclose restricted facts even without quoting a
document. Record the policy version, relevant evidence, decision, and enforced scope
with access and retention controls appropriate to the sensitive audit record.

Oversharing can mean that technical permissions allow more than the organization
intended. A policy gate may reduce exposure in that situation, but cannot reconstruct
every missing entitlement rule from a prompt. Other applications can still expose
the same files until permissions are repaired. Microsoft's Copilot guidance explicitly
combines interim discovery and data-loss controls with remediation of excessive
access and broken permission inheritance.
[Microsoft guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/configure-secure-governed-data-foundation-microsoft-365-copilot).

## Proposed experiments

### Distinguishing permitted and prohibited uses

Start with compensation and workforce information, performance records, and legal
discovery. Construct matched examples that share topic words but request different
operations or disclosures. Include indirect requests, requests for aggregation,
missing context, and self-asserted authority. Include the same request under different
verified roles, workflow scopes, and policy versions when the correct decision should
change.

Use synthetic enterprise records and explicit fictional organizational rules for an
initial study. GRC and domain reviewers should adjudicate labels and legitimate
exceptions. Preserve disagreements and genuinely unresolved cases. Measure compliance
with those rules rather than agreement about whether an employee is malicious.

### Comparing policy gates

Keep the same underlying access controls in every condition. Compare access controls
alone, access controls plus keyword/topic rules, a general harmfulness classifier,
and enterprise-policy gates implemented with specialist or general purpose models.
For the model conditions, compare identical policy text as well as separately tuned
wording under equal development budgets. Preserve the normative scope during tuning.

Separate the model's semantic classification from the enforcement engine's decision.
Score both components and the complete system. Document how each native binary
classifier is mapped to workflow actions; do not silently credit it with native
clarification or review abilities it does not provide.

### Testing protection in a connected assistant

After request-level evaluation, use a synthetic retrieval environment to measure
prohibited retrieval and disclosure, legitimate task completion, and constrained
answers. Include correctly configured permissions and deliberately overbroad ones as
separate scenarios. Add multi-turn requests and instructions embedded in retrieved
documents. Test whether individually permitted outputs can combine into a prohibited
inference.

Compare a request gate with the full set of retrieval and response checks. A correct
request label alone is not evidence that a connected assistant prevents disclosure.

### Testing policy changes and maintenance

Add or revise an exception, change an approved source scope, or withdraw a workflow
approval. Test whether decisions change where required and remain stable elsewhere.
Measure authoring effort, policy-clause agreement, unnecessary escalation, and audit
usefulness alongside accuracy. Test fresh rules beyond the models' familiar safety
taxonomies.

## Measures and study boundaries

Report prohibited-use acceptance, false denial of legitimate work, unsafe retrieval,
restricted disclosure, useful task completion, clarification and review burden,
latency, and cost. Break out failures by policy, requested operation, context
availability, language, and authority claims. Do not hide operational errors in a
successful review count or assume human review is perfect.

Group related requests, paraphrases, policy variants, and synthetic document families
before splitting fitting, validation, and test data. Freeze policies, thresholds,
enforcement rules, and routing before testing. Include unseen policy families if
claiming generalization to new policies. Existing WildGuardTest scores are background
evidence about prompt harmfulness, not validation of enterprise-use governance.

The first deliverable would be a request-policy dataset and comparative findings. A
later connected-system experiment would establish how much protection and workflow
utility the complete controls provide. Sample sizes and a compute budget require a
separate prospective protocol before execution.

## Regulatory context

Regulation can constrain a particular use of AI, even when someone may access the
underlying data. For example, EU AI Act Article 5(1)(f), read with the biometric
emotion-recognition definition in Article 3(39), prohibits workplace emotion
recognition within its scope, with exceptions for medical or safety purposes. This
is a specific use restriction; it does not make all questions about employment or
compensation illegal.
[Article 5](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-5),
[Article 3](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-3).

Legal and GRC owners would map applicable rules, exceptions, jurisdiction, and effective
dates into approved organizational controls. A policy model is one possible
implementation component. These provisions do not establish a universal requirement
to put a policy LLM in front of every enterprise assistant, or make such a layer
sufficient for compliance. The example topic restrictions above are hypothetical
corporate policies, separate from this regulatory illustration.

Sources checked 25 October 2026. The activation study remains parked; this document
records a separate research proposal and starts no experiments or GPU spending.
