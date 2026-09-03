"""
pipeline/normalize.py
Query normalization, language detection, language directive parsing,
entity extraction, and product tokenization for BIS AI Pipeline.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


def is_devanagari(text: str) -> bool:
    """Check if query contains Devanagari (Hindi) script."""
    return bool(re.search(r"[\u0900-\u097F]", text))


def normalize_query(query: str) -> str:
    """Clean whitespace and standardize common symbols."""
    if not query:
        return ""
    q = query.strip()
    q = re.sub(r"\s+", " ", q)
    return q


# Lightweight regex patterns for explicit language directives (longer patterns ordered first)
LANGUAGE_DIRECTIVE_PATTERNS = [
    (re.compile(r"\b(?:and\s+)?(?:answer|reply|respond)\s+in\s+hindi\b", re.IGNORECASE), "hi"),
    (re.compile(r"\b(?:and\s+)?use\s+hindi\b", re.IGNORECASE), "hi"),
    (re.compile(r"\bhindi\s+me(?:in)?\s+(?:batao|bataiye|kaho)\b", re.IGNORECASE), "hi"),
    (re.compile(r"\bhindi\s+me(?:in)?\b", re.IGNORECASE), "hi"),
    (re.compile(r"\bहिंदी\s+में\s*(?:बताएं|बताओ|उत्तर\s+दें)?\b"), "hi"),
    (re.compile(r"\b(?:and\s+)?in\s+hindi\b", re.IGNORECASE), "hi"),
    (re.compile(r"\b(?:and\s+)?(?:answer|reply|respond)\s+in\s+english\b", re.IGNORECASE), "en"),
    (re.compile(r"\b(?:and\s+)?use\s+english\b", re.IGNORECASE), "en"),
    (re.compile(r"\b(?:and\s+)?in\s+english\b", re.IGNORECASE), "en"),
]


def parse_language_directive(query: str) -> Tuple[str, Optional[str]]:
    """
    Separate query content from explicit output-language directives (e.g. 'use hindi', 'answer in hindi').
    Returns (cleaned_content_query, requested_lang_or_None).
    """
    cleaned = normalize_query(query)
    requested_lang = None

    for pattern, lang in LANGUAGE_DIRECTIVE_PATTERNS:
        if pattern.search(cleaned):
            requested_lang = lang
            cleaned = pattern.sub("", cleaned)
            break

    # Clean residual connector words, punctuation, and whitespaces
    cleaned = re.sub(r"[,;।]\s*$", "", cleaned)
    cleaned = re.sub(r"\s+and\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*and\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = normalize_query(cleaned)

    # If the user just typed the directive alone (e.g. "use hindi"), don't make it empty
    if not cleaned:
        cleaned = query.strip()

    return cleaned, requested_lang


STOP_WORDS = {
    "what", "which", "standard", "standards", "under", "apply", "applies",
    "applicable", "code", "codes", "bis", "isi", "qco", "mandatory", "compulsory",
    "for", "the", "and", "with", "details", "about", "indian", "specification",
    "specifications", "please", "verify", "check", "tell", "show", "give", "me",
    "answer", "reply", "respond"
}


def extract_entities(query: str) -> Dict[str, Any]:
    """
    Extract key identifiers from the query:
    - cleaned_query: directive-stripped query content
    - detected_input_lang: 'hi' or 'en'
    - requested_output_lang: 'hi' or 'en'
    - is_hindi: True if requested_output_lang is 'hi'
    - is_numbers, huid_codes, hs_codes, product_terms, search_keywords
    """
    # 1. Parse and strip explicit output-language directives
    content_query, explicit_lang = parse_language_directive(query)
    detected_input_lang = "hi" if is_devanagari(query) else "en"
    requested_output_lang = explicit_lang if explicit_lang else detected_input_lang

    entities = {
        "is_numbers": [],
        "huid_codes": [],
        "hs_codes": [],
        "product_terms": [],
        "detected_input_lang": detected_input_lang,
        "requested_output_lang": requested_output_lang,
        "is_hindi": (requested_output_lang == "hi"),
        "search_keywords": [],
        "cleaned_query": content_query,
        "raw_query": query,
    }

    # 2. Match Indian Standards (e.g. IS 1293, IS 13252 (Part 1):2010, IS-15820)
    is_pattern = re.compile(
        r"\b(?:IS|is)[-\s]?(\d+(?:\s*\([^\)]+\))?(?:\s*:\s*\d{4})?)",
        re.IGNORECASE,
    )
    for match in is_pattern.finditer(content_query):
        num_part = match.group(1).strip()
        entities["is_numbers"].append(f"IS {num_part}".upper())

    # 3. Match 6-character HUID (alphanumeric, exactly 6 characters, must contain both letters & digits)
    words = re.findall(r"\b[A-Za-z0-9]{6}\b", content_query)
    for word in words:
        upper_w = word.upper()
        has_alpha = any(c.isalpha() for c in upper_w)
        has_digit = any(c.isdigit() for c in upper_w)
        if has_alpha and has_digit:
            entities["huid_codes"].append(upper_w)

    # 4. Match HS / ITC-HS codes
    hs_pattern = re.compile(r"\b(\d{4}(?:\.\d{2}(?:\.\d{2})?)?|\d{6}|\d{8})\b")
    for match in hs_pattern.finditer(content_query):
        candidate = match.group(1).strip()
        if len(candidate) == 4 and (candidate.startswith("19") or candidate.startswith("20")):
            continue
        entities["hs_codes"].append(candidate)

    # 5. Extract Candidate Product Terms by stripping stop words from content_query
    tokens = [w for w in re.findall(r"[A-Za-z]+", content_query) if w.lower() not in STOP_WORDS and len(w) > 2]
    if tokens:
        entities["product_terms"].append(" ".join(tokens))
        for t in tokens:
            if t not in entities["product_terms"]:
                entities["product_terms"].append(t)

    # 6. Map Hindi concepts to search keywords
    if detected_input_lang == "hi":
        if "सोना" in content_query or "सोने" in content_query or "हॉलमार्क" in content_query:
            entities["search_keywords"].extend(["gold", "hallmarking", "huid", "IS 1417"])
        if "सीमेंट" in content_query:
            entities["search_keywords"].extend(["cement", "portland cement", "IS 1489", "IS 269"])
        if "isi" in content_query.lower() or "प्रमाणन" in content_query or "प्रक्रिया" in content_query:
            entities["search_keywords"].extend(["ISI mark", "Scheme I", "certification process"])

    return entities
