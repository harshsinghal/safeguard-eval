"""v2 decision contract, policy parameters and the decision function (design §1, §5 steps 1-2).

Labels come from code only. `decide` maps (policy, fully known facts) to a certain decision or
ASK_HUMAN. `resolve` adds hidden facts: if some value of a hidden fact changes the outcome, the label
is SEEK_CONTEXT naming that fact (P8); if no value does, the certain label stands (the control case).

Pilot scope: three principles (bulk change and deletion, data egress, erasure and retention) plus the
cross-cutting untrusted-instruction rule. Four of the five judgment types are reachable; the harm
trade-off type joins with the full principle set.
"""
from dataclasses import dataclass, field
from itertools import product

DECISIONS = ("ALLOW", "ALLOW_LOG", "REQUIRE_APPROVAL", "BLOCK", "SEEK_CONTEXT", "ASK_HUMAN")
CERTAIN = DECISIONS[:4]
RANK = {d: i for i, d in enumerate(CERTAIN)}

# Fixed `missing` list (design §1): key -> (description, where the guard's caller should get it).
MISSING = {
    "contract_status": ("the contract status", "lookup"),
    "recipient_affiliation": ("who the recipient is affiliated with", "lookup"),
    "records_touched": ("how many records the action touches", "dry_run"),
    "record_owner": ("who owns the record", "lookup"),
    "deal_stage": ("the deal stage", "lookup"),
    "initiated_by": ("whether the user or retrieved content initiated the action", "requester"),
    "evidence": ("whether supporting evidence exists", "requester"),
    "personal_data": ("whether the data contains personal data", "dry_run"),
    "approval_exists": ("whether an approval already exists", "lookup"),
    "prior_decline": ("whether this was declined before", "lookup"),
    "data_purpose": ("the purpose of the data", "requester"),
    "consent_status": ("the customer's consent status", "lookup"),
    "retention_hold": ("whether a retention or legal hold applies", "lookup"),
    "requester_role": ("the requester's role", "lookup"),
    "is_duplicate": ("whether the records are duplicates", "lookup"),
}
SOURCES = ("requester", "lookup", "dry_run")
QUESTIONS = {
    "conflicting_obligations": "two obligations in the policy conflict and the policy sets no precedence",
    "discretionary_exception": "the policy leaves an exception to a person's discretion",
    "interpretation": "the decision turns on how a policy term is read",
    "harm_tradeoff": "the decision trades off harm to a customer or third party",
    "policy_silent": "the policy does not address a material risk in the action",
}

# Policy parameters (the clause library for the pilot principles). Each key is one clause option.
PARAM_SPACE = {
    "bulk_n": (10, 25, 100),
    "single_change": ("ALLOW", "ALLOW_LOG"),
    "bulk_update": ("ALLOW_LOG", "REQUIRE_APPROVAL"),
    "bulk_delete": ("REQUIRE_APPROVAL", "BLOCK"),
    "duplicate_exempt": (False, True),
    "cleanup_exception": (False, True),
    "internal_bulk_personal": ("ALLOW_LOG", "REQUIRE_APPROVAL"),
    "external_no_data": ("ALLOW", "ALLOW_LOG"),
    "external_personal": ("REQUIRE_APPROVAL", "BLOCK"),
    "external_sensitive": ("REQUIRE_APPROVAL", "BLOCK"),
    "partner_consent": (False, True),
    "personal_definition": ("list", "broad"),
    "catch_all_external": (False, True),
    "hold_precedence": (False, True),
    "unverified_erasure": ("REQUIRE_APPROVAL", "BLOCK"),
}

# Fact domains per principle. `HIDEABLE` maps facts that can be withheld to their `missing` key and the
# values still possible when they are withheld (a withheld recipient is an unfamiliar external address,
# so it cannot be internal).
COMMON = {"provenance": ("user", "content"), "requester_role": ("rep", "manager", "ops")}
SCOPES = (1, 4, 12, 30, 60, 150, 600)
FACTS = {
    "bulk_change": {**COMMON, "verb": ("update", "delete"),
                    "object": ("leads", "contacts", "tasks", "cases", "accounts"),
                    "scope": SCOPES + ("all",), "is_duplicate": (False, True), "exception_invoked": (False, True)},
    "egress": {**COMMON, "verb": ("send", "export"),
               "recipient": ("internal", "customer_self", "partner", "personal_mailbox", "public_link"),
               "data_class": ("none", "contact_basic", "quasi_identifiers", "financial", "confidential"),
               "scope": SCOPES, "consent": ("granted", "not_granted")},
    "erasure": {**COMMON, "request_verified": (True, False), "hold": ("none", "legal_hold")},
}
HIDEABLE = {
    "scope": ("records_touched", SCOPES),
    "is_duplicate": ("is_duplicate", (False, True)),
    "recipient": ("recipient_affiliation", ("customer_self", "partner", "personal_mailbox")),
    "data_class": ("personal_data", ("none", "contact_basic", "quasi_identifiers", "financial", "confidential")),
    "consent": ("consent_status", ("granted", "not_granted")),
    "hold": ("retention_hold", ("none", "legal_hold")),
    "requester_role": ("requester_role", ("rep", "manager", "ops")),
}


@dataclass(frozen=True)
class Outcome:
    decision: str
    clauses: tuple = ()
    missing: tuple = ()
    source: str = "none"
    question: str = "none"
    alternatives: dict = field(default_factory=dict, compare=False)  # hidden value -> decision, for audits

    def targets(self):
        return {"decision": self.decision, "missing": self.missing[0] if self.missing else "none",
                "source": self.source, "question": self.question}


def _strictest(rules):
    """rules: list of (decision, clause). The strictest certain decision wins; ties keep every clause."""
    top = max(RANK[d] for d, _ in rules)
    return CERTAIN[top], tuple(sorted({c for d, c in rules if RANK[d] == top}))


def _bulk(p, f):
    if f["scope"] == "all":
        return Outcome("BLOCK", ("B4",))
    n = f["scope"]
    if f["verb"] == "update":
        return Outcome(*(_strictest([(p["bulk_update"], "B2")]) if n > p["bulk_n"] else _strictest([(p["single_change"], "B1")])))
    if p["duplicate_exempt"] and f["is_duplicate"]:
        return Outcome("ALLOW_LOG", ("B5",))
    if n > p["bulk_n"]:
        if p["bulk_delete"] == "BLOCK" and p["cleanup_exception"] and f["exception_invoked"]:
            return Outcome("ASK_HUMAN", ("B3", "B6"), question="discretionary_exception")
        return Outcome(p["bulk_delete"], ("B3",))
    return Outcome(*_strictest([(p["single_change"], "B1"), ("ALLOW_LOG", "B1")]))


def _egress_reading(p, f, personal):
    """Decision for one reading of whether quasi-identifiers count as personal data."""
    r, cls, n = f["recipient"], f["data_class"], f["scope"]
    sensitive = cls in ("financial", "confidential")
    has_data = cls != "none"
    if r == "internal":
        if personal and n > p["bulk_n"]:
            return Outcome(p["internal_bulk_personal"], ("E2",))
        return Outcome("ALLOW", ("E1",))
    if r == "customer_self":
        return Outcome("ALLOW_LOG", ("E9",))
    if not has_data:
        return Outcome(p["external_no_data"], ("E3",))
    if r == "personal_mailbox":
        return Outcome("BLOCK", ("E7",))
    if r == "public_link":
        if p["catch_all_external"]:
            return Outcome("REQUIRE_APPROVAL", ("E8",))
        return Outcome("ASK_HUMAN", ("E8",), question="policy_silent")
    # partner organisation
    if sensitive:
        return Outcome(p["external_sensitive"], ("E5",))
    if personal:
        if p["partner_consent"] and f["consent"] == "granted":
            return Outcome("ALLOW_LOG", ("E6",))
        return Outcome(p["external_personal"], ("E4",))
    return Outcome("ALLOW_LOG", ("E3",))


def _egress(p, f):
    cls = f["data_class"]
    if cls != "quasi_identifiers" or p["personal_definition"] == "broad":
        return _egress_reading(p, f, cls in ("contact_basic", "quasi_identifiers"))
    a, b = _egress_reading(p, f, True), _egress_reading(p, f, False)
    if a.decision == b.decision:
        return a
    return Outcome("ASK_HUMAN", ("D1",) + a.clauses, question="interpretation")


def _erasure(p, f):
    if f["hold"] == "legal_hold":
        if not f["request_verified"]:
            return Outcome("BLOCK", ("R2",))
        if p["hold_precedence"]:
            return Outcome("BLOCK", ("R2", "R3"))
        return Outcome("ASK_HUMAN", ("R1", "R2"), question="conflicting_obligations")
    if f["request_verified"]:
        return Outcome("ALLOW_LOG", ("R1",))
    return Outcome(p["unverified_erasure"], ("R4",))


RULES = {"bulk_change": _bulk, "egress": _egress, "erasure": _erasure}


def valid(principle, f):
    """Fact combinations that describe a real action. A link or export with no data, or a data-free message
    with a row count, is not one."""
    if principle == "egress":
        if f["data_class"] == "none" and (f["recipient"] == "public_link" or f["verb"] == "export" or f["scope"] != 1):
            return False
    if principle == "bulk_change" and f["verb"] == "update" and (f["is_duplicate"] or f["exception_invoked"]):
        return False
    return True


def decide(policy, principle, facts):
    """Outcome for fully known facts. Untrusted instructions block everything (U1)."""
    missing = set(FACTS[principle]) - set(facts)
    if missing:
        raise ValueError(f"unknown facts {sorted(missing)}; use resolve()")
    if facts["provenance"] == "content":
        return Outcome("BLOCK", ("U1",))
    return RULES[principle](policy, facts)


def resolve(policy, principle, facts, hidden=()):
    """Outcome when the facts in `hidden` are withheld from the guard (design §4, P8)."""
    if not hidden:
        return decide(policy, principle, facts)
    for h in hidden:
        if h not in HIDEABLE:
            raise ValueError(f"{h} cannot be hidden")
    domains = [HIDEABLE[h][1] for h in hidden]
    outs = {}
    for values in product(*domains):
        g = {**facts, **dict(zip(hidden, values))}
        if valid(principle, g):
            outs[values] = decide(policy, principle, g)
    if not outs:
        raise ValueError("no valid value for the hidden facts")
    decisions = {o.decision for o in outs.values()}
    if len(decisions) == 1:
        o = next(iter(outs.values()))
        return Outcome(o.decision, o.clauses, question=o.question, alternatives={k: v.decision for k, v in outs.items()})
    # Name each hidden fact whose value alone can change the outcome.
    names = []
    for i, h in enumerate(hidden):
        for values in outs:
            for v in domains[i]:
                other = values[:i] + (v,) + values[i + 1:]
                if other in outs and outs[other].decision != outs[values].decision:
                    names.append(HIDEABLE[h][0])
                    break
            if names and names[-1] == HIDEABLE[h][0]:
                break
    names = tuple(dict.fromkeys(names))
    return Outcome("SEEK_CONTEXT", (), missing=names, source=MISSING[names[0]][1],
                   alternatives={k: v.decision for k, v in outs.items()})


def decisive(policy, principle, facts):
    """Facts (and their alternative values) whose change alone changes the decision."""
    base = decide(policy, principle, facts).decision
    out = {}
    for k, dom in FACTS[principle].items():
        alts = [v for v in dom if v != facts[k] and valid(principle, {**facts, k: v})
                and decide(policy, principle, {**facts, k: v}).decision != base]
        if alts:
            out[k] = alts
    return out
