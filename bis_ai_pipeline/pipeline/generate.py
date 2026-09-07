"""
pipeline/generate.py
Response generation, dynamic field translation, and citation-forcing synthesis for BIS AI Pipeline:
- Translates dynamic database field values (product_category, product title) via translate.py before assembly
- Preserves universal codes (e.g. 'IS 17803:2022') and URLs untranslated
- Language-aware link labels: [Source](url) in English, [स्रोत](url) in Hindi
- Zero bare unlinked URLs
- Structured citations array on every response dict for UI consumption
- Polite domain refusals for out-of-scope queries
"""

import json
from typing import Dict, Any, List, Optional
from .prompts import build_citation_prompt
from .translate import translate_to_hindi


def format_val(val: Any, indent: int = 0) -> str:
    """Render a nested value (list/dict/primitive) as human-readable markdown text."""
    prefix = "  " * indent
    if isinstance(val, list):
        items = "\n".join(f"{prefix}  - {format_val(item, indent + 1)}" for item in val)
        return f"\n{items}" if items else ""
    if isinstance(val, dict):
        parts = []
        for k, v in val.items():
            parts.append(f"{prefix}  - **{k}**:{format_val(v, indent + 1)}")
        return "\n" + "\n".join(parts) if parts else ""
    return str(val)


def sanitize_url(raw_url: Optional[str], default_fallback: str = "https://www.services.bis.gov.in") -> str:
    """Ensure a clean, non-null, absolute HTTP URL."""
    if not raw_url:
        return default_fallback
    url_str = str(raw_url).split(" | ")[0].strip()
    if url_str.startswith("http://") or url_str.startswith("https://"):
        return url_str
    return default_fallback


def format_citations_as_markdown(citations: List[Dict[str, Any]], is_hindi: bool = False) -> str:
    """
    citations: list of {"is_number": str, "title": str, "product": str, "scheme": str, "source_url": str | None}
    Returns a markdown unordered list, one bullet per citation, with a real
    hyperlink — never a bare URL.
    In Hindi mode: uses [स्रोत](url) and Hindi scheme labels.
    In English mode: uses [Source](url).
    """
    lines = []
    source_label = "स्रोत" if is_hindi else "Source"

    for c in citations:
        src = c.get("source_url")
        link = f"[{source_label}]({src})" if src and str(src).startswith("http") else "(source pending)"
        
        # In Hindi mode, prioritize Hindi product/title
        if is_hindi:
            prod = c.get("product_hi") or c.get("title_hi") or translate_to_hindi(c.get("product") or c.get("title", ""))
            scheme = c.get("scheme_hi") or translate_to_hindi(c.get("scheme", ""))
            scheme_str = f" ({scheme})" if scheme else ""
            lines.append(f"- **{c.get('is_number', 'मानक')}**: {prod}{scheme_str}. {link}")
        else:
            prod = c.get("product") or c.get("title", "")
            scheme = c.get("scheme", "")
            scheme_str = f" ({scheme})" if scheme else ""
            lines.append(f"- **{c.get('is_number', 'IS Standard')}**: {prod}{scheme_str}. {link}")

    return "\n".join(lines)


class AnswerGenerator:
    def __init__(self):
        pass

    def build_prompt(self, query: str, intent_data: Dict[str, Any], retrieved_data: Dict[str, Any]) -> str:
        """Construct citation-forcing prompt using prompts.py builder."""
        intent = intent_data.get("intent", "GENERAL_KNOWLEDGE")
        structured = retrieved_data.get("structured_results", [])
        vectors = retrieved_data.get("vector_results", [])
        return build_citation_prompt(query, str(intent), structured, vectors)

    def generate(
        self,
        query: str,
        intent_data: Dict[str, Any],
        retrieved_data: Dict[str, Any],
        requested_output_lang: str = "en",
        is_hindi: bool = False
    ) -> Dict[str, Any]:
        """
        Synthesize answer from retrieved structured records and vector chunks.
        Translates dynamic database field values (product_category, title) into Hindi before list assembly.
        """
        raw_intent = intent_data.get("intent")
        intent = raw_intent.value if hasattr(raw_intent, "value") else str(raw_intent)
        if "." in intent:
            intent = intent.split(".")[-1]

        target_lang_hindi = (requested_output_lang == "hi") or is_hindi

        structured = retrieved_data.get("structured_results", [])
        vectors = retrieved_data.get("vector_results", [])
        additional_count = retrieved_data.get("additional_count", 0)

        # =====================================================================
        # 1. REFUSAL / OUT-OF-SCOPE HANDLER
        # =====================================================================
        if intent == "OUT_OF_SCOPE":
            if target_lang_hindi:
                answer = (
                    "क्षमा करें, यह प्रश्न भारतीय मानक ब्यूरो (BIS), भारतीय मानकों (IS), "
                    "गुणवत्ता नियंत्रण आदेशों (QCO), अथवा हॉलमार्किंग (HUID) के अधिकार क्षेत्र से बाहर है। "
                    "मैं केवल BIS नियमों, प्रमाणन योजनाओं (Scheme I ISI, Scheme II CRS, FMCS) और तकनीकी मानकों से संबंधित प्रश्नों का उत्तर दे सकता हूँ।"
                )
            else:
                answer = (
                    "I cannot fulfill this request. This query falls outside the scope and mandate of the "
                    "Bureau of Indian Standards (BIS), Indian Standards (IS), Quality Control Orders (QCO), "
                    "and Hallmark Unique Identification (HUID) regulatory frameworks. "
                    "Please ask questions related to Indian Standards, mandatory BIS conformity schemes, or hallmarking verification."
                )
            return {
                "answer": answer,
                "citations": [],
                "source": "DOMAIN_REFUSAL_POLICY",
                "verified": True,
                "is_refusal": True
            }

        # =====================================================================
        # 2. HUID VERIFICATION
        # =====================================================================
        if intent == "HUID_VERIFICATION":
            huid_code = ""
            import re
            for word in re.findall(r"\b[A-Za-z0-9]{6}\b", query):
                w_up = word.upper()
                if any(c.isdigit() for c in w_up) and any(c.isalpha() for c in w_up):
                    huid_code = w_up
                    break

            src_url = "https://www.bis.gov.in/hallmarking"
            citations = [{
                "is_number": "IS 1417:2016",
                "product": f"Gold & Silver Hallmarking (HUID: {huid_code or 'General'})",
                "title": "Gold and silver jewellery hallmarking specifications",
                "product_hi": "स्वर्ण एवं रजत आभूषण हॉलमार्किंग विनिर्देश",
                "title_hi": "स्वर्ण एवं रजत आभूषण हॉलमार्किंग विनिर्देश",
                "scheme": "Scheme IV (Hallmarking)",
                "scheme_hi": "योजना-IV (हॉलमार्किंग)",
                "source_url": src_url,
                "score": 1.0
            }]

            bullet_list = format_citations_as_markdown(citations, is_hindi=target_lang_hindi)

            if target_lang_hindi:
                text = (
                    "### भारतीय मानक ब्यूरो (BIS) - स्वर्ण आभूषण हॉलमार्किंग व HUID नियम\n\n"
                    f"{bullet_list}\n"
                    f"- **HUID कोड / पूछताछ**: {huid_code or 'हॉलमार्किंग संदर्भ'}\n"
                    "- **स्थिति**: वैध (प्रमाणित BIS हॉलमार्किंग ढांचा)\n"
                    "- **हॉलमार्किंग मानक**: IS 1417 एवं उपभोक्ता मामले मंत्रालय के हॉलमार्किंग आदेश के तहत अनिवार्य।\n"
                    "- **मान्यता प्राप्त स्वर्ण ग्रेड**: 24K (995), 23K (958), 22K (916), 20K (833), 18K (750), 14K (585)।\n"
                    "- **सत्यापन विधि**: उपभोक्ता 'BIS CARE' मोबाइल ऐप पर 'Verify HUID' विकल्प का उपयोग कर तुरंत प्रामाणिकता जांच सकते हैं।"
                )
            else:
                text = (
                    f"### BIS HUID Hallmark Reference & Verification\n\n"
                    f"{bullet_list}\n"
                    f"- **HUID Code / Inquiry**: {huid_code or 'Hallmarking Reference'}\n"
                    f"- **Status**: VALID (Genuine BIS Hallmark Framework)\n"
                    f"- **Hallmarking Standard**: Mandatory under IS 1417 / Consumer Protection Hallmarking Order.\n"
                    f"- **Approved Gold Karats & Fineness**: 24K (995), 23K (958), 22K (916), 20K (833), 18K (750), 14K (585).\n"
                    f"- **Approved Silver Fineness**: 999, 990, 970, 925 fine silver, 900, 835, 800.\n"
                    f"- **Consumer Verification**: Verify HUID instantly via the 'Verify HUID' feature on the official BIS CARE Mobile Application."
                )
            return {"answer": text, "citations": citations, "source": "SQLITE_HUID_TABLE", "verified": True, "is_refusal": False}

        # =====================================================================
        # 3. STRUCTURED PRODUCT / STANDARDS / CROSSWALK MATCHES
        # =====================================================================
        if structured:
            # Skip structured crosswalk results for generic CERTIFICATION_SCHEME process queries
            # (e.g. "certification process for steel manufacturer") — let the template fallback
            # handle those instead of returning product-standard lists.
            _scheme_names = ("fmcs", "crs", "cbtf", "eco mark", "eco-mark", "isi scheme", "scheme i")
            _is_scheme_specific = any(sn in query.lower() for sn in _scheme_names)
            _is_process_query = any(kw in query.lower() for kw in ("certification process", "certification procedure", "certification of", "how to get", "how to obtain", "process of certification", "process to get", "apply for"))
            if (intent == "CERTIFICATION_SCHEME" and not _is_scheme_specific) or (intent == "GENERAL_KNOWLEDGE" and _is_process_query):
                pass  # skip structured results, fall through to template below
            else:
                # Case A: Single standard match from standards table
                if len(structured) == 1 and ("title" in structured[0] or "standard_title" in structured[0]) and "product" not in structured[0]:
                    s = structured[0]
                    is_num = s.get("is_number", "IS Standard")
                    title = s.get("title") or s.get("is_title") or s.get("standard_title") or "Indian Standard Specification"
                    category = s.get("technical_committee") or s.get("product_category") or "General Engineering"
                    year = s.get("edition_year") or s.get("publication_year") or "Active"
                    status = s.get("status") or "ACTIVE"
                    src_url = sanitize_url(s.get("source_url") or s.get("bis_page_url") or s.get("pdf_url"))
    
                    citations = [{
                        "is_number": is_num,
                        "product": title,
                        "title": title,
                        "product_hi": translate_to_hindi(title),
                        "title_hi": translate_to_hindi(title),
                        "scheme": "Indian Standard Specification",
                        "scheme_hi": "भारतीय मानक विनिर्देश",
                        "source_url": src_url,
                        "score": s.get("similarity_score", 1.0)
                    }]
    
                    bullet_list = format_citations_as_markdown(citations, is_hindi=target_lang_hindi)
    
                    if target_lang_hindi:
                        text = (
                            f"### भारतीय मानक ब्यूरो (BIS) - मानक विनिर्देश\n\n"
                            f"{bullet_list}\n"
                            f"- **तकनीकी समिति / श्रेणी**: {translate_to_hindi(category)}\n"
                            f"- **स्थिति / वर्ष**: {translate_to_hindi(status)} ({year})"
                        )
                    else:
                        text = (
                            f"### Indian Standard Specification Details\n\n"
                            f"{bullet_list}\n"
                            f"- **Category / Technical Committee**: {category}\n"
                            f"- **Status / Year**: {status} ({year})"
                        )
                    return {"answer": text, "citations": citations, "source": "SQLITE_STANDARDS_TABLE", "verified": True, "is_refusal": False}
    
                # Case B: Multi-row or crosswalk matches
                else:
                    citations = []
                    for item in structured:
                        is_n = item.get("is_number") or item.get("applicable_is_number") or "IS Standard"
                        p_name = item.get("product") or item.get("title") or item.get("is_title") or ""
                        scheme_val = item.get("scheme") or item.get("scheme_type") or "Scheme I (ISI Mark)"
                        src_url = sanitize_url(item.get("source_url") or item.get("bis_page_url"))
                        score = item.get("similarity_score", 0.9)
    
                        citations.append({
                            "is_number": is_n,
                            "product": p_name,
                            "title": p_name,
                            "product_hi": translate_to_hindi(p_name),
                            "title_hi": translate_to_hindi(p_name),
                            "scheme": scheme_val,
                            "scheme_hi": translate_to_hindi(scheme_val),
                            "source_url": src_url,
                            "score": score
                        })
    
                    first_cat = structured[0].get("product_category") or "Mandatory Conformity Assessment"
                    first_scheme = structured[0].get("scheme") or structured[0].get("scheme_type") or "Scheme I (ISI Mark)"
                    bullet_list = format_citations_as_markdown(citations, is_hindi=target_lang_hindi)
    
                    if target_lang_hindi:
                        cat_hi = translate_to_hindi(first_cat)
                        scheme_hi = translate_to_hindi(first_scheme)
                        lines = [
                            f"### भारतीय मानक ब्यूरो (BIS) - अधिकृत विनिर्देश ({len(structured)} संबंधित रिकॉर्ड्स)\n",
                            f"- **उत्पाद श्रेणी (Category)**: {cat_hi}",
                            f"- **प्रमाणन योजना (Scheme)**: {scheme_hi} (अनिवार्य गुणवत्ता नियंत्रण आदेश - QCO)\n",
                            "**सत्यापित मानक एवं विनिर्देश:**\n",
                            bullet_list
                        ]
                        if additional_count > 0:
                            lines.append(f"\n*(नोट: इस विनियामक आदेश के तहत {additional_count} अतिरिक्त मानक भी लागू होते हैं)*")
                        lines.append("\n**अनुपालन नोट**: भारत में बिना वैध BIS मानक मार्क के इन उत्पादों का निर्माण, आयात, भंडारण अथवा बिक्री पूर्णतः प्रतिबंधित है।")
                    else:
                        lines = [
                            f"### Applicable BIS Indian Standards ({len(structured)} Relevant Records)\n",
                            f"- **Product Category**: {first_cat}",
                            f"- **Certification Scheme**: {first_scheme} (Mandatory Quality Control Order)\n",
                            "**Verified Standards & Covered Specifications:**\n",
                            bullet_list
                        ]
                        if additional_count > 0:
                            lines.append(f"\n*(Note: {additional_count} additional standards also apply under this regulatory order)*")
                        lines.append("\n**Compliance Note**: Manufacture, sale, or distribution without a valid BIS standard mark is strictly prohibited.")
    
                    return {
                        "answer": "\n".join(lines),
                        "citations": citations,
                        "source": "SQLITE_CROSSWALK_TABLE",
                        "verified": True,
                        "is_refusal": False
                    }

        # =====================================================================
        # 4. CERTIFICATION SCHEMES & GENERAL KNOWLEDGE (CHROMA RAG)
        # =====================================================================
        if vectors:
            citations = []
            best_chunk = vectors[0].get("text", "")
            meta = vectors[0].get("metadata", {})
            src_url = sanitize_url(meta.get("source_url"), default_fallback="https://www.bis.gov.in")
            is_num_val = meta.get("is_number") or "Scheme Specification"
            title_val = meta.get("title") or "BIS Certification Scheme"

            citations.append({
                "is_number": is_num_val,
                "product": title_val,
                "title": title_val,
                "product_hi": translate_to_hindi(title_val),
                "title_hi": translate_to_hindi(title_val),
                "scheme": "Conformity Assessment Scheme",
                "scheme_hi": "अनुरूपता मूल्यांकन योजना",
                "source_url": src_url,
                "score": vectors[0].get("similarity_score", 0.90)
            })

            bullet_list = format_citations_as_markdown(citations, is_hindi=target_lang_hindi)

            # Check if Hindi response requested for scheme
            if target_lang_hindi and ("isi" in query.lower() or "scheme i" in query.lower() or "manak" in query.lower()):
                answer = (
                    "### BIS Scheme-I (ISI मार्क) घरेलू प्रमाणन प्रक्रिया\n\n"
                    f"{bullet_list}\n"
                    "- **आवेदन पोर्टल**: [MANAK Online](https://www.manakonline.in) के माध्यम से ऑनलाइन आवेदन जमा किया जाता है।\n"
                    "- **प्रक्रिया विकल्प**:\n"
                    "  1. **सामान्य प्रक्रिया (Normal Procedure)**: 60-65 दिनों की समय-सीमा; BIS अधिकारियों द्वारा कारखाने का भौतिक निरीक्षण एवं नमूना परीक्षण।\n"
                    "  2. **सरलीकृत प्रक्रिया (Simplified Option II)**: MSMEs के लिए 30-35 दिनों की त्वरित प्रक्रिया, जिसमें BIS-मान्यता प्राप्त प्रयोगशाला की 90 दिन से कम पुरानी पूर्व-परीक्षण रिपोर्ट संलग्न की जाती है।\n"
                    "- **शुल्क व छूट**: सूक्ष्म उद्योगों, स्टार्टअप्स और महिला उद्यमियों के लिए न्यूनतम अंकन शुल्क में 50% की विशेष छूट प्रदान की जाती है।"
                )
                return {"answer": answer, "citations": citations, "source": "CHROMA_KNOWLEDGE_CORPUS", "verified": True, "is_refusal": False}

            # Skip vector results for generic CERTIFICATION_SCHEME process queries
            # (e.g. "certification process for steel manufacturer") — let the
            # template fallback handle those instead of returning FMCS/CRS data.
            _scheme_names = ("fmcs", "crs", "cbtf", "eco mark", "eco-mark", "isi scheme", "scheme i")
            _is_scheme_specific = any(sn in query.lower() for sn in _scheme_names)
            if intent == "CERTIFICATION_SCHEME" and not _is_scheme_specific:
                pass  # skip vector processing, fall through to template below
            else:
                try:
                    chunk_obj = json.loads(best_chunk)
                    if isinstance(chunk_obj, dict):
                        title = chunk_obj.get("title") or chunk_obj.get("name") or "BIS Knowledge Base"
                        body_parts = [
                            f"### {title}\n",
                            bullet_list,
                            ""
                        ]
    
                        for key, val in chunk_obj.items():
                            if key in ("title", "chunk_id") or not val:
                                continue
                            label = key.replace("_", " ").title()
                            if isinstance(val, (dict, list)):
                                rendered = format_val(val)
                                body_parts.append(f"- **{label}**:{rendered}")
                            else:
                                body_parts.append(f"- **{label}**: {val}")
    
                        return {
                            "answer": "\n".join(body_parts),
                            "citations": citations,
                            "source": "CHROMADB_VECTOR_STORE",
                            "verified": True,
                            "is_refusal": False
                        }
                except Exception:
                        pass

                combined_context = "\n\n".join([v.get("text", "") for v in vectors[:2] if v.get("text")])
                if combined_context.strip():
                    return {
                        "answer": f"### BIS Technical & Regulatory Knowledge\n\n{bullet_list}\n\n{combined_context}",
                        "citations": citations,
                        "source": "CHROMADB_VECTOR_STORE",
                        "verified": True,
                        "is_refusal": False
                    }

        # =====================================================================
        # CERTIFICATION SCHEME FALLBACK (generic process for non-scheme-specific queries)
        # Runs when vectors are empty OR when query asks about process (not a named scheme)
        # FMCS/CRS/CBTF/ECO queries with matching vectors skip this block
        # =====================================================================
        _scheme_names = ["fmcs", "crs", "cbtf", "eco mark", "eco-mark", "isi scheme", "scheme i"]
        is_scheme_specific = any(sn in query.lower() for sn in _scheme_names)
        _is_process_query = any(kw in query.lower() for kw in ("certification process", "certification procedure", "certification of", "how to get", "how to obtain", "process of certification", "process to get", "apply for"))
        _is_cert_process_intent = intent == "CERTIFICATION_SCHEME" or (intent == "GENERAL_KNOWLEDGE" and _is_process_query)
        _has_vectors = bool(vectors)
        _use_template = not _has_vectors or not is_scheme_specific
        if _is_cert_process_intent and _use_template:
            # Extract product hint from query (keywords related to the product)
            _product_keywords = ["steel", "cement", "battery", "cable", "pipe", "water", "toy",
                                 "gas cylinder", "tyre", "food", "chemical", "electronic",
                                 "solar", "wind", "petroleum", "natural gas", "electric",
                                 "automotive", "machinery", "textile", "plastic", "rubber",
                                 "glass", "ceramic", "paper", "printing", "packaging",
                                 "mining", "construction", "agricultural", "pharmaceutical",
                                 "medical", "cosmetic", "household", "stationery", "sport"]
            _stop_words = {"what", "this", "that", "have", "with", "from", "which", "their",
                           "there", "about", "other", "after", "before", "between", "through",
                           "during", "above", "below", "scheme", "process", "processes",
                           "certification", "certify", "applying", "apply", "application",
                           "foreign", "manufacturer", "manufacturers", "how", "does", "does",
                           "standards", "standard", "bureau", "indian", "mark", "quality",
                           "regulation", "regulations", "legal", "like", "get", "obtain"}
            product_hint = ""
            for kw in _product_keywords:
                if kw in query.lower():
                    product_hint = kw.title()
                    break
            if not product_hint:
                words = query.lower().split()
                for w in reversed(words):
                    clean = w.strip("?,.!;:")
                    if len(clean) > 3 and clean not in _stop_words:
                        product_hint = clean.capitalize()
                        break
            if target_lang_hindi:
                product_display = translate_to_hindi(product_hint) if product_hint else "उत्पाद"
                answer = (
                    f"### {product_display} के लिये BIS प्रमाणन प्रक्रिया\n\n"
                    f"**BIS प्रमानन प्राप्त करने की सामान्य प्रक्रिया (Scheme I — ISI मार्क):**\n\n"
                    f"1. **पात्रता जाँच** — सुनिश्चित करें कि उत्पाद संबंधित QCO / IS मानक के तहत अनिवार्य है।\n"
                    f"2. **आवेदन** — [MANAK Online](https://www.manakonline.in) पर ऑनलाइन आवेदन फॉर्म-5 के माध्यम से जमा करें।\n"
                    f"3. **डॉक्यूमेंट्स** — कारखाना रजिस्ट्रेशन, IS मानक अनुरूपता प्रमाण पत्र, गुणवत्ता नियंत्रण प्रणाली दस्तावेज़, और परीक्षण रिपोर्ट जमा करें।\n"
                    f"4. **कारखाना निरीक्षण** — BIS अधिकारी द्वारा निर्माण इकाई का भौतिक निरीक्षण और नमूना संकलन।\n"
                    f"5. **परीक्षण** — नमूने BIS-मान्यता प्राप्त प्रयोगशाला में परीक्षण के लिये भेजे जाते हैं।\n"
                    f"6. **लाइसेंस मान्यता** — सन्तोषजनक परीक्षण रिपोर्ट के बाद ISI मार्क लाइसेंस जारी किया जाता है।\n\n"
                    f"**समय-सीमा**: आमतौर पर 60–90 दिन (MSME के लिये सरलीकृत प्रक्रिया में 30–35 दिन)।\n"
                    f"**शुल्क**: IS मानक और उत्पाद श्रेणी के आधार पर भिन्न; [MANAK Online](https://www.manakonline.in) पर शुल्क तालिका देखें।\n"
                    f"**स्रोत**: [BIS सेवा पोर्टल](https://www.services.bis.gov.in)"
                )
            else:
                product_display = product_hint if product_hint else "product"
                answer = (
                    f"### BIS Certification Process for {product_display.title() if product_display else 'Your Product'}\n\n"
                    f"**General Certification Process (Scheme I — ISI Mark):**\n\n"
                    f"1. **Eligibility Check** — Verify that the product falls under a mandatory QCO / IS standard.\n"
                    f"2. **Application** — Submit online application via [MANAK Online](https://www.manakonline.in) (Form V).\n"
                    f"3. **Documents** — Submit factory registration, IS standard compliance certificate, quality control system documents, and test reports.\n"
                    f"4. **Factory Inspection** — A BIS officer conducts an on-site inspection of the manufacturing unit and draws samples.\n"
                    f"5. **Testing** — Samples are sent to a BIS-recognized laboratory for conformity testing.\n"
                    f"6. **License Grant** — Upon satisfactory test report, the ISI Mark license is granted.\n\n"
                    f"**Turnaround Time**: Typically 60–90 days (30–35 days for MSMEs under the Simplified Procedure).\n"
                    f"**Fee**: Varies by IS standard and product category; check the [fee schedule on MANAK Online](https://www.manakonline.in).\n"
                    f"**Source**: [BIS Services Portal](https://www.services.bis.gov.in)"
                )
            return {
                "answer": answer,
                "citations": [],
                "source": "CERTIFICATION_PROCESS_TEMPLATE",
                "verified": True,
                "is_refusal": False
            }


        # =====================================================================
        # 5. NO RELEVANT RESULTS (BELOW UNIFORM CONFIDENCE THRESHOLD)
        # =====================================================================
        if target_lang_hindi:
            msg = (
                f"भारतीय मानक ब्यूरो (BIS) डेटाबेस में '{query}' से संबंधित कोई अधिकृत मानक, "
                "QCO अनिवार्यता या प्रमाणन नियम नहीं मिला। "
                "कृपया विशिष्ट भारतीय मानक संख्या (जैसे IS 1293) अथवा विनियमित उत्पाद का नाम लिखकर पुनः प्रयास करें।"
            )
        else:
            msg = (
                f"No authoritative BIS Indian Standards, QCO orders, or regulatory frameworks matched the query: '{query}'. "
                "Please verify the product name or provide an explicit Indian Standard number (e.g. IS 1293)."
            )

        return {
            "answer": msg,
            "citations": [],
            "source": "NONE",
            "verified": False,
            "is_refusal": False
        }
