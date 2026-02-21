import requests
import json

BASE = "http://localhost:8000/api"
passed = 0
failed = 0
skipped = 0

def check(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✅ {label}")
        passed += 1
    else:
        print(f"  ❌ {label}{f' → {detail}' if detail else ''}")
        failed += 1

def skip(label, reason=""):
    global skipped
    print(f"  ⏭️  {label} (skipped: {reason})")
    skipped += 1

def section(title):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")

# ── DETECT LLM STATUS ─────────────────────────────────────────────────────────
r = requests.post(f"{BASE}/tickets/classify/", json={"description": "my credit card was charged twice this month"})
llm_active = r.status_code == 200 and r.json().get("suggested_category") != "general"
print(f"\n{'='*50}")
print(f"  Support Ticket System — Full Test Suite")
print(f"  LLM Status: {'🟢 ACTIVE' if llm_active else '🔴 INACTIVE (fallback mode)'}")
print(f"{'='*50}")

# ── 1. TICKET CREATION ────────────────────────────────────────────────────────
section("1. Ticket Creation")

tickets = [
    {"title": "Cannot login to account",      "description": "Getting 403 forbidden on every login attempt since yesterday", "category": "account",   "priority": "high"},
    {"title": "Double charged on invoice",    "description": "My credit card was billed twice for the same subscription",    "category": "billing",   "priority": "critical"},
    {"title": "Export button crashes app",    "description": "Clicking export PDF causes the entire dashboard to crash",     "category": "technical", "priority": "high"},
    {"title": "How do I change my username",  "description": "I want to update my display name in my profile settings",      "category": "account",   "priority": "low"},
    {"title": "API response very slow",       "description": "The REST API is taking 30+ seconds to respond to requests",    "category": "technical", "priority": "medium"},
]

created_ids = []
for t in tickets:
    r = requests.post(f"{BASE}/tickets/", json=t)
    check(f"POST '{t['title'][:35]}...' → 201", r.status_code == 201)
    if r.status_code == 201:
        created_ids.append(r.json()["id"])

# ── 2. VALIDATION ─────────────────────────────────────────────────────────────
section("2. Input Validation")

cases = [
    ({"title": "",        "description": "desc"},                      "empty title → 400"),
    ({"title": "   ",     "description": "desc"},                      "whitespace title → 400"),
    ({"title": "Title"},                                                "missing description → 400"),
    ({"title": "T",       "description": "D", "category": "wrong"},    "invalid category → 400"),
    ({"title": "T",       "description": "D", "priority": "urgent"},   "invalid priority → 400"),
    ({"title": "T",       "description": "D", "status": "pending"},    "invalid status → 400"),
    ({"title": "x"*201,   "description": "D"},                         "title >200 chars → 400"),
]
for payload, label in cases:
    r = requests.post(f"{BASE}/tickets/", json=payload)
    check(label, r.status_code == 400)

# ── 3. LISTING & ORDERING ─────────────────────────────────────────────────────
section("3. Listing & Ordering")

r = requests.get(f"{BASE}/tickets/")
check("GET /tickets/ → 200", r.status_code == 200)
data = r.json()
check(f"Returns {len(tickets)} tickets", len(data) >= len(tickets), f"got {len(data)}")
if len(data) >= 2:
    check("Newest first (descending created_at)", data[0]["id"] > data[1]["id"])

# ── 4. FILTERS ────────────────────────────────────────────────────────────────
section("4. Filters & Search")

r = requests.get(f"{BASE}/tickets/", params={"category": "technical"})
check("?category=technical", r.status_code == 200 and all(t["category"] == "technical" for t in r.json()))

r = requests.get(f"{BASE}/tickets/", params={"priority": "critical"})
check("?priority=critical", r.status_code == 200 and all(t["priority"] == "critical" for t in r.json()))

r = requests.get(f"{BASE}/tickets/", params={"status": "open"})
check("?status=open", r.status_code == 200 and all(t["status"] == "open" for t in r.json()))

r = requests.get(f"{BASE}/tickets/", params={"search": "login"})
check("?search=login finds ticket", r.status_code == 200 and len(r.json()) >= 1)

r = requests.get(f"{BASE}/tickets/", params={"search": "charged"})
check("?search=charged finds ticket", r.status_code == 200 and len(r.json()) >= 1)

r = requests.get(f"{BASE}/tickets/", params={"category": "technical", "priority": "high"})
check("?category=technical&priority=high combined", r.status_code == 200)

r = requests.get(f"{BASE}/tickets/", params={"category": "billing", "status": "open"})
check("?category=billing&status=open combined", r.status_code == 200)

r = requests.get(f"{BASE}/tickets/", params={"search": "xyznonexistent"})
check("?search=nonexistent → empty list", r.status_code == 200 and r.json() == [])

# ── 5. STATUS TRANSITIONS ─────────────────────────────────────────────────────
section("5. Status Transitions (PATCH)")

if created_ids:
    tid = created_ids[0]
    for status in ["in_progress", "resolved", "closed", "open"]:
        r = requests.patch(f"{BASE}/tickets/{tid}/", json={"status": status})
        check(f"PATCH #{tid} → {status}", r.status_code == 200 and r.json()["status"] == status)

    # Override category and priority
    r = requests.patch(f"{BASE}/tickets/{tid}/", json={"category": "billing", "priority": "critical"})
    check("PATCH override category + priority", r.status_code == 200 and r.json()["category"] == "billing")

# ── 6. STATS ──────────────────────────────────────────────────────────────────
section("6. Stats Endpoint")

r = requests.get(f"{BASE}/tickets/stats/")
check("GET /tickets/stats/ → 200", r.status_code == 200)
if r.status_code == 200:
    s = r.json()
    required_keys = ["total_tickets", "open_tickets", "avg_tickets_per_day", "priority_breakdown", "category_breakdown"]
    check("All required keys present", all(k in s for k in required_keys))
    check("priority_breakdown has low/medium/high/critical", all(k in s["priority_breakdown"] for k in ["low","medium","high","critical"]))
    check("category_breakdown has billing/technical/account/general", all(k in s["category_breakdown"] for k in ["billing","technical","account","general"]))
    check("open_tickets <= total_tickets", s["open_tickets"] <= s["total_tickets"])
    check("avg_tickets_per_day > 0", s["avg_tickets_per_day"] > 0)
    priority_sum = sum(s["priority_breakdown"].values())
    check("priority counts sum to total_tickets", priority_sum == s["total_tickets"], f"{priority_sum} != {s['total_tickets']}")
    category_sum = sum(s["category_breakdown"].values())
    check("category counts sum to total_tickets", category_sum == s["total_tickets"], f"{category_sum} != {s['total_tickets']}")
    print(f"\n  📊 total={s['total_tickets']} | open={s['open_tickets']} | avg/day={s['avg_tickets_per_day']}")
    print(f"  📊 priority={s['priority_breakdown']}")
    print(f"  📊 category={s['category_breakdown']}")

# ── 7. LLM CLASSIFY ───────────────────────────────────────────────────────────
section("7. LLM Classification")

classify_cases = [
    ("billing",   "My credit card was charged twice and I need a refund immediately"),
    ("technical", "The application crashes every time I click the export button"),
    ("account",   "I cannot reset my password, the email link expired"),
    ("general",   "I have a question about how to use the dashboard"),
]

for expected_cat, desc in classify_cases:
    r = requests.post(f"{BASE}/tickets/classify/", json={"description": desc})
    check(f"classify → 200 for '{expected_cat}' description", r.status_code == 200)
    if r.status_code == 200:
        d = r.json()
        check("has suggested_category + suggested_priority", "suggested_category" in d and "suggested_priority" in d)
        check("category is valid choice", d.get("suggested_category") in {"billing","technical","account","general"})
        check("priority is valid choice", d.get("suggested_priority") in {"low","medium","high","critical"})
        if llm_active:
            check(f"AI correctly guessed '{expected_cat}'", d["suggested_category"] == expected_cat, f"got '{d['suggested_category']}'")
        else:
            skip(f"AI accuracy for '{expected_cat}'", "GROQ_API_KEY not active")
        print(f"  → {d.get('suggested_category')} / {d.get('suggested_priority')}")

# Validation
r = requests.post(f"{BASE}/tickets/classify/", json={"description": "short"})
check("classify too short → 400", r.status_code == 400)

r = requests.post(f"{BASE}/tickets/classify/", json={})
check("classify missing field → 400", r.status_code == 400)

# ── 8. EDGE CASES ─────────────────────────────────────────────────────────────
section("8. Edge Cases")

r = requests.get(f"{BASE}/tickets/99999/")
check("GET non-existent → 404", r.status_code == 404)

r = requests.patch(f"{BASE}/tickets/99999/", json={"status": "open"})
check("PATCH non-existent → 404", r.status_code == 404)

r = requests.get(f"{BASE}/tickets/", params={"category": "billing", "priority": "critical", "status": "open", "search": "charged"})
check("All 4 filters combined → 200", r.status_code == 200)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*50}")
print(f"  Results: {passed} passed | {failed} failed | {skipped} skipped")
print(f"  Score: {passed}/{total} ({round(passed/total*100)}%)")
if not llm_active:
    print(f"\n  ⚠️  Add GROQ_API_KEY to .env and restart to")
    print(f"     unlock {skipped} skipped LLM accuracy tests.")
if failed == 0:
    print("\n  🎉 All tests passed — ready to submit!")
print(f"{'='*50}\n")