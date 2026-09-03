"""
pipeline/prompts.py
Prompt templates, few-shot examples, and citation-forcing prompt builder for BIS AI Pipeline.
"""

from typing import List, Dict, Any, Optional

CITATION_INSTRUCTION = """
When your answer includes one or more standards, format them as a markdown bulleted
list — one bullet per standard — never as a continuous paragraph. Each bullet must
follow this exact shape:

- **{is_number}**: {is_title or product} — {one-line relevance note}. [Source]({source_url})

If a standard has no source_url available, write "(source pending)" instead of a
broken or missing link — never omit the citation entirely and never invent a URL.
""".strip()

FEW_SHOT_EXAMPLES = """
### Examples of compliant citation bullet formatting:

- **IS 17803:2022**: Potable Water Bottles (Copper, Stainless Steel, Aluminum) — Mandatory Scheme I (ISI Mark) under Potable Water Bottles Quality Control Order. [Source](https://bis.gov.in/wp-content/uploads/2023/07/Pottable-Wtaer-bottles-QCO-2023-1.pdf)
- **IS 1293:2019**: Plugs and Socket-Outlets of Rated Voltage up to and including 250 Volts — Mandatory safety standard for household electrical plugs and sockets. [Source](https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails/IS%201293:2019)
- **IS 14625**: Plastic Feeding Bottles — Mandatory ISI Mark under Infant Milk Substitutes and Feeding Bottles Act. [Source](https://indiacode.nic.in/bitstream/123456789/1958/1/199241.pdf)
""".strip()


def build_system_prompt() -> str:
    """Return system prompt with citation forcing and few-shot formatting rules."""
    return f"""
You are the official regulatory AI assistant for the Bureau of Indian Standards (BIS).
You provide authoritative information on Indian Standards (IS), Quality Control Orders (QCO),
Hallmark Unique Identification (HUID), and BIS Conformity Assessment Schemes.

{CITATION_INSTRUCTION}

{FEW_SHOT_EXAMPLES}
""".strip()


def build_citation_prompt(
    query: str,
    intent: str,
    structured_data: Optional[List[Dict[str, Any]]] = None,
    vector_data: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Construct full prompt instructing the model to reproduce citations in exact
    bulleted markdown hyperlink format.
    """
    lines = [
        build_system_prompt(),
        "\n--- Verified Regulatory Data Context ---"
    ]

    if structured_data:
        for idx, item in enumerate(structured_data, start=1):
            is_num = item.get("is_number") or item.get("applicable_is_number") or "IS Standard"
            prod_title = item.get("product") or item.get("title") or item.get("is_title") or "Regulated Product"
            scheme = item.get("scheme") or item.get("scheme_type") or "Scheme I (ISI Mark)"
            src = item.get("source_url") or item.get("bis_page_url") or ""
            link_str = f"[Source]({src})" if src and src.startswith("http") else "(source pending)"
            lines.append(f"- **{is_num}**: {prod_title} ({scheme}) — {link_str}")
    else:
        lines.append("No structured database records.")

    if vector_data:
        lines.append("\n--- Vector Knowledge Context ---")
        for v in vector_data:
            meta = v.get("metadata", {})
            src = meta.get("source_url") or ""
            link_str = f"[Source]({src})" if src and src.startswith("http") else "(source pending)"
            lines.append(f"- **{meta.get('title', 'BIS Guideline')}**: {v.get('text', '')[:200]}... — {link_str}")

    lines.append(f"\nUser Query: {query}")
    lines.append(f"Intent: {intent}")
    lines.append("Answer in bulleted markdown format following the exact specification:")
    return "\n".join(lines)
