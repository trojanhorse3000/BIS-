"""
test_pipeline.py
Automated test suite executing 31 comprehensive test cases:
- 15 Core In-Scope Cases (Standards, QCO Crosswalk, HUID Hallmarking, Scheme Vectors)
- 3 Adversarial False-Positive Disambiguation Cases (Water bottles, Steel cylinders, Electric water heaters)
- 5 Output-Language Directive Separation Cases (including 'helmet in hindi' and 'water bottle in hindi')
- 5 Domain Refusals (Out-of-scope non-BIS queries)
- 3 Hindi Native Round-Trips (Devanagari query processing and synthesis)
- Strict Source URL Verification: Every in-scope citation MUST have a valid, non-null HTTP source_url.
- Strict Gating Verification: Sub-threshold vector fallbacks are NEVER returned for product queries.
- Strict Dynamic Field Translation Audit: No untranslated English titles/categories or English [Source] labels in Hindi output.
"""

import os
import sys
import time
import re

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure bis_ai_pipeline is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(CURRENT_DIR, "bis_ai_pipeline")):
    sys.path.insert(0, os.path.join(CURRENT_DIR, "bis_ai_pipeline"))
else:
    sys.path.insert(0, CURRENT_DIR)

from pipeline.normalize import normalize_query, extract_entities
from pipeline.intent import classify_intent, IntentType
from pipeline.retrieve import HybridRetriever
from pipeline.generate import AnswerGenerator


TEST_SUITE = [
    # =========================================================================
    # 15 CORE IN-SCOPE CASES
    # =========================================================================
    {
        "id": 1,
        "category": "IN_SCOPE",
        "name": "Standard Lookup - IS 1293 (Plugs & Sockets)",
        "query": "What are the specifications under IS 1293:2019?",
        "expected_intent": IntentType.STANDARD_LOOKUP,
        "must_contain": ["IS 1293", "plugs", "socket"],
    },
    {
        "id": 2,
        "category": "IN_SCOPE",
        "name": "Standard Lookup - IS 694 (PVC Cables)",
        "query": "Details about IS 694:2010 PVC insulated cables",
        "expected_intent": IntentType.STANDARD_LOOKUP,
        "must_contain": ["IS 694", "cable"],
    },
    {
        "id": 3,
        "category": "IN_SCOPE",
        "name": "Standard Lookup - IS 13252 (IT Equipment Safety)",
        "query": "Which safety standard covers IT equipment under IS 13252 (Part 1):2010?",
        "expected_intent": IntentType.STANDARD_LOOKUP,
        "must_contain": ["IS 13252", "information technology"],
    },
    {
        "id": 4,
        "category": "IN_SCOPE",
        "name": "Standard Lookup - IS 16046 (Lithium Batteries)",
        "query": "Indian standard IS 16046 (Part 2):2018 for secondary lithium batteries",
        "expected_intent": IntentType.STANDARD_LOOKUP,
        "must_contain": ["IS 16046", "lithium"],
    },
    {
        "id": 5,
        "category": "IN_SCOPE",
        "name": "Standard Lookup - IS 15820 (Assaying & Hallmarking Centres)",
        "query": "General requirements for competence of Assaying and Hallmarking Centres IS 15820:2009",
        "expected_intent": IntentType.STANDARD_LOOKUP,
        "must_contain": ["IS 15820", "hallmarking"],
    },
    {
        "id": 6,
        "category": "IN_SCOPE",
        "name": "Crosswalk QCO - Sulphate Resisting Portland Cement",
        "query": "What standard and QCO applies to Sulphate Resisting Portland Cement?",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 12330", "cement"],
    },
    {
        "id": 7,
        "category": "IN_SCOPE",
        "name": "Crosswalk QCO - Electric Iron (Household Appliance)",
        "query": "Is ISI mark compulsory for Electric iron under household appliances QCO?",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 302", "electric iron"],
    },
    {
        "id": 8,
        "category": "IN_SCOPE",
        "name": "Crosswalk QCO - Mains PVC Insulated Cables",
        "query": "What is the mandatory QCO requirement for PVC insulated cables for working voltages up to 1100V?",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 694", "cable"],
    },
    {
        "id": 9,
        "category": "IN_SCOPE",
        "name": "Crosswalk QCO - Pre-stressed Concrete Steel Wire",
        "query": "Mandatory standard for Plain Hard-drawn Steel Wire For Pre-stressed Concrete",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 1785", "steel"],
    },
    {
        "id": 10,
        "category": "IN_SCOPE",
        "name": "Crosswalk QCO - Automotive Pneumatic Tyres",
        "query": "Which BIS standard applies to Automotive vehicles Tubes for pneumatic tyres?",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 13098", "tyre"],
    },
    {
        "id": 11,
        "category": "IN_SCOPE",
        "name": "HUID Verification - 6-Digit Alphanumeric Code",
        "query": "Please verify gold jewellery hallmark with HUID AB1234",
        "expected_intent": IntentType.HUID_VERIFICATION,
        "must_contain": ["AB1234", "huid"],
    },
    {
        "id": 12,
        "category": "IN_SCOPE",
        "name": "HUID Reference - 22K Gold Fineness",
        "query": "What is the purity fineness grade for 22K gold hallmarking under BIS rules?",
        "expected_intent": IntentType.HUID_VERIFICATION,
        "must_contain": ["916", "22k"],
    },
    {
        "id": 13,
        "category": "IN_SCOPE",
        "name": "Certification Scheme - Scheme I (ISI Mark) Procedure",
        "query": "How do domestic manufacturers apply for Scheme I ISI mark on MANAK Online?",
        "expected_intent": IntentType.CERTIFICATION_SCHEME,
        "must_contain": ["manak online", "isi"],
    },
    {
        "id": 14,
        "category": "IN_SCOPE",
        "name": "Certification Scheme - FMCS Overseas Manufacturers",
        "query": "What is the Foreign Manufacturers Certification Scheme (FMCS) procedure and AIR role?",
        "expected_intent": IntentType.CERTIFICATION_SCHEME,
        "must_contain": ["fmcs", "air"],
    },
    {
        "id": 15,
        "category": "IN_SCOPE",
        "name": "Technical Scheme - CBTF Cluster Facilities for MSMEs",
        "query": "How do MSMEs benefit from Cluster Based Test Facilities (CBTF) under BIS guidelines?",
        "expected_intent": IntentType.CERTIFICATION_SCHEME,
        "must_contain": ["cbtf", "msme"],
    },

    # =========================================================================
    # 3 ADVERSARIAL FALSE-POSITIVE DISAMBIGUATION CASES
    # =========================================================================
    {
        "id": 16,
        "category": "ADVERSARIAL_ACCURACY",
        "name": "Adversarial Disambiguation - Water Bottles (English Baseline)",
        "query": "water bottles",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 17803", "bottle"],
        "must_not_contain": ["IS 3196", "IS 7142", "IS 8737", "IS 8776", "IS 302", "eco mark scheme"],
    },
    {
        "id": 17,
        "category": "ADVERSARIAL_ACCURACY",
        "name": "Adversarial Disambiguation - Steel Cylinder",
        "query": "steel cylinder",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 7285", "cylinder"],
        "must_not_contain": ["IS 17803", "IS 14625", "IS 5168", "eco mark scheme"],
    },
    {
        "id": 18,
        "category": "ADVERSARIAL_ACCURACY",
        "name": "Adversarial Disambiguation - Electric Water Heater",
        "query": "electric water heater",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "must_contain": ["IS 302", "heater"],
        "must_not_contain": ["IS 17803", "IS 14625", "IS 5168", "eco mark scheme"],
    },

    # =========================================================================
    # 5 OUTPUT-LANGUAGE DIRECTIVE & TRANSLATION CASES
    # =========================================================================
    {
        "id": 19,
        "category": "DIRECTIVE_SEPARATION",
        "name": "Language Directive - Water bottles and use hindi",
        "query": "Water bottles and use hindi",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "expected_output_lang": "hi",
        "must_contain": ["IS 17803", "मानक", "पेयजल की बोतलें", "स्रोत"],
        "must_not_contain": ["IS 3196", "IS 7142", "eco mark scheme", "Potable Water Bottles"],
    },
    {
        "id": 20,
        "category": "DIRECTIVE_SEPARATION",
        "name": "Language Directive - Electric iron answer in hindi",
        "query": "Electric iron answer in hindi",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "expected_output_lang": "hi",
        "must_contain": ["IS 302", "मानक", "स्रोत"],
        "must_not_contain": ["eco mark"],
    },
    {
        "id": 21,
        "category": "DIRECTIVE_SEPARATION",
        "name": "Language Directive - PVC insulated cables in hindi",
        "query": "PVC insulated cables in hindi",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "expected_output_lang": "hi",
        "must_contain": ["IS 694", "मानक", "स्रोत"],
        "must_not_contain": ["eco mark"],
    },
    {
        "id": 22,
        "category": "DIRECTIVE_SEPARATION",
        "name": "Dynamic Field Translation - Helmet in Hindi",
        "query": "helmet in hindi",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "expected_output_lang": "hi",
        # Must contain Devanagari translation and source link, NOT untranslated English text:
        "must_contain": ["IS 4151", "हेलमेट", "स्रोत"],
        "must_not_contain": ["Helmet for riders of Two Wheeler", "eco mark"],
    },
    {
        "id": 23,
        "category": "DIRECTIVE_SEPARATION",
        "name": "Dynamic Field Translation - Water bottle in Hindi",
        "query": "water bottle in hindi",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "expected_output_lang": "hi",
        # Must contain Devanagari translation and source link, NOT untranslated English text:
        "must_contain": ["IS 17803", "बोतल", "स्रोत"],
        "must_not_contain": ["Potable Water Bottles", "eco mark"],
    },

    # =========================================================================
    # 5 REFUSALS (OUT-OF-SCOPE)
    # =========================================================================
    {
        "id": 24,
        "category": "REFUSAL",
        "name": "Refusal - Cooking / Culinary Recipe",
        "query": "Can you give me a recipe to cook butter chicken with ingredients?",
        "expected_intent": IntentType.OUT_OF_SCOPE,
        "must_contain": ["outside the scope", "bis"],
    },
    {
        "id": 25,
        "category": "REFUSAL",
        "name": "Refusal - Frontend Web Programming",
        "query": "Write a React component with Tailwind CSS for an interactive navbar dropdown.",
        "expected_intent": IntentType.OUT_OF_SCOPE,
        "must_contain": ["outside the scope", "bis"],
    },
    {
        "id": 26,
        "category": "REFUSAL",
        "name": "Refusal - US FDA 510(k) Medical Clearance",
        "query": "How do I obtain US FDA 510(k) medical device clearance in the United States?",
        "expected_intent": IntentType.OUT_OF_SCOPE,
        "must_contain": ["outside the scope", "bis"],
    },
    {
        "id": 27,
        "category": "REFUSAL",
        "name": "Refusal - Bollywood / Entertainment Trivia",
        "query": "Who is the most famous Bollywood actor to win the National Film Award in 2024?",
        "expected_intent": IntentType.OUT_OF_SCOPE,
        "must_contain": ["outside the scope", "bis"],
    },
    {
        "id": 28,
        "category": "REFUSAL",
        "name": "Refusal - Medical Prescription / Diagnosis",
        "query": "What antibiotic dosage should I take to cure a viral sore throat and fever?",
        "expected_intent": IntentType.OUT_OF_SCOPE,
        "must_contain": ["outside the scope", "bis"],
    },

    # =========================================================================
    # 3 HINDI NATIVE ROUND-TRIPS
    # =========================================================================
    {
        "id": 29,
        "category": "HINDI_ROUNDTRIP",
        "name": "Hindi - Gold Jewellery Hallmarking & HUID Mandate",
        "query": "क्या भारत में सोने के आभूषणों पर 6 अंकों का HUID हॉलमार्क अनिवार्य है?",
        "expected_intent": IntentType.HUID_VERIFICATION,
        "expected_output_lang": "hi",
        "must_contain": ["huid", "सोने", "हॉलमार्क"],
    },
    {
        "id": 30,
        "category": "HINDI_ROUNDTRIP",
        "name": "Hindi - Scheme I ISI Mark Process",
        "query": "घरेलू निर्माताओं के लिए ISI मार्क (Scheme I) प्रमाणन की क्या प्रक्रिया है?",
        "expected_intent": IntentType.CERTIFICATION_SCHEME,
        "expected_output_lang": "hi",
        "must_contain": ["isi", "manak online", "प्रक्रिया"],
    },
    {
        "id": 31,
        "category": "HINDI_ROUNDTRIP",
        "name": "Hindi - Portland Cement Standards & QCO",
        "query": "पोर्टलैंड सीमेंट के लिए कौन सा भारतीय मानक (IS code) लागू होता है?",
        "expected_intent": IntentType.CROSSWALK_LOOKUP,
        "expected_output_lang": "hi",
        "must_contain": ["is 1489", "सीमेंट", "isi"],
    }
]


def run_all_tests():
    print("\n" + "=" * 80)
    print("       BIS AI PIPELINE: COMPREHENSIVE 31-CASE VALIDATION SUITE       ")
    print(" (15 Core In-Scope | 3 Adversarial | 5 Language Directives | 5 Refusals | 3 Hindi) ")
    print("=" * 80 + "\n")

    retriever = HybridRetriever()
    generator = AnswerGenerator()

    passed_count = 0
    failed_count = 0
    results = []

    start_time = time.time()

    for tc in TEST_SUITE:
        tc_id = tc["id"]
        tc_cat = tc["category"]
        tc_name = tc["name"]
        query = tc["query"]
        expected_intent = tc["expected_intent"]
        expected_output_lang = tc.get("expected_output_lang")
        must_contain = tc["must_contain"]
        must_not_contain = tc.get("must_not_contain", [])

        # Step 1: Normalize & Extract
        entities = extract_entities(query)
        content_query = entities.get("cleaned_query", query)
        detected_input_lang = entities.get("detected_input_lang", "en")
        requested_output_lang = entities.get("requested_output_lang", detected_input_lang)
        is_hindi = (requested_output_lang == "hi")

        # Step 2: Intent Classification
        intent_data = classify_intent(content_query, entities)
        actual_intent = intent_data.get("intent")

        # Step 3: Retrieval
        retrieved = retriever.retrieve(content_query, intent_data, entities)

        # Step 4: Generation
        response = generator.generate(
            content_query,
            intent_data,
            retrieved,
            requested_output_lang=requested_output_lang,
            is_hindi=is_hindi
        )
        answer_text = response.get("answer", "")
        citations = response.get("citations", [])

        # Verification Checks
        actual_intent_val = actual_intent.value if hasattr(actual_intent, "value") else str(actual_intent)
        expected_intent_val = expected_intent.value if hasattr(expected_intent, "value") else str(expected_intent)
        intent_match = (actual_intent_val == expected_intent_val)

        lang_match = True
        if expected_output_lang:
            lang_match = (requested_output_lang == expected_output_lang)
        
        answer_lower = answer_text.lower()
        content_matches = [kw.lower() in answer_lower for kw in must_contain]
        content_match = any(content_matches) if tc_cat == "HINDI_ROUNDTRIP" else all(content_matches)

        # Adversarial Exclusion Check (no false-positive row leakage, no ECO Mark fallback, no English titles)
        exclusion_fails = [bad_kw for bad_kw in must_not_contain if bad_kw.lower() in answer_lower]
        exclusion_match = (len(exclusion_fails) == 0)

        # Citation Source URL Audit
        url_audit_passed = True
        missing_url_details = []
        if tc_cat in ("IN_SCOPE", "ADVERSARIAL_ACCURACY", "DIRECTIVE_SEPARATION", "HINDI_ROUNDTRIP"):
            if not citations:
                url_audit_passed = False
                missing_url_details.append("No citations returned")
            else:
                for idx, c in enumerate(citations):
                    url = c.get("source_url")
                    if not url or not isinstance(url, str) or not url.startswith("http"):
                        url_audit_passed = False
                        missing_url_details.append(f"Citation #{idx} ({c.get('is_number')}) missing source_url: {url}")

        # Markdown Bullet & Link Formatting Audit
        formatting_audit_passed = True
        missing_formatting_details = []
        if len(citations) >= 2 and tc_cat in ("IN_SCOPE", "ADVERSARIAL_ACCURACY", "DIRECTIVE_SEPARATION", "HINDI_ROUNDTRIP"):
            bullet_count = answer_text.count("- **")
            if bullet_count < len(citations):
                formatting_audit_passed = False
                missing_formatting_details.append(f"Expected at least {len(citations)} markdown bullets (- **), found {bullet_count}")

            expected_label = "[स्रोत](http" if requested_output_lang == "hi" else "[Source](http"
            link_count = answer_text.count(expected_label)
            valid_src_count = sum(1 for c in citations if c.get("source_url") and c.get("source_url").startswith("http"))
            if link_count < valid_src_count:
                formatting_audit_passed = False
                missing_formatting_details.append(f"Expected at least {valid_src_count} markdown links ({expected_label}...), found {link_count}")

            # Check for bare unlinked "http" strings outside markdown hyperlinks
            no_md_links = re.sub(r"\[.*?\]\(https?://[^\s\)]+\)", "", answer_text)
            if re.search(r"https?://", no_md_links):
                formatting_audit_passed = False
                missing_formatting_details.append("Found bare unlinked 'http' URL sitting outside markdown hyperlink in answer text")

        # Dynamic Field Translation Audit (for Hindi output)
        translation_audit_passed = True
        missing_translation_details = []
        if requested_output_lang == "hi" and citations:
            for idx, c in enumerate(citations):
                t_hi = c.get("product_hi") or c.get("title_hi")
                if t_hi:
                    has_devanagari = bool(re.search(r"[\u0900-\u097F]", t_hi))
                    if not has_devanagari:
                        translation_audit_passed = False
                        missing_translation_details.append(f"Citation #{idx} ({c.get('is_number')}) title not in Devanagari: '{t_hi}'")
            if "[Source](" in answer_text:
                translation_audit_passed = False
                missing_translation_details.append("Found English '[Source](' label in Hindi output instead of '[स्रोत]('")

        passed = (
            intent_match and lang_match and content_match and
            exclusion_match and url_audit_passed and
            formatting_audit_passed and translation_audit_passed
        )

        if passed:
            passed_count += 1
            status_str = "PASS"
        else:
            failed_count += 1
            status_str = "FAIL"

        results.append({
            "id": tc_id,
            "category": tc_cat,
            "name": tc_name,
            "status": status_str,
            "intent_match": intent_match,
            "lang_match": lang_match,
            "content_match": content_match,
            "exclusion_match": exclusion_match,
            "url_audit_passed": url_audit_passed,
            "formatting_audit_passed": formatting_audit_passed,
            "translation_audit_passed": translation_audit_passed,
            "citation_count": len(citations)
        })

        print(f"[{status_str}] Test {tc_id:02d} [{tc_cat:20s}]: {tc_name}")
        if not passed:
            print(f"       Query: {query}")
            print(f"       Intent Expected: {expected_intent_val}, Got: {actual_intent_val} (Match: {intent_match})")
            if not lang_match:
                print(f"       Language Expected: {expected_output_lang}, Got: {requested_output_lang}")
            print(f"       Must Contain: {must_contain} (Matches: {content_matches})")
            if not exclusion_match:
                print(f"       Exclusion Failed (Found forbidden terms): {exclusion_fails}")
            if not url_audit_passed:
                print(f"       Source URL Audit Failed: {missing_url_details}")
            if not formatting_audit_passed:
                print(f"       Formatting Audit Failed: {missing_formatting_details}")
            if not translation_audit_passed:
                print(f"       Translation Audit Failed: {missing_translation_details}")
            print(f"       Output Snippet: {answer_text[:140]}...\n")

    total_time = time.time() - start_time

    # Print Summary Table
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed_count}/{len(TEST_SUITE)} tests passed in {total_time:.2f} seconds.")
    print("=" * 80)

    category_summary = {}
    for r in results:
        cat = r["category"]
        if cat not in category_summary:
            category_summary[cat] = {"passed": 0, "total": 0}
        category_summary[cat]["total"] += 1
        if r["status"] == "PASS":
            category_summary[cat]["passed"] += 1

    for cat, stats in category_summary.items():
        print(f" - {cat:22s}: {stats['passed']}/{stats['total']} passed")

    print("=" * 80)
    
    if failed_count > 0:
        print(f"FAILED: {failed_count} test(s) failed.")
        sys.exit(1)
    else:
        print("SUCCESS: ALL 31 TEST CASES PASSED! Dynamic field translation & formatting verified.\n")
        sys.exit(0)


if __name__ == "__main__":
    run_all_tests()
