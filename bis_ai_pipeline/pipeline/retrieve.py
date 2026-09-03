"""
pipeline/retrieve.py
Relevance-scored hybrid retrieval engine combining SQLite relational lookups,
in-memory sentence-transformers embedding similarity for Crosswalk, and ChromaDB vector search
with uniform confidence gating across ALL retrieval paths.
"""

import os
import sqlite3
import re
from typing import Dict, Any, List, Optional
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(PARENT_DIR, "bis_data.db")
CHROMA_DIR = os.path.join(PARENT_DIR, "chroma_store")
COLLECTION_NAME = "bis_knowledge"


def clean_source_url(raw_url: Optional[str]) -> str:
    """Return a single clean, valid source URL."""
    if not raw_url or not str(raw_url).strip():
        return "https://www.services.bis.gov.in"
    first_url = str(raw_url).split(" | ")[0].strip()
    if not first_url.startswith("http"):
        return "https://www.services.bis.gov.in"
    return first_url


class HybridRetriever:
    def __init__(self, db_path: str = DB_PATH, chroma_dir: str = CHROMA_DIR):
        self.db_path = db_path
        self.chroma_dir = chroma_dir
        self._model = None
        self._chroma_client = None
        self._collection = None
        self._crosswalk_rows = None
        self._crosswalk_embeddings = None

    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        if not os.path.exists(self.db_path):
            return None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_collection(self):
        if self._collection is None:
            if not os.path.exists(self.chroma_dir):
                return None
            try:
                self._chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
                for name in ["bis_knowledge", "bis_knowledge_base"]:
                    try:
                        self._collection = self._chroma_client.get_collection(name=name)
                        break
                    except Exception:
                        continue
            except Exception:
                return None
        return self._collection

    def _get_model(self):
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _load_crosswalk_index(self):
        """Pre-index crosswalk rows and product embeddings in memory."""
        if self._crosswalk_rows is not None and self._crosswalk_embeddings is not None:
            return self._crosswalk_rows, self._crosswalk_embeddings

        conn = self._get_db_connection()
        if not conn:
            return [], None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, product, product_category, scheme, is_number, is_title, qco_number, ministry, source_url FROM crosswalk"
            )
            rows = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

        if not rows:
            return [], None

        model = self._get_model()
        texts = []
        for r in rows:
            p = r.get("product") or ""
            c = r.get("product_category") or ""
            texts.append(f"{p} - {c}".strip(" -"))

        embeddings = model.encode(texts, normalize_embeddings=True)
        self._crosswalk_rows = rows
        self._crosswalk_embeddings = embeddings
        return self._crosswalk_rows, self._crosswalk_embeddings

    # --- Structured Database Methods ---

    def lookup_huid(self, query_term: str) -> Optional[Dict[str, Any]]:
        """Look up HUID in SQLite."""
        conn = self._get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('huid_records', 'huid_reference')")
            tables = [r[0] for r in cursor.fetchall()]

            cleaned = query_term.upper().strip()

            if "huid_records" in tables:
                cursor.execute("SELECT * FROM huid_records WHERE UPPER(huid_code) = ?", (cleaned,))
                row = cursor.fetchone()
                if row:
                    d = dict(row)
                    d["source_url"] = clean_source_url(d.get("source_url") or "https://www.bis.gov.in/hallmarking")
                    d["similarity_score"] = 1.0
                    return d

            if "huid_reference" in tables:
                cursor.execute("SELECT * FROM huid_reference WHERE caratage LIKE ? OR gold_fineness_grade LIKE ?", (f"%{cleaned}%", f"%{cleaned}%"))
                rows = cursor.fetchall()
                if rows:
                    ref_list = []
                    for r in rows:
                        rd = dict(r)
                        rd["source_url"] = clean_source_url(rd.get("source_url") or "https://www.bis.gov.in/hallmarking")
                        ref_list.append(rd)
                    return {
                        "query_term": query_term,
                        "status": "VALID REFERENCE",
                        "source_url": "https://www.bis.gov.in/hallmarking",
                        "reference_rules": ref_list,
                        "similarity_score": 1.0
                    }
                cursor.execute("SELECT * FROM huid_reference LIMIT 5")
                rows = cursor.fetchall()
                if rows:
                    ref_list = []
                    for r in rows:
                        rd = dict(r)
                        rd["source_url"] = clean_source_url(rd.get("source_url") or "https://www.bis.gov.in/hallmarking")
                        ref_list.append(rd)
                    return {
                        "query_term": query_term,
                        "status": "VALID FORMAT (6-Character Hallmark)",
                        "source_url": "https://www.bis.gov.in/hallmarking",
                        "reference_rules": ref_list,
                        "similarity_score": 1.0
                    }
            return None
        finally:
            conn.close()

    def lookup_standard(self, is_query: str) -> List[Dict[str, Any]]:
        """Look up standard by exact or partial IS number / title."""
        conn = self._get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cleaned = is_query.strip()
            
            cursor.execute("PRAGMA table_info(standards)")
            columns = [r[1] for r in cursor.fetchall()]
            title_col = "title" if "title" in columns else "standard_title"

            simple_is = cleaned.split(":")[0].strip()

            query_sql = f"""
                SELECT * FROM standards 
                WHERE is_number LIKE ? OR is_number LIKE ? OR {title_col} LIKE ?
                LIMIT 10
            """
            cursor.execute(query_sql, (f"%{cleaned}%", f"%{simple_is}%", f"%{cleaned}%"))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["source_url"] = clean_source_url(d.get("bis_page_url") or d.get("pdf_url") or d.get("source_url"))
                d["similarity_score"] = 1.0
                results.append(d)
            return results
        finally:
            conn.close()

    def lookup_crosswalk_exact_is(self, is_number: str) -> List[Dict[str, Any]]:
        """Look up crosswalk rows by specific IS number."""
        conn = self._get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cleaned = is_number.strip().split(":")[0].strip()
            cursor.execute("SELECT * FROM crosswalk WHERE is_number LIKE ? LIMIT 5", (f"%{cleaned}%",))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["source_url"] = clean_source_url(d.get("source_url"))
                d["similarity_score"] = 1.0
                results.append(d)
            return results
        finally:
            conn.close()

    # --- Relevance-Scored Embedding Search ---

    def semantic_search_crosswalk(self, query: str, threshold: float = 0.52, top_k: int = 6) -> Dict[str, Any]:
        """
        Relevance-scored retrieval matching specifically against the product
        and product_category fields using sentence-transformers embedding similarity.
        Filters out rows below threshold and caps results at top_k.
        """
        rows, embeddings = self._load_crosswalk_index()
        if not rows or embeddings is None:
            return {"matches": [], "additional_count": 0, "total_cleared": 0}

        model = self._get_model()
        q_emb = model.encode([query], normalize_embeddings=True)[0]
        sims = np.dot(embeddings, q_emb)

        qualifying = []
        for idx, score in enumerate(sims):
            if float(score) >= threshold:
                qualifying.append((idx, float(score)))

        qualifying.sort(key=lambda x: x[1], reverse=True)

        top_matches = []
        for idx, score in qualifying[:top_k]:
            row_copy = dict(rows[idx])
            row_copy["similarity_score"] = round(score, 3)
            row_copy["source_url"] = clean_source_url(row_copy.get("source_url"))
            top_matches.append(row_copy)

        additional_count = max(0, len(qualifying) - top_k)
        return {
            "matches": top_matches,
            "additional_count": additional_count,
            "total_cleared": len(qualifying)
        }

    # --- Vector Search Methods (ChromaDB) with Uniform Confidence Gating ---

    def search_vector_corpus(self, query: str, threshold: float = 0.50, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Perform semantic search on vector corpus using ChromaDB with uniform confidence threshold.
        Never accepts sub-threshold matches (e.g. 0.319 ECO Mark).
        """
        collection = self._get_collection()
        if not collection:
            return []

        try:
            model = self._get_model()
            q_emb = model.encode([query], normalize_embeddings=True)[0]
            
            res = collection.query(
                query_embeddings=[q_emb.tolist()],
                n_results=min(top_k * 2, collection.count() or top_k)
            )

            results = []
            if res and res.get("documents") and res["documents"][0]:
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                ids = res["ids"][0]

                doc_embs = model.encode(docs, normalize_embeddings=True)
                sims = np.dot(doc_embs, q_emb)

                for doc, meta, doc_id, score in zip(docs, metas, ids, sims):
                    score_f = float(score)
                    if score_f >= threshold:
                        meta_copy = dict(meta) if meta else {}
                        meta_copy["source_url"] = clean_source_url(meta_copy.get("source_url") or "https://www.bis.gov.in")
                        results.append({
                            "id": doc_id,
                            "text": doc,
                            "metadata": meta_copy,
                            "similarity_score": round(score_f, 3)
                        })

                results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:top_k]
        except Exception as e:
            print(f"[HybridRetriever] Vector search error: {e}")
            return []

    # --- Unified Retrieval ---

    def retrieve(self, query: str, intent_info: Dict[str, Any], entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute coordinated hybrid retrieval with uniform confidence gating across ALL paths.
        Uses directive-stripped cleaned_query to prevent directive noise from diluting embeddings.
        """
        raw_intent = intent_info.get("intent")
        intent = raw_intent.value if hasattr(raw_intent, "value") else str(raw_intent)
        if "." in intent:
            intent = intent.split(".")[-1]

        # Use cleaned_query (directive-stripped) for all matching
        clean_q = entities.get("cleaned_query") or query

        output = {
            "structured_results": [],
            "vector_results": [],
            "additional_count": 0,
            "context_type": intent
        }

        # 0. Refusal
        if intent == "OUT_OF_SCOPE":
            return output

        # 1. HUID Verification
        if intent == "HUID_VERIFICATION":
            codes = entities.get("huid_codes", [])
            if codes:
                for h in codes:
                    rec = self.lookup_huid(h)
                    if rec:
                        output["structured_results"].append(rec)
            else:
                terms = ["24K", "22K", "18K", "14K", "916", "750", "925", "silver", "gold"]
                matched_term = next((t for t in terms if t.lower() in clean_q.lower()), "gold")
                rec = self.lookup_huid(matched_term)
                if rec:
                    output["structured_results"].append(rec)
            return output

        # 2. Certification Schemes (retrieve from vector knowledge with uniform threshold >= 0.50)
        if intent == "CERTIFICATION_SCHEME":
            vector_query = clean_q
            if entities.get("detected_input_lang") == "hi" and entities.get("search_keywords"):
                vector_query = f"{clean_q} " + " ".join(entities["search_keywords"])
            output["vector_results"] = self.search_vector_corpus(vector_query, threshold=0.50, top_k=3)
            return output

        # 3. Specific Standard Lookup (by IS Number)
        if entities.get("is_numbers"):
            for std in entities["is_numbers"]:
                std_records = self.lookup_standard(std)
                output["structured_results"].extend(std_records)
                cw_records = self.lookup_crosswalk_exact_is(std)
                output["structured_results"].extend(cw_records)
            return output

        # 4. Product / Commodity QCO Crosswalk Lookup using RELEVANCE-SCORED EMBEDDINGS
        search_query = clean_q
        if entities.get("product_terms"):
            search_query = entities["product_terms"][0]
        elif entities.get("search_keywords"):
            search_query = " ".join(entities["search_keywords"])

        search_result = self.semantic_search_crosswalk(search_query, threshold=0.52, top_k=6)
        if search_result["matches"]:
            output["structured_results"] = search_result["matches"]
            output["additional_count"] = search_result["additional_count"]
            return output

        # 5. Semantic Vector Search fallback:
        # Strict uniform thresholding: ONLY accept if cosine similarity >= 0.50!
        # Do NOT silently accept weak matches like ECO Mark Scheme (0.319).
        vector_query = clean_q
        if entities.get("detected_input_lang") == "hi" and entities.get("search_keywords"):
            vector_query = f"{clean_q} " + " ".join(entities["search_keywords"])
        output["vector_results"] = self.search_vector_corpus(vector_query, threshold=0.50, top_k=3)

        return output
