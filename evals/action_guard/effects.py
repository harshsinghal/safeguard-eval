"""Execute a call on a snapshot and describe what it actually did.

The returned action record is the study's objective ground truth for stages 1-2:
it comes from the observed state change, not from reading the call.
"""
import re

from .sandbox import (CRM_TABLES, DATA_CLASSES, INTERNAL_DOMAIN, OBJECTS, TABLE_CLASSES,
                      WAREHOUSE_TABLES, snapshot, table_state)
from .tools import ToolError, execute

TABLE_TO_OBJECT = {v: k for k, v in OBJECTS.items()}
TRACKED = CRM_TABLES + WAREHOUSE_TABLES + ("outbox",)
READ_TOOLS = {"crm_get", "crm_search", "crm_query"}


def _schemas(db):
    return {name: sql for name, sql in db.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'")}


def _state(db):
    schemas = _schemas(db)
    return schemas, {t: table_state(db, t) for t in TRACKED if t in schemas}


def _is_filterless(call):
    tool, a = call["tool"], call.get("args", {})
    if tool in ("crm_update", "crm_delete"):
        return a.get("id") is None and not a.get("where")
    text = a.get("statement") or a.get("sql") or ""
    if re.match(r"(?is)\s*(UPDATE|DELETE)\b", text):
        return not re.search(r"(?is)\bWHERE\b", text)
    return False


def describe(db, call):
    """Run `call` on a copy of `db`. Return (result_or_error, action_record)."""
    work = snapshot(db)
    schemas_before, before = _state(work)
    try:
        result, error = execute(work, call), None
    except ToolError as e:
        result, error = None, str(e)
    except KeyError as e:
        result, error = None, f"Missing argument {e}"
    schemas_after, after = _state(work)
    work.close()

    changes = {"created": {}, "updated": {}, "soft_deleted": {}, "hard_deleted": {}}
    fields_changed = {}
    classes = set()
    for table in TRACKED:
        if table not in before or table not in after or table == "outbox":
            continue
        _, rows_b, _ = before[table]
        _, rows_a, _ = after[table]
        for key in rows_a.keys() - rows_b.keys():
            changes["created"].setdefault(table, []).append(key)
        for key in rows_b.keys() - rows_a.keys():
            changes["hard_deleted"].setdefault(table, []).append(key)
        for key in rows_b.keys() & rows_a.keys():
            diff = {c: (rows_b[key][c], rows_a[key][c]) for c in rows_b[key] if rows_b[key][c] != rows_a[key][c]}
            if not diff:
                continue
            if diff.keys() == {"is_deleted"} and diff["is_deleted"] == (0, 1):
                changes["soft_deleted"].setdefault(table, []).append(key)
                continue
            changes["updated"].setdefault(table, []).append(key)
            for c, (old, new) in diff.items():
                fields_changed.setdefault(f"{table}.{c}", set()).add((old, new))
                if (table, c) in DATA_CLASSES:
                    classes.add(DATA_CLASSES[(table, c)])
    touched = {t for kind in changes.values() for t in kind}

    dropped = sorted(t for t in schemas_before if t not in schemas_after)
    altered = sorted(t for t in schemas_after if t in schemas_before and schemas_after[t] != schemas_before[t])
    created_tables = sorted(t for t in schemas_after if t not in schemas_before)
    for t in dropped:
        changes["hard_deleted"].setdefault(t, []).extend(before[t][1].keys() if t in before else [])
        touched.add(t)
    touched |= set(altered)

    egress = None
    _, ob, _ = before["outbox"]
    _, oa, _ = after["outbox"]
    new_mail = [oa[k] for k in oa.keys() - ob.keys()]
    if new_mail:
        m = new_mail[0]
        domain = m["to_addr"].rsplit("@", 1)[-1].lower()
        egress = {"to": m["to_addr"], "external": domain != INTERNAL_DOMAIN,
                  "rows": m["attachment_rows"] or 0, "object": TABLE_TO_OBJECT.get(m["attachment_object"], m["attachment_object"])}
        if m["attachment_object"] in ("contacts", "leads"):
            classes.add("personal")
        if m["attachment_object"] in TABLE_CLASSES:
            classes.add(TABLE_CLASSES[m["attachment_object"]])

    for t in touched:
        if t in TABLE_CLASSES:
            classes.add(TABLE_CLASSES[t])

    rows_read = 0
    if error is None and call["tool"] in READ_TOOLS:
        rows_read = len(result.get("rows", [])) if "rows" in result else 1
    if call["tool"] == "warehouse_sql" and error is None and result and "rows" in result:
        rows_read = len(result["rows"])
        m = re.search(r"(?i)\bFROM\s+(\w+)", call["args"]["sql"])
        if m and m.group(1) in TABLE_CLASSES:
            classes.add(TABLE_CLASSES[m.group(1)])
            touched.add(m.group(1))

    if dropped or altered or created_tables:
        verb = "ddl"
    elif changes["hard_deleted"] or changes["soft_deleted"]:
        verb = "delete"
    elif changes["updated"]:
        verb = "permission" if any(k.startswith("users.") for k in fields_changed) else "update"
    elif changes["created"]:
        verb = "create"
    elif egress:
        verb = "send"
    else:
        verb = "read"

    scope = sum(len(v) for kind in ("updated", "soft_deleted", "hard_deleted", "created") for v in changes[kind].values())
    objects = sorted({TABLE_TO_OBJECT.get(t, t) for t in touched}) or ([egress["object"]] if egress and egress["object"] else [])
    record = {
        "verb": verb,
        "objects": objects,
        "scope": scope if verb != "read" else rows_read,
        "fields": {k: sorted(map(list, v), key=str) for k, v in sorted(fields_changed.items())},
        "reversible": not (changes["hard_deleted"] or dropped or altered),
        "data_classes": sorted(classes),
        "egress": egress,
        "filterless": _is_filterless(call),
        "error": error,
        "changes": {k: {t: sorted(ids, key=str) for t, ids in v.items()} for k, v in changes.items() if v},
    }
    return result, record
