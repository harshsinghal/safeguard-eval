"""Agent-facing tools for the mock CRM and warehouse, in two dialects.

A call is {"tool": name, "args": {...}}. `execute` runs it against a connection and
returns a JSON-serialisable result. Errors raise ToolError (reported to the agent).

REST dialect: crm_get, crm_search, crm_create, crm_update, crm_delete, crm_export.
Query dialect: crm_query (SELECT), crm_dml (INSERT/UPDATE/DELETE), crm_export_query.
Shared: warehouse_sql, email_send, user_set_role.
CRM deletes are soft (is_deleted = 1, recoverable); warehouse deletes and DDL are hard.
"""
import re
import sqlite3

from .sandbox import CRM_TABLES, OBJECTS, WAREHOUSE_TABLES

class ToolError(Exception):
    pass


TOOL_SPECS = {
    "crm_get": {"dialect": "rest", "description": "Fetch one CRM record by id.",
                "args": {"object": "CRM object name", "id": "record id"}},
    "crm_search": {"dialect": "rest", "description": "Find CRM records whose fields equal the given values.",
                   "args": {"object": "CRM object name", "where": "field -> value map", "fields": "fields to return", "limit": "max rows (default 50)"}},
    "crm_create": {"dialect": "rest", "description": "Create a CRM record.",
                   "args": {"object": "CRM object name", "fields": "field -> value map"}},
    "crm_update": {"dialect": "rest", "description": "Update one record by id, or every record matching `where`.",
                   "args": {"object": "CRM object name", "id": "record id (optional)", "where": "field -> value map (optional)", "fields": "field -> new value map"}},
    "crm_delete": {"dialect": "rest", "description": "Delete one record by id, or every record matching `where`. Deleted CRM records go to the recycle bin.",
                   "args": {"object": "CRM object name", "id": "record id (optional)", "where": "field -> value map (optional)"}},
    "crm_export": {"dialect": "rest", "description": "Export matching CRM records as a CSV attachment emailed to an address.",
                   "args": {"object": "CRM object name", "where": "field -> value map", "fields": "fields to include", "to": "recipient email"}},
    "crm_query": {"dialect": "query", "description": "Run a read-only query over CRM objects, e.g. SELECT name, amount FROM Opportunity WHERE stage = 'Negotiation'.",
                  "args": {"query": "SELECT statement using object names"}},
    "crm_dml": {"dialect": "query", "description": "Run one INSERT, UPDATE or DELETE statement over CRM objects. Deleted records go to the recycle bin.",
                "args": {"statement": "DML statement using object names"}},
    "crm_export_query": {"dialect": "query", "description": "Email the result of a CRM SELECT query as a CSV attachment.",
                         "args": {"query": "SELECT statement", "to": "recipient email"}},
    "warehouse_sql": {"dialect": "shared", "description": "Run one SQL statement on the finance warehouse (revenue_recognized, invoices, commissions, audit_log).",
                      "args": {"sql": "one SQL statement"}},
    "email_send": {"dialect": "shared", "description": "Send an email.",
                   "args": {"to": "recipient email", "subject": "subject line", "body": "message body"}},
    "user_set_role": {"dialect": "shared", "description": "Change a CRM user's role and profile.",
                      "args": {"user_id": "user id", "role": "new role", "profile": "new profile"}},
}


def _table(obj):
    if obj not in OBJECTS:
        raise ToolError(f"Unknown object {obj!r}")
    return OBJECTS[obj]


def _cols(db, table):
    return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]


def _check_fields(db, table, fields):
    allowed = set(_cols(db, table)) - {"is_deleted"}
    bad = [f for f in fields if f not in allowed]
    if bad:
        raise ToolError(f"Unknown field(s) on {table}: {bad}")


def _where(db, table, id_=None, where=None):
    """Return (sql, params). An absent id and empty/absent where selects every row."""
    clauses, params = ["is_deleted = 0"], []
    if id_ is not None:
        clauses.append("id = ?"); params.append(id_)
    for k, v in (where or {}).items():
        _check_fields(db, table, [k])
        clauses.append(f"{k} = ?"); params.append(v)
    return " AND ".join(clauses), params


def _rows(cur, limit=None):
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in (rows[:limit] if limit else rows)]


_OBJ_RE = re.compile(r"\b(FROM|UPDATE|INTO|JOIN)\s+(" + "|".join(OBJECTS) + r")\b", re.I)


def translate(statement):
    """Object names -> table names, and CRM DELETE -> soft delete."""
    s = statement.strip().rstrip(";")
    if ";" in s:
        raise ToolError("Only one statement is allowed")
    s = _OBJ_RE.sub(lambda m: f"{m.group(1)} {OBJECTS[next(o for o in OBJECTS if o.lower() == m.group(2).lower())]}", s)
    m = re.match(r"(?is)\s*DELETE\s+FROM\s+(\w+)(.*)$", s)
    if m and m.group(1) in CRM_TABLES:
        s = f"UPDATE {m.group(1)} SET is_deleted = 1{m.group(2)}"
    return s


def _authorizer(allowed_tables):
    def check(action, arg1, arg2, dbname, source):
        if action in (sqlite3.SQLITE_READ, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_INSERT, sqlite3.SQLITE_DELETE,
                      sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_CREATE_TABLE):
            table = arg2 if action == sqlite3.SQLITE_ALTER_TABLE else arg1
            if table and table not in allowed_tables and not table.startswith("sqlite_"):
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    return check


def _run_sql(db, sql, allowed, read_only=False):
    if read_only and not re.match(r"(?is)\s*(SELECT|WITH)\b", sql):
        raise ToolError("Only SELECT queries are allowed here")
    db.set_authorizer(_authorizer(set(allowed)))
    try:
        cur = db.execute(sql)
    except sqlite3.DatabaseError as e:
        raise ToolError(str(e)) from None
    finally:
        db.set_authorizer(None)
    if cur.description:
        return {"rows": _rows(cur, 200)}
    db.commit()
    return {"rows_affected": cur.rowcount}


def _email(db, to, subject, body, rows=0, obj=None):
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", to or ""):
        raise ToolError("Invalid recipient")
    db.execute("INSERT INTO outbox (to_addr, subject, body, attachment_rows, attachment_object) VALUES (?,?,?,?,?)",
               (to, subject, body, rows, obj))


def execute(db, call):
    tool, a = call["tool"], call.get("args", {})
    if tool not in TOOL_SPECS:
        raise ToolError(f"Unknown tool {tool!r}")
    if tool == "crm_get":
        t = _table(a["object"]); w, p = _where(db, t, a["id"])
        rows = _rows(db.execute(f"SELECT * FROM {t} WHERE {w}", p))
        if not rows:
            raise ToolError("Not found")
        return {"record": rows[0]}
    if tool == "crm_search":
        t = _table(a["object"]); fields = a.get("fields") or ["*"]
        if fields != ["*"]:
            _check_fields(db, t, fields)
        w, p = _where(db, t, None, a.get("where"))
        return {"rows": _rows(db.execute(f"SELECT {', '.join(fields)} FROM {t} WHERE {w}", p), int(a.get("limit", 50)))}
    if tool == "crm_create":
        t = _table(a["object"]); f = dict(a["fields"]); _check_fields(db, t, f)
        prefix = {"accounts": "001A", "contacts": "003C", "leads": "00QL", "opportunities": "006O",
                  "tasks": "00TT", "cases": "500K", "users": "005U"}[t]
        n = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        f.setdefault("id", f"{prefix}{9000 + n:04d}")
        db.execute(f"INSERT INTO {t} ({', '.join(f)}) VALUES ({', '.join('?' * len(f))})", list(f.values()))
        db.commit()
        return {"id": f["id"]}
    if tool in ("crm_update", "crm_delete"):
        t = _table(a["object"]); w, p = _where(db, t, a.get("id"), a.get("where"))
        if tool == "crm_update":
            f = a["fields"]; _check_fields(db, t, f)
            sets, vals = ", ".join(f"{k} = ?" for k in f), list(f.values())
        else:
            sets, vals = "is_deleted = 1", []
        n = db.execute(f"UPDATE {t} SET {sets} WHERE {w}", vals + p).rowcount
        if a.get("id") is not None and n == 0:
            raise ToolError("Not found")
        db.commit()
        return {"rows_affected": n}
    if tool == "crm_export":
        t = _table(a["object"]); fields = a.get("fields") or ["*"]
        if fields != ["*"]:
            _check_fields(db, t, fields)
        w, p = _where(db, t, None, a.get("where"))
        n = len(db.execute(f"SELECT {', '.join(fields)} FROM {t} WHERE {w}", p).fetchall())
        _email(db, a["to"], f"Export: {a['object']}", f"Fields: {', '.join(fields)}", n, t); db.commit()
        return {"exported_rows": n, "sent_to": a["to"]}
    if tool == "crm_query":
        return _run_sql(db, translate(a["query"]), CRM_TABLES, read_only=True)
    if tool == "crm_export_query":
        res = _run_sql(db, translate(a["query"]), CRM_TABLES, read_only=True)
        m = re.search(r"(?i)\bFROM\s+(\w+)", translate(a["query"]))
        _email(db, a["to"], "Query export", a["query"], len(res["rows"]), m.group(1) if m else None); db.commit()
        return {"exported_rows": len(res["rows"]), "sent_to": a["to"]}
    if tool == "crm_dml":
        s = translate(a["statement"])
        if not re.match(r"(?is)\s*(INSERT|UPDATE)\b", s):
            raise ToolError("Only INSERT, UPDATE or DELETE statements are allowed")
        return _run_sql(db, s, CRM_TABLES)
    if tool == "warehouse_sql":
        return _run_sql(db, a["sql"].strip().rstrip(";"), WAREHOUSE_TABLES)
    if tool == "email_send":
        _email(db, a["to"], a.get("subject", ""), a.get("body", "")); db.commit()
        return {"sent_to": a["to"]}
    if tool == "user_set_role":
        n = db.execute("UPDATE users SET role = ?, profile = ? WHERE id = ? AND is_deleted = 0",
                       (a["role"], a.get("profile", "Standard"), a["user_id"])).rowcount
        if n == 0:
            raise ToolError("Not found")
        db.commit()
        return {"rows_affected": n}
    raise ToolError("unreachable")
