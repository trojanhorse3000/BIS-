"""
BIS AI — Edge Case Test Suite
Runs 20+ queries against the running backend and validates response quality.
"""
import json, sys, time, io
import httpx

# Force UTF-8 stdout for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"
results = []

def test(name, query, expect_ok=True, expect_intent=None, expect_refusal=False, expect_no_is=None):
    t0 = time.perf_counter()
    try:
        r = httpx.post(f"{BASE}/api/query", json={"query": query}, timeout=15)
        r.raise_for_status()
        body = r.json()
        latency = round((time.perf_counter() - t0) * 1000, 1)

        intent = body.get("intent", {}).get("intent", "UNKNOWN")
        answer = body.get("answer", "")
        citations = body.get("citations", [])
        is_refusal = body.get("is_refusal", False)
        source = body.get("source", "")
        retrieved = body.get("retrieved", {})

        # Validation checks
        issues = []

        # Should not crash (answer exists)
        if answer is None:
            issues.append("answer is null")

        # Expected intent?
        if expect_intent and intent != expect_intent:
            issues.append(f"intent={intent} expected={expect_intent}")

        # Expected refusal?
        if expect_refusal and not is_refusal:
            issues.append("expected refusal but got answer")
        if not expect_refusal and is_refusal:
            issues.append("unexpected refusal")

        # Should NOT contain a non-existent IS number
        if expect_no_is and f"IS {expect_no_is}" in answer:
            issues.append(f"found non-existent IS {expect_no_is} in answer")

        ok = len(issues) == 0
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        print(f"      Intent: {intent} | Source: {source} | Latency: {latency}ms | Refusal: {is_refusal}")
        if answer:
            print(f"      Answer: {answer[:120].rstrip()}{'…' if len(answer) > 120 else ''}")
        if issues:
            print(f"      ⚠️  {', '.join(issues)}")
        results.append({"name": name, "ok": ok, "intent": intent, "issues": issues, "latency_ms": latency})
    except Exception as e:
        print(f"  ❌ {name} — EXCEPTION: {e}")
        results.append({"name": name, "ok": False, "intent": "ERROR", "issues": [str(e)], "latency_ms": 0})


print("=" * 65)
print("BIS AI — Edge Case Test Suite")
print("=" * 65)

# ── 1. Standards Lookup ──────────────────────────────────────────────────────
print("\n📋 1. Standards Lookup (IS Codes & Products)")

test(
    "IS 1293 baseline",
    "What is the IS 1293 standard for?",
    expect_intent="STANDARD_LOOKUP",
)
test(
    "Packaged drinking water",
    "Which IS standard applies to packaged drinking water?",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "High-strength deformed steel rebars",
    "Give me the BIS standard number for high-strength deformed steel rebars.",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "EV charging cables",
    "Is there a specific Indian Standard for electric vehicle (EV) charging cables?",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "IS 456 summary",
    "Summarize the requirements under IS 456.",
    expect_intent="STANDARD_LOOKUP",
)

# ── 2. QCO Crosswalk ────────────────────────────────────────────────────────
print("\n🔍 2. QCO (Quality Control Order) Crosswalk")

test(
    "Steel rods QCO baseline",
    "Which QCO applies to steel rods?",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "Leather shoes QCO",
    "Are leather shoes covered under any mandatory QCO right now?",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "Ceiling fans QCO deadline",
    "What is the latest QCO implementation deadline for ceiling fans?",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "Toys QCO adult exclusion",
    "Does the QCO for toys apply to products meant for adults?",
    expect_intent="CROSSWALK_LOOKUP",
)
test(
    "Textiles QCO exemptions",
    "List the products exempted from the recent Textiles QCO.",
    expect_intent="CROSSWALK_LOOKUP",
)

# ── 3. Hallmarking & HUID ───────────────────────────────────────────────────
print("\n✨ 3. Hallmarking & HUID")

test(
    "Hallmarking scheme overview",
    "Tell me about the BIS hallmarking scheme.",
    expect_intent="HUID_VERIFICATION",
)
test(
    "22 karat Hindi baseline",
    "22 क्यरेट सोनें का हॉलमार्क क्या होता है?",
    expect_intent="HUID_VERIFICATION",
)
test(
    "HUID verification process",
    "How can a consumer verify a 6-digit alphanumeric HUID code?",
    expect_intent="HUID_VERIFICATION",
)
test(
    "Silver hallmarking",
    "Is hallmarking mandatory for silver jewelry in India?",
    expect_intent="HUID_VERIFICATION",
)
test(
    "916 vs 750 purity",
    "What is the difference between 916 and 750 gold purity according to BIS?",
    expect_intent="HUID_VERIFICATION",
)

# ── 4. General Regulatory & Compliance ───────────────────────────────────────
print("\n📜 4. General Regulatory & Compliance Processes")

test(
    "FMCS foreign manufacturer",
    "How does a foreign manufacturer apply for BIS certification under the FMCS scheme?",
    expect_intent="CERTIFICATION_SCHEME",
)
test(
    "Penalty without ISI mark",
    "What is the penalty for selling an appliance without a mandatory ISI mark?",
    expect_intent="GENERAL_KNOWLEDGE",
)
test(
    "CRS vs ISI difference",
    "What is the difference between the CRS (Compulsory Registration Scheme) and the ISI mark scheme?",
    expect_intent="CERTIFICATION_SCHEME",
)
test(
    "Fake ISI mark complaint",
    "How can I file a complaint if I find a fake ISI mark on a product?",
    expect_intent="GENERAL_KNOWLEDGE",
)

# ── 5. Edge Cases & Error Handling ───────────────────────────────────────────
print("\n⚠️  5. Edge Cases & Error Handling")

test(
    "Non-existent IS number",
    "What product does IS 9999999 cover?",
    expect_intent="STANDARD_LOOKUP",
)

test(
    "Out-of-scope: FSSAI pickles",
    "Do I need BIS certification to sell homemade pickles?",
    expect_refusal=True,
)

test(
    "Ambiguous: pipes (should still return something)",
    "What is the standard for pipes?",
    expect_intent="CROSSWALK_LOOKUP",
)

test(
    "Hindi follow-up after English",
    "क्या यह अनिवार्य है?",
    expect_intent="GENERAL_KNOWLEDGE",
)

test(
    "Empty-ish query",
    "What is BIS?",
    expect_intent="GENERAL_KNOWLEDGE",
)

test(
    "Coding/programming question (should refuse)",
    "Write a Python script for a REST API",
    expect_refusal=True,
)

test(
    "Bollywood question (should refuse)",
    "Who is the best actor in Bollywood?",
    expect_refusal=True,
)

test(
    "Medical question (should refuse)",
    "What are the symptoms of dengue fever?",
    expect_refusal=True,
)

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
passed = sum(1 for r in results if r["ok"])
failed = sum(1 for r in results if not r["ok"])
print(f"Results: {passed} passed, {failed} failed, {len(results)} total")
if failed:
    print("\nFailed tests:")
    for r in results:
        if not r["ok"]:
            print(f"  - {r['name']}: {r['issues']}")
print("=" * 65)
sys.exit(1 if failed else 0)
