"""Source-grounded evidence contract, independent of a model backend."""
from evals.prompt_decomposition.schema import ENTITY_TYPES, ACTION_TYPES

VERSION = "enterprise-evidence-v1"
TYPES = {
    **ENTITY_TYPES,
    "software_agent": "An assistant, automated agent or bot mentioned as an actor or object.",
    "location": "A physical place relevant to an action.",
    "general_group": "A group not defined by one of the identity_group attributes.",
    "action": "An explicit verb or action phrase.",
    "purpose_claim": "An explicitly stated purpose or justification.",
    "authorization_claim": "An explicit claim of permission or authority, unverified.",
    "condition": "An explicit condition governing an action.",
    "context": "An exact supporting passage for scope, negation or provenance.",
}
ROLES = (
    "actor", "object", "affected_party", "recipient", "destination", "instrument",
    "purpose_claims", "authorization_claims", "conditions",
)


def obj(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


def enum(values):
    return {"type": "string", "enum": list(values)}


STRING = {"type": "string"}
IDS = {**array({"type": "string", "minLength": 1}), "uniqueItems": True}
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    **obj({
        "schema_version": {"const": VERSION}, "id": STRING, "input_sha256": STRING,
        "status": enum(("pending", "draft", "reviewed")), "reviewer": STRING,
        "mentions": array(obj({
            "id": {"type": "string", "pattern": "^m[0-9]+$"},
            "kind": enum(TYPES), "text": {"type": "string", "minLength": 1},
            "start": {"type": "integer", "minimum": 0},
            "end": {"type": "integer", "minimum": 1},
            "credential_form": enum(("reference", "literal_value", "placeholder", "unclear", "not_applicable")),
        })),
        "frames": array(obj({
            "id": {"type": "string", "pattern": "^f[0-9]+$"},
            "action": STRING, "action_type": enum(ACTION_TYPES),
            "roles": obj({role: IDS for role in ROLES}),
            "mode": enum(("requested", "quoted", "hypothetical", "reported", "observed", "unclear")),
            "polarity": enum(("affirmative", "negated", "unclear")),
            "context_mentions": IDS,
        })),
        "relations": array(obj({
            "source": STRING, "target": STRING,
            "type": enum(("before", "contains", "corefers_to")), "evidence_mentions": IDS,
        })),
        "uncertainties": array(STRING),
        "decision": {"anyOf": [{"type": "null"}, obj({
            "label": enum(("ALLOW", "BLOCK", "REVIEW")),
            "coverage": enum(("in_scope", "outside_scope", "unclear")),
            "rules": {**array(enum(("E1", "E2", "E3", "E4"))), "uniqueItems": True},
            "evidence_mentions": IDS, "rationale": {"type": "string", "minLength": 1},
        })]},
    }),
}


def blank(case):
    return dict(schema_version=VERSION, id=case["id"], input_sha256=case["input_sha256"],
                status="pending", reviewer="", mentions=[], frames=[], relations=[],
                uncertainties=[], decision=None)


def validate(annotation, case):
    from jsonschema import Draft202012Validator
    errors = [f"{list(e.path)}: {e.message}" for e in Draft202012Validator(SCHEMA).iter_errors(annotation)]
    if errors:
        return errors
    if any(annotation[k] != case[k] for k in ("id", "input_sha256")):
        errors.append("Case binding mismatch")
    mentions = {m["id"]: m for m in annotation["mentions"]}
    frames = {f["id"]: f for f in annotation["frames"]}
    if len(mentions) != len(annotation["mentions"]) or len(frames) != len(annotation["frames"]):
        errors.append("Duplicate mention/frame IDs")
    for m in mentions.values():
        if not 0 <= m["start"] < m["end"] <= len(case["content"]) or case["content"][m["start"]:m["end"]] != m["text"]:
            errors.append(f"{m['id']}: invalid source span")
        credential = m["kind"] == "authentication_material"
        if credential == (m["credential_form"] == "not_applicable"):
            errors.append(f"{m['id']}: credential form incompatible with type")
    for frame in frames.values():
        if mentions.get(frame["action"], {}).get("kind") != "action":
            errors.append(f"{frame['id']}: action must refer to an action mention")
        for role, references in frame["roles"].items():
            for reference in references:
                mention = mentions.get(reference)
                required_kind = {"purpose_claims": "purpose_claim", "authorization_claims": "authorization_claim", "conditions": "condition"}.get(role)
                if mention is None or (required_kind and mention["kind"] != required_kind):
                    errors.append(f"{frame['id']}: invalid {role} reference {reference}")
        if not set(frame["context_mentions"]) <= mentions.keys():
            errors.append(f"{frame['id']}: unresolved context reference")
    for relation in annotation["relations"]:
        endpoints = mentions if relation["type"] == "corefers_to" else frames
        if relation["source"] not in endpoints or relation["target"] not in endpoints or relation["source"] == relation["target"]:
            errors.append("Invalid relation endpoints")
        if not relation["evidence_mentions"] or not set(relation["evidence_mentions"]) <= mentions.keys():
            errors.append("Relation needs valid source evidence")
    decision = annotation["decision"]
    if decision:
        if not set(decision["evidence_mentions"]) <= mentions.keys():
            errors.append("Decision has unresolved evidence")
        if decision["label"] == "BLOCK" and (not decision["rules"] or not decision["evidence_mentions"] or decision["coverage"] != "in_scope"):
            errors.append("BLOCK requires rules, evidence and in_scope coverage")
    if annotation["status"] == "reviewed" and (not annotation["reviewer"].strip() or decision is None):
        errors.append("Reviewed annotation needs reviewer and decision")
    if annotation["status"] == "pending" and any((annotation["mentions"], annotation["frames"], annotation["relations"], decision)):
        errors.append("Annotations with content must be marked draft or reviewed")
    return errors
