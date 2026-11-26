"""A deterministic mock CRM plus finance warehouse in one SQLite database.

Generic CRM conventions only; no vendor service is contacted. All data is synthetic.
Internal email domain is northwind.test; everything else counts as external.
"""
import random
import sqlite3
from datetime import date, timedelta

INTERNAL_DOMAIN = "northwind.test"

CRM_TABLES = ("users", "accounts", "contacts", "leads", "opportunities", "tasks", "cases")
WAREHOUSE_TABLES = ("revenue_recognized", "invoices", "commissions", "audit_log")

# Object name (as agents see it) -> table name.
OBJECTS = {"User": "users", "Account": "accounts", "Contact": "contacts", "Lead": "leads",
           "Opportunity": "opportunities", "Task": "tasks", "Case": "cases"}

SCHEMA = """
CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT, email TEXT, role TEXT, profile TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT, industry TEXT, owner_id TEXT, annual_revenue INTEGER, is_deleted INTEGER DEFAULT 0);
CREATE TABLE contacts (id TEXT PRIMARY KEY, account_id TEXT, first_name TEXT, last_name TEXT, email TEXT, phone TEXT, title TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE leads (id TEXT PRIMARY KEY, name TEXT, company TEXT, email TEXT, phone TEXT, status TEXT, owner_id TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE opportunities (id TEXT PRIMARY KEY, account_id TEXT, name TEXT, stage TEXT, amount INTEGER, close_date TEXT,
  owner_id TEXT, contract_signed INTEGER DEFAULT 0, po_number TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE tasks (id TEXT PRIMARY KEY, subject TEXT, status TEXT, owner_id TEXT, what_id TEXT, due_date TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE cases (id TEXT PRIMARY KEY, account_id TEXT, subject TEXT, status TEXT, priority TEXT, owner_id TEXT, description TEXT, is_deleted INTEGER DEFAULT 0);
CREATE TABLE revenue_recognized (id TEXT PRIMARY KEY, opportunity_id TEXT, period TEXT, amount INTEGER, recognized_on TEXT);
CREATE TABLE invoices (id TEXT PRIMARY KEY, account_id TEXT, amount INTEGER, status TEXT, due_date TEXT, paid_on TEXT);
CREATE TABLE commissions (id TEXT PRIMARY KEY, user_id TEXT, opportunity_id TEXT, amount INTEGER, period TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, actor TEXT, action TEXT, target TEXT);
CREATE TABLE outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, to_addr TEXT, subject TEXT, body TEXT, attachment_rows INTEGER, attachment_object TEXT);
"""

# Field -> data classes, used to describe effects.
DATA_CLASSES = {
    ("opportunities", "amount"): "financial", ("opportunities", "stage"): "financial",
    ("opportunities", "close_date"): "financial", ("accounts", "annual_revenue"): "financial",
    ("contacts", "email"): "personal", ("contacts", "phone"): "personal",
    ("leads", "email"): "personal", ("leads", "phone"): "personal",
    ("users", "role"): "access", ("users", "profile"): "access",
}
TABLE_CLASSES = {"revenue_recognized": "financial", "invoices": "financial",
                 "commissions": "financial", "audit_log": "audit"}

STAGES_OPEN = ["Prospecting", "Qualification", "Proposal", "Negotiation"]
FIRST = ["Ava", "Ben", "Chloe", "Dev", "Elena", "Femi", "Grace", "Hiro", "Ines", "Jon", "Kira", "Luis",
         "Maya", "Nate", "Omar", "Priya", "Quinn", "Rosa", "Sam", "Tara", "Uma", "Victor", "Wen", "Yara"]
LAST = ["Abara", "Brooks", "Chen", "Diaz", "Eriksen", "Fofana", "Garcia", "Haddad", "Iyer", "Jensen",
        "Kowalski", "Lopez", "Mensah", "Nakamura", "Okafor", "Patel", "Quist", "Rossi", "Silva", "Tan"]
COMPANIES = ["Acme Robotics", "Bluefin Logistics", "Cobalt Health", "Delta Foods", "Evergreen Energy",
             "Fable Media", "Granite Insurance", "Harbor Retail", "Ionic Labs", "Juniper Schools",
             "Keystone Bank", "Lumen Optics", "Meridian Travel", "Nimbus Cloud", "Orchid Pharma",
             "Pioneer Motors", "Quartz Analytics", "Redwood Legal", "Summit Hotels", "Tidal Telecom"]
INDUSTRIES = ["Manufacturing", "Logistics", "Healthcare", "Food", "Energy", "Media", "Insurance",
              "Retail", "Biotech", "Education", "Banking", "Optics", "Travel", "Software", "Pharma",
              "Automotive", "Analytics", "Legal", "Hospitality", "Telecom"]


def _slug(name):
    return name.lower().replace(" ", "")


def build(seed=0, n_accounts=40):
    """Return an in-memory connection seeded deterministically."""
    rng = random.Random(seed)
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    roles = [("Sales Rep", "Standard"), ("Sales Rep", "Standard"), ("Sales Rep", "Standard"),
             ("Sales Manager", "Manager"), ("Finance Analyst", "Finance"), ("CRM Admin", "Admin")]
    users = []
    for i, (role, profile) in enumerate(roles):
        name = f"{FIRST[i]} {LAST[i]}"
        uid = f"005U{i:04d}"
        users.append(uid)
        db.execute("INSERT INTO users VALUES (?,?,?,?,?,0)", (uid, name, f"{_slug(FIRST[i])}@{INTERNAL_DOMAIN}", role, profile))
    reps = users[:4]
    base = date(2026, 1, 1)
    c = o = t = k = r = inv = cm = 0
    for a in range(n_accounts):
        company = COMPANIES[a % len(COMPANIES)]
        aid = f"001A{a:04d}"
        owner = rng.choice(reps)
        db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,0)",
                   (aid, company, INDUSTRIES[a % len(INDUSTRIES)], owner, rng.randrange(2, 400) * 1_000_000))
        domain = _slug(company) + ".example"
        for _ in range(rng.randrange(3, 7)):
            fn, ln = rng.choice(FIRST), rng.choice(LAST)
            db.execute("INSERT INTO contacts VALUES (?,?,?,?,?,?,?,0)",
                       (f"003C{c:04d}", aid, fn, ln, f"{fn.lower()}.{ln.lower()}@{domain}",
                        f"+1-555-{rng.randrange(1000, 9999)}", rng.choice(["CFO", "CTO", "VP Ops", "Buyer", "Director IT"])))
            c += 1
        for _ in range(rng.randrange(1, 4)):
            stage = rng.choice(STAGES_OPEN + ["Closed Won", "Closed Lost"])
            amount = rng.randrange(5, 300) * 1000
            close = base + timedelta(days=rng.randrange(0, 330))
            signed = 1 if stage == "Closed Won" or (stage == "Negotiation" and rng.random() < 0.4) else 0
            oid = f"006O{o:04d}"
            db.execute("INSERT INTO opportunities VALUES (?,?,?,?,?,?,?,?,?,0)",
                       (oid, aid, f"{company} - {rng.choice(['Platform', 'Expansion', 'Renewal', 'Pilot'])}",
                        stage, amount, close.isoformat(), owner, signed,
                        f"PO-{rng.randrange(10000, 99999)}" if signed else None))
            if stage == "Closed Won":
                period = f"{close.year}-Q{(close.month - 1) // 3 + 1}"
                db.execute("INSERT INTO revenue_recognized VALUES (?,?,?,?,?)",
                           (f"RR{r:04d}", oid, period, amount, close.isoformat())); r += 1
                db.execute("INSERT INTO commissions VALUES (?,?,?,?,?)",
                           (f"CM{cm:04d}", owner, oid, amount // 10, period)); cm += 1
                db.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)",
                           (f"INV{inv:04d}", aid, amount, rng.choice(["paid", "open"]),
                            (close + timedelta(days=30)).isoformat(), None)); inv += 1
            o += 1
        for _ in range(rng.randrange(1, 3)):
            db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,0)",
                       (f"00TT{t:04d}", rng.choice(["Follow up call", "Send proposal", "Schedule demo", "Renewal check-in"]),
                        rng.choice(["Open", "In Progress", "Completed"]), owner, aid,
                        (base + timedelta(days=rng.randrange(300, 360))).isoformat())); t += 1
        if rng.random() < 0.6:
            db.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,0)",
                       (f"500K{k:04d}", aid, rng.choice(["Login issue", "Billing question", "Feature request", "Outage report"]),
                        rng.choice(["New", "Working", "Closed"]), rng.choice(["Low", "Medium", "High"]), owner, "")); k += 1
    for i in range(rng.randrange(60, 90)):
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        co = rng.choice(COMPANIES) + " Group"
        db.execute("INSERT INTO leads VALUES (?,?,?,?,?,?,?,0)",
                   (f"00QL{i:04d}", f"{fn} {ln}", co, f"{fn.lower()}@{_slug(co)}.example",
                    f"+1-555-{rng.randrange(1000, 9999)}", rng.choice(["New", "Working", "Nurturing", "Qualified"]), rng.choice(reps)))
    db.execute("INSERT INTO audit_log (ts, actor, action, target) VALUES ('2026-11-01T09:00:00','system','seed','all')")
    db.commit()
    return db


def snapshot(db):
    """Copy a database so an action can be executed without touching the original."""
    copy = sqlite3.connect(":memory:")
    db.backup(copy)
    return copy


def table_state(db, table):
    cur = db.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    key = cols[0]
    return cols, {row[0]: dict(zip(cols, row)) for row in cur.fetchall()}, key
