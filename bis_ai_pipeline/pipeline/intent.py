"""
pipeline/intent.py
Intent classification for BIS queries including Refusal/Out-of-scope detection and product standards matching.
"""

from enum import Enum
from typing import Dict, Any, List


class IntentType(str, Enum):
    HUID_VERIFICATION = "HUID_VERIFICATION"
    STANDARD_LOOKUP = "STANDARD_LOOKUP"
    QCO_COMPLIANCE = "QCO_COMPLIANCE"
    CROSSWALK_LOOKUP = "CROSSWALK_LOOKUP"
    CERTIFICATION_SCHEME = "CERTIFICATION_SCHEME"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"  # Refusals


IN_SCOPE_KEYWORDS = [
    "bis", "standard", "standards", "is ", "isi", "qco", "quality control", "hallmark", "huid",
    "ahc", "lab", "assaying", "jewellery", "gold", "silver", "karat", "purity", "caratage",
    "scheme", "crs", "fmcs", "cbtf", "eco mark", "manak", "certification", "license", "licence",
    "cement", "cables", "steel", "battery", "batteries", "plugs", "socket", "water", "appliances",
    "switchgear", "pipes", "bottles", "stoves", "tyres", "cylinders", "x-ray", "conformance",
    "conformity", "compliance", "mandatory", "compulsory", "test", "testing", "msme",
    # Hindi keywords
    "मानक", "हॉलमार्क", "प्रमाणन", "सोने", "सोना", "सीमेंट", "लागू"
]

OUT_OF_SCOPE_TRIGGERS = [
    "recipe", "butter chicken", "cook", "bake", "ingredient", "dish",
    "react", "component", "css", "html", "javascript", "tailwind", "programming", "python code for",
    "fda", "510(k)", "united states", "usa fda", "us fda", "ce mark", "osha",
    "bollywood", "actor", "actress", "movie", "film", "cinema", "award", "box office",
    "antibiotic", "sore throat", "symptoms", "prescription", "cure", "dosage", "diagnos"
]


def classify_intent(query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify query into an IntentType based on extracted entities, semantic keywords,
    and out-of-scope refusal triggers.
    """
    q_lower = query.lower()

    # 1. Out-of-Scope / Refusal Check
    is_explicit_refusal = any(trigger in q_lower for trigger in OUT_OF_SCOPE_TRIGGERS)
    has_in_scope = any(kw in q_lower for kw in IN_SCOPE_KEYWORDS) or bool(entities.get("is_numbers")) or bool(entities.get("huid_codes")) or bool(entities.get("search_keywords")) or bool(entities.get("product_terms"))

    if is_explicit_refusal or (not has_in_scope and len(q_lower.split()) > 3):
        return {
            "intent": IntentType.OUT_OF_SCOPE,
            "confidence": 0.98 if is_explicit_refusal else 0.85,
            "primary_target": None,
            "reason": "Query falls outside the mandate of Bureau of Indian Standards (BIS)."
        }

    # 2. Specific Indian Standard Lookup (when IS number is detected and not a QCO inquiry)
    is_nums = entities.get("is_numbers", [])
    qco_indicators = ["qco", "mandatory", "compulsory", "order", "which standard applies", "applies to", "isi mark compulsory"]
    is_qco_inquiry = any(qi in q_lower for qi in qco_indicators)

    if is_nums and not is_qco_inquiry:
        return {
            "intent": IntentType.STANDARD_LOOKUP,
            "confidence": 0.95,
            "primary_target": is_nums[0]
        }

    # 3. HUID Verification & Hallmarking
    if (entities.get("huid_codes") or "huid" in q_lower or 
        ("hallmark" in q_lower and not is_nums) or 
        "सोना" in query or "सोने" in query or "fineness" in q_lower or "karat" in q_lower):
        return {
            "intent": IntentType.HUID_VERIFICATION,
            "confidence": 0.95,
            "primary_target": entities.get("huid_codes")[0] if entities.get("huid_codes") else "HALLMARKING_GENERAL"
        }

    # 4. Certification Schemes & Procedures (ISI Scheme I, CRS Scheme II, FMCS, CBTF, ECO Mark)
    scheme_keywords = ["scheme", "crs", "fmcs", "cbtf", "eco mark", "apply for", "simplified procedure", "manak online", "प्रक्रिया", "प्रमाणन", "msme"]
    if any(sk in q_lower for sk in scheme_keywords):
        return {
            "intent": IntentType.CERTIFICATION_SCHEME,
            "confidence": 0.90,
            "primary_target": None
        }

    # 5. Crosswalk & Product Standards Lookup (e.g., "Cement BIS standards", "water bottles", "steel cylinder", "tyres QCO")
    crosswalk_triggers = ["qco", "mandatory", "compulsory", "crosswalk", "applies to", "which bis standard", "which standard", "isi mark compulsory", "लागू", "मानक", "order", "standard", "standards"]
    has_product = bool(entities.get("product_terms")) or bool(entities.get("search_keywords"))
    is_short_product_inquiry = has_product and (len(q_lower.split()) <= 4)
    if entities.get("hs_codes") or is_nums or (has_product and any(ct in q_lower for ct in crosswalk_triggers)) or is_short_product_inquiry or any(ct in q_lower for ct in ["qco", "crosswalk", "लागू"]):
        return {
            "intent": IntentType.CROSSWALK_LOOKUP,
            "confidence": 0.92,
            "primary_target": entities.get("hs_codes")[0] if entities.get("hs_codes") else (is_nums[0] if is_nums else (entities.get("product_terms")[0] if entities.get("product_terms") else None))
        }

    # 6. General BIS Knowledge / RAG
    return {
        "intent": IntentType.GENERAL_KNOWLEDGE,
        "confidence": 0.75,
        "primary_target": None
    }
