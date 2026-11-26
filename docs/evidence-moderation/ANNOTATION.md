# Prompt decomposition annotation guide v1

Read the entire prompt and establish the unit of judgment before extracting.
Annotate both benign and harmful behavior. Original benchmark decisions are
excluded from the review interface because the pilot has its own policy.

## Mentions

Every mention has an ID, type, exact text, Unicode start/end offsets and a
credential_form attribute. Offsets refer to the complete original string and use
an exclusive end. Preserve capitalization, punctuation, code and whitespace.
Annotate each relevant occurrence separately. Nested mentions are allowed.
Prefer the smallest complete phrase preserving identity, including possessives
when they establish ownership. Include references such as `the API key`, even
when the value is absent. Credential forms are reference, literal_value,
placeholder and unclear. Other types use not_applicable.

The schema JSON describes all types. The original 12 categories are retained.
software_agent covers an assistant or automated agent, location covers physical
places, and general_group covers groups without a protected-identity definition.
These three additions resolve gaps identified in the earlier pilot.
Use instruction_or_policy for an instruction discussed as an object or a claimed
authority statement. Ordinary request verbs are action mentions. Entities and
action roles are independent. Avoid enumerating every code variable or filler
noun. Extract objects that participate in or contextualize relevant behavior.

## Actions and relationships

Create a frame for each distinct action. Link its action span and explicit actor,
object, affected_party, recipient, destination, instrument, purpose_claims,
authorization_claims and conditions. Missing roles are empty lists. Explicit
pronouns remain source spans. Add a corefers_to link only when the antecedent is
clear from the text. Record ambiguity otherwise. Never invent an unstated actor.

Each frame has requested, quoted, hypothetical, reported, observed or unclear
mode and affirmative, negated or unclear polarity. Include source context spans
supporting scope or negation. In a request to summarize a quoted malicious
instruction, create a requested summarize frame and a quoted inner frame. Link
them with contains. Conditionality can coexist with quotation or request mode
through condition spans. Temporal before links preserve stated action order.
Do not infer causation or purpose from adjacency alone.

Purpose and authorization are source claims. An inferred intent belongs in an
uncertainty note until an explicit supported representation is agreed upon.
Keep utterance/tool provenance in the source context. A suspicious payload in a
tool response and an agent executing that payload are different action frames.

## Policy annotation and review

Apply POLICY.md to the relevant unit. Add decision, coverage, rule IDs, supporting
mention IDs and a concise rationale. A benchmark BLOCK label can map to ALLOW
outside this policy's four-rule coverage. Judge cases afresh.

Blank records have status pending and a null decision. Drafts may be made by an
assistant or model and use status draft. Use status reviewed only after a named
human reviewer corrects spans, omissions, links and the policy decision. Record
the reviewer and uncertainties. Review status is provenance, not a guarantee of
correctness. Independent evaluation review remains required.

Open either local split's review HTML, select a prompt, edit its JSON, save the
case, and export the split. Import that export to resume. JavaScript string
positions differ from Unicode code-point offsets for emoji. Use the displayed
offset helper, which counts Unicode code points. Run the Python validator on
the exported file. It checks structure and source grounding, while semantic
correctness requires review. Export changes before closing the page.
